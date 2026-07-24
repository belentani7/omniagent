"""Provider implementations for OmniAgent."""

import os
import httpx


def execute(provider: str, prompt: str, config: dict) -> str:
    """Execute a prompt on the specified provider."""
    handlers = {
        "anthropic": _call_anthropic,
        "openai": _call_openai,
        "google": _call_google,
        "deepseek": _call_deepseek,
        "groq": _call_groq,
    }
    handler = handlers.get(provider)
    if not handler:
        return f"[Error: Unknown provider '{provider}']"
    return handler(prompt, config)


def _get_key(provider: str, config: dict) -> str | None:
    """Get API key from env or config."""
    env_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "groq": "GROQ_API_KEY",
    }
    env_var = env_map.get(provider)
    if env_var:
        key = os.environ.get(env_var)
        if key:
            return key
    return config.get(f"{provider}_api_key")


def _call_anthropic(prompt: str, config: dict) -> str:
    key = _get_key("anthropic", config)
    if not key:
        return "[Error: No ANTHROPIC_API_KEY set]"
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-20250514", "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def _call_openai(prompt: str, config: dict) -> str:
    key = _get_key("openai", config)
    if not key:
        return "[Error: No OPENAI_API_KEY set]"
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "gpt-4.1", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_google(prompt: str, config: dict) -> str:
    key = _get_key("google", config)
    if not key:
        return "[Error: No GOOGLE_API_KEY set]"
    resp = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 4096}},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _call_deepseek(prompt: str, config: dict) -> str:
    key = _get_key("deepseek", config)
    if not key:
        return "[Error: No DEEPSEEK_API_KEY set]"
    resp = httpx.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_groq(prompt: str, config: dict) -> str:
    key = _get_key("groq", config)
    if not key:
        return "[Error: No GROQ_API_KEY set]"
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
