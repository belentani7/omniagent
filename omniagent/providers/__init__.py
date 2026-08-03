"""Provider implementations for OmniAgent — real, working providers."""

import os
import httpx

PROVIDER_INFO = {
    "groq": {
        "label": "Groq",
        "best_for": "Code gen, quick queries, budget",
        "model": "llama-3.3-70b-versatile",
        "cost_tier": "economy",
    },
    "google": {
        "label": "Google",
        "best_for": "Research, general, translation",
        "model": "gemini-2.0-flash",
        "cost_tier": "free",
    },
    "openrouter": {
        "label": "OpenRouter",
        "best_for": "Any model, quality/cost balance",
        "model": "qwen/qwen-2.5-coder-32b-instruct:free",
        "cost_tier": "variable",
    },
    "deepseek": {
        "label": "DeepSeek",
        "best_for": "Code review, math, reasoning",
        "model": "deepseek-chat",
        "cost_tier": "economy",
    },
    "ollama": {
        "label": "Ollama (local)",
        "best_for": "Offline, privacy",
        "model": "qwen2.5-coder:7b",
        "cost_tier": "free-local",
    },
}

ENV_KEYS = {
    "groq": "GROQ_API_KEY",
    "google": "GOOGLE_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}


def execute(provider: str, prompt: str, config: dict) -> str:
    """Execute a prompt on the specified provider."""
    handlers = {
        "groq": _call_groq,
        "google": _call_google,
        "openrouter": _call_openrouter,
        "deepseek": _call_deepseek,
        "ollama": _call_ollama,
    }
    handler = handlers.get(provider)
    if not handler:
        return f"[Error: Unknown provider '{provider}']"
    try:
        return handler(prompt, config)
    except httpx.HTTPStatusError as e:
        return f"[Error: {provider} HTTP {e.response.status_code}: {e.response.text[:200]}]"
    except httpx.RequestError as e:
        return f"[Error: {provider} connection failed: {e}]"


def _get_key(provider: str, config: dict) -> str | None:
    env_var = ENV_KEYS.get(provider)
    if env_var:
        key = os.environ.get(env_var)
        if key:
            return key
    return config.get(f"{provider}_api_key")


def _call_groq(prompt: str, config: dict) -> str:
    key = _get_key("groq", config)
    if not key:
        return "[Error: No GROQ_API_KEY set]"
    model = config.get("models", {}).get("groq", PROVIDER_INFO["groq"]["model"])
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_google(prompt: str, config: dict) -> str:
    key = _get_key("google", config)
    if not key:
        return "[Error: No GOOGLE_API_KEY set]"
    model = config.get("models", {}).get("google", PROVIDER_INFO["google"]["model"])
    resp = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 4096}},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _call_openrouter(prompt: str, config: dict) -> str:
    key = _get_key("openrouter", config)
    if not key:
        return "[Error: No OPENROUTER_API_KEY set]"
    model = config.get("models", {}).get("openrouter", PROVIDER_INFO["openrouter"]["model"])
    resp = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_deepseek(prompt: str, config: dict) -> str:
    key = _get_key("deepseek", config)
    if not key:
        return "[Error: No DEEPSEEK_API_KEY set]"
    model = config.get("models", {}).get("deepseek", PROVIDER_INFO["deepseek"]["model"])
    resp = httpx.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_ollama(prompt: str, config: dict) -> str:
    base_url = config.get("ollama_base_url", os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    model = config.get("models", {}).get("ollama", PROVIDER_INFO["ollama"]["model"])
    resp = httpx.post(
        f"{base_url}/api/chat",
        headers={"Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False},
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]
