"""Provider clients for OmniAgent.

Only the prompt is sent to the selected provider. Credentials are sent in
headers (never query strings), provider failures are sanitized, and successful
responses include token usage when the API reports it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlsplit

import httpx

PROVIDER_INFO = {
    "groq": {
        "label": "Groq",
        "best_for": "Fast hosted inference",
        "model": "openai/gpt-oss-120b",
        "cost_tier": "paid",
        "environment_variable": "GROQ_API_KEY",
    },
    "google": {
        "label": "Google Gemini",
        "best_for": "General text tasks and research",
        "model": "gemini-3.8-flash",
        "cost_tier": "free tier or paid",
        "environment_variable": "GOOGLE_API_KEY",
    },
    "openrouter": {
        "label": "OpenRouter",
        "best_for": "Model choice and provider flexibility",
        "model": "qwen/qwen3.8-27b:free",
        "cost_tier": "free endpoint; rate-limited",
        "environment_variable": "OPENROUTER_API_KEY",
    },
    "deepseek": {
        "label": "DeepSeek",
        "best_for": "Reasoning and code review",
        "model": "deepseek-flash",
        "cost_tier": "variable; peak/off-peak rates",
        "environment_variable": "DEEPSEEK_API_KEY",
    },
    "ollama": {
        "label": "Ollama (local)",
        "best_for": "Local inference and offline workflows",
        "model": "qwen2.5-coder:7b",
        "cost_tier": "no provider token charge; hardware excluded",
        "environment_variable": None,
    },
}

ENV_KEYS = {
    provider: details["environment_variable"]
    for provider, details in PROVIDER_INFO.items()
    if details["environment_variable"]
}


class ProviderError(RuntimeError):
    """Sanitized provider failure safe to display in a terminal."""

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"{provider}: {message}")


@dataclass(frozen=True)
class ProviderResponse:
    """Text response plus usage metadata reported by the provider, if any."""

    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("model must be a non-empty string")
        for name, value in (
            ("input_tokens", self.input_tokens),
            ("output_tokens", self.output_tokens),
        ):
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 1_000_000_000_000
            ):
                raise ValueError(f"{name} must be an integer from 0 to 1,000,000,000,000 or None")
        if self.request_id is not None and not isinstance(self.request_id, str):
            raise ValueError("request_id must be a string or None")


def execute(provider: str, prompt: str, config: dict[str, Any]) -> ProviderResponse:
    """Call one configured provider, raising a redacted error on failure."""

    handlers = {
        "groq": _call_groq,
        "google": _call_google,
        "openrouter": _call_openrouter,
        "deepseek": _call_deepseek,
        "ollama": _call_ollama,
    }
    handler = handlers.get(provider)
    if handler is None:
        raise ProviderError(provider, "unknown provider")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ProviderError(provider, "prompt must not be empty")

    try:
        return handler(prompt, config)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        hint = "check credentials, quota, and model availability"
        raise ProviderError(provider, f"HTTP {status}; {hint}. Response body withheld.") from None
    except httpx.TimeoutException:
        raise ProviderError(provider, "request timed out") from None
    except httpx.RequestError:
        # Do not stringify the exception: request URLs or headers can contain secrets.
        raise ProviderError(provider, "network request failed") from None


def _get_key(provider: str, config: dict[str, Any]) -> str:
    env_var = ENV_KEYS.get(provider)
    key = os.environ.get(env_var, "").strip() if env_var else ""
    if not key:
        configured = config.get(f"{provider}_api_key", "")
        key = configured.strip() if isinstance(configured, str) else ""
    if not key:
        env_name = env_var or f"{provider.upper()}_API_KEY"
        raise ProviderError(provider, f"no credential configured; set {env_name} or run `oa setup`")
    return key


def _model(provider: str, config: dict[str, Any]) -> str:
    models = config.get("models", {})
    if not isinstance(models, dict):
        raise ProviderError(provider, "config.models must be a mapping")
    value = models.get(provider, PROVIDER_INFO[provider]["model"])
    if not isinstance(value, str) or not value.strip():
        raise ProviderError(provider, f"config.models.{provider} must be a non-empty string")
    return value.strip()


def _max_output_tokens(provider: str, config: dict[str, Any]) -> int:
    value = config.get("max_output_tokens", 2048)
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 65536:
        raise ProviderError(provider, "max_output_tokens must be an integer from 1 to 65536")
    return value


def _post_json(provider: str, url: str, **kwargs: Any) -> dict[str, Any]:
    response = httpx.post(url, **kwargs)
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError:
        raise ProviderError(provider, "provider returned invalid JSON") from None
    if not isinstance(data, dict):
        raise ProviderError(provider, "provider returned an unexpected response")
    return data


def _token_count(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1_000_000_000_000:
        return None
    return value


def _openai_response(provider: str, data: dict[str, Any], requested_model: str) -> ProviderResponse:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ProviderError(provider, "provider returned no text choice")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ProviderError(provider, "provider returned an unexpected response")
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and isinstance(part.get("text", ""), str)
        )
    if not isinstance(content, str) or not content.strip():
        raise ProviderError(provider, "provider returned no text content")
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    actual_model = data.get("model")
    actual_id = data.get("id")
    return ProviderResponse(
        text=content,
        model=actual_model.strip()
        if isinstance(actual_model, str) and actual_model.strip()
        else requested_model,
        input_tokens=_token_count(usage.get("prompt_tokens")),
        output_tokens=_token_count(usage.get("completion_tokens")),
        request_id=actual_id if isinstance(actual_id, str) else None,
    )


def _call_openai_compatible(
    provider: str,
    prompt: str,
    config: dict[str, Any],
    url: str,
    *,
    token_parameter: str = "max_tokens",
) -> ProviderResponse:
    key = _get_key(provider, config)
    model = _model(provider, config)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        token_parameter: _max_output_tokens(provider, config),
    }
    data = _post_json(
        provider,
        url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    return _openai_response(provider, data, model)


def _call_groq(prompt: str, config: dict[str, Any]) -> ProviderResponse:
    return _call_openai_compatible(
        "groq",
        prompt,
        config,
        "https://api.groq.com/openai/v1/chat/completions",
        token_parameter="max_completion_tokens",
    )


def _call_google(prompt: str, config: dict[str, Any]) -> ProviderResponse:
    provider = "google"
    key = _get_key(provider, config)
    model = _model(provider, config)
    encoded_model = quote(model, safe="-._")
    data = _post_json(
        provider,
        f"https://generativelanguage.googleapis.com/v1beta/models/{encoded_model}:generateContent",
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": _max_output_tokens(provider, config)},
        },
        timeout=120,
    )
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
        raise ProviderError(
            provider, "provider returned no text candidate; it may have been blocked"
        )
    content = candidates[0].get("content")
    parts = content.get("parts", []) if isinstance(content, dict) else []
    text = (
        "".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text", ""), str)
        )
        if isinstance(parts, list)
        else ""
    )
    if not text.strip():
        raise ProviderError(provider, "provider returned no text content")

    usage = data.get("usageMetadata") if isinstance(data.get("usageMetadata"), dict) else {}
    input_tokens = _token_count(usage.get("promptTokenCount"))
    output_tokens = _token_count(usage.get("candidatesTokenCount"))
    thoughts_tokens = _token_count(usage.get("thoughtsTokenCount"))
    if output_tokens is not None and thoughts_tokens is not None:
        output_tokens += thoughts_tokens
    elif (
        output_tokens is None
        and _token_count(usage.get("totalTokenCount")) is not None
        and input_tokens is not None
    ):
        output_tokens = max(0, usage["totalTokenCount"] - input_tokens)
    actual_model = data.get("modelVersion")
    return ProviderResponse(
        text=text,
        model=actual_model.strip()
        if isinstance(actual_model, str) and actual_model.strip()
        else model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        request_id=data.get("responseId") if isinstance(data.get("responseId"), str) else None,
    )


def _call_openrouter(prompt: str, config: dict[str, Any]) -> ProviderResponse:
    return _call_openai_compatible(
        "openrouter", prompt, config, "https://openrouter.ai/api/v1/chat/completions"
    )


def _call_deepseek(prompt: str, config: dict[str, Any]) -> ProviderResponse:
    return _call_openai_compatible(
        "deepseek", prompt, config, "https://api.deepseek.com/chat/completions"
    )


def _call_ollama(prompt: str, config: dict[str, Any]) -> ProviderResponse:
    provider = "ollama"
    base_url = config.get(
        "ollama_base_url", os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    if not isinstance(base_url, str):
        raise ProviderError(provider, "ollama_base_url must be a URL string")
    base_url = base_url.strip().rstrip("/")
    parsed = urlsplit(base_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username
        or parsed.password
    ):
        raise ProviderError(
            provider, "ollama_base_url must be an HTTP(S) URL without embedded credentials"
        )
    model = _model(provider, config)
    data = _post_json(
        provider,
        f"{base_url}/api/chat",
        headers={"Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"num_predict": _max_output_tokens(provider, config)},
        },
        timeout=300,
    )
    message = data.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ProviderError(provider, "provider returned no text content")
    actual_model = data.get("model")
    return ProviderResponse(
        text=content,
        model=actual_model.strip()
        if isinstance(actual_model, str) and actual_model.strip()
        else model,
        input_tokens=_token_count(data.get("prompt_eval_count")),
        output_tokens=_token_count(data.get("eval_count")),
        request_id=data.get("id") if isinstance(data.get("id"), str) else None,
    )
