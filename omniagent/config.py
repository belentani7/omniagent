"""Configuration management for OmniAgent."""

import os
from pathlib import Path
import yaml

CONFIG_DIR = Path.home() / ".config" / "omniagent"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "monthly_budget": 0.0,
    "default_provider": "groq",
    "routing": {
        "code_review": "deepseek",
        "code_generation": "groq",
        "translation": "google",
        "math": "deepseek",
        "quick_query": "groq",
        "creative_writing": "openrouter",
        "data_analysis": "openrouter",
        "research": "google",
    },
    "models": {
        "groq": "llama-3.3-70b-versatile",
        "google": "gemini-2.0-flash",
        "openrouter": "qwen/qwen-2.5-coder-32b-instruct:free",
        "deepseek": "deepseek-chat",
        "ollama": "qwen2.5-coder:7b",
    },
    "ollama_base_url": "http://localhost:11434",
    "cost_tiers": {
        "free": {"google": 0.0, "ollama": 0.0},
        "economy": {"groq": 0.0002, "deepseek": 0.0005},
        "variable": {"openrouter": 0.001},
    },
}

# Order providers are tried when a task type's preferred provider is unavailable
FALLBACK_ORDER = ["groq", "google", "deepseek", "openrouter", "ollama"]


def load_config() -> dict:
    """Load config from file, falling back to defaults."""
    config = _deep_copy(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            user_config = yaml.safe_load(f) or {}
        _deep_merge(config, user_config)
    return config


def update_config(updates: dict):
    """Update config file with new values."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = load_config()
    _deep_merge(config, updates)
    CONFIG_FILE.touch(mode=0o600, exist_ok=True)
    CONFIG_FILE.chmod(0o600)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)


def get_available_providers(config: dict) -> list[str]:
    """Check which providers have API keys set (or are local)."""
    env_keys = {
        "groq": "GROQ_API_KEY",
        "google": "GOOGLE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }
    available = []
    for provider, env_var in env_keys.items():
        if os.environ.get(env_var):
            available.append(provider)
        elif config.get(f"{provider}_api_key"):
            available.append(provider)
    # Ollama is always available if reachable (local)
    base = config.get("ollama_base_url", "http://localhost:11434")
    try:
        import httpx
        r = httpx.get(f"{base}/api/tags", timeout=2)
        if r.status_code == 200:
            available.append("ollama")
    except Exception:
        pass
    return available


def _deep_copy(d: dict) -> dict:
    import copy
    return copy.deepcopy(d)


def _deep_merge(base: dict, override: dict):
    """Deep merge override into base."""
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
