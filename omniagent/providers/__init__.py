"""Provider implementations for OmniAgent."""

import os
import httpx


def execute(provider: str, prompt: str, config: dict) -> str:
    """Execute a prompt on the specified provider."""
    handlers = {
        "provider_a": _call_provider_a,
        "provider_b": _call_provider_b,
        "provider_c": _call_provider_c,
        "provider_d": _call_provider_d,
        "provider_e": _call_provider_e,
    }
    handler = handlers.get(provider)
    if not handler:
        return f"[Error: Unknown provider '{provider}']"
    return handler(prompt, config)


def _get_key(provider: str, config: dict) -> str | None:
    env_map = {
        "provider_a": "PROVIDER_A_API_KEY",
        "provider_b": "PROVIDER_B_API_KEY",
        "provider_c": "PROVIDER_C_API_KEY",
        "provider_d": "PROVIDER_D_API_KEY",
        "provider_e": "PROVIDER_E_API_KEY",
    }
    env_var = env_map.get(provider)
    if env_var:
        key = os.environ.get(env_var)
        if key:
            return key
    return config.get(f"{provider}_api_key")


def _call_provider_a(prompt: str, config: dict) -> str:
    key = _get_key("provider_a", config)
    if not key:
        return "[Error: No PROVIDER_A_API_KEY set]"
    resp = httpx.post(
        "https://api.provider-a.com/v1/messages",
        headers={"x-api-key": key, "content-type": "application/json"},
        json={"model": "model-a-1", "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def _call_provider_b(prompt: str, config: dict) -> str:
    key = _get_key("provider_b", config)
    if not key:
        return "[Error: No PROVIDER_B_API_KEY set]"
    resp = httpx.post(
        "https://api.provider-b.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "model-b-1", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_provider_c(prompt: str, config: dict) -> str:
    key = _get_key("provider_c", config)
    if not key:
        return "[Error: No PROVIDER_C_API_KEY set]"
    resp = httpx.post(
        "https://api.provider-c.com/v1/generate",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 4096}},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _call_provider_d(prompt: str, config: dict) -> str:
    key = _get_key("provider_d", config)
    if not key:
        return "[Error: No PROVIDER_D_API_KEY set]"
    resp = httpx.post(
        "https://api.provider-d.com/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "model-d-1", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_provider_e(prompt: str, config: dict) -> str:
    key = _get_key("provider_e", config)
    if not key:
        return "[Error: No PROVIDER_E_API_KEY set]"
    resp = httpx.post(
        "https://api.provider-e.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "model-e-1", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
