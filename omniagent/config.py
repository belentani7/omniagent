"""Configuration management for OmniAgent."""

import os
from pathlib import Path
import yaml

CONFIG_DIR = Path.home() / ".config" / "omniagent"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "monthly_budget": 50.0,
    "routing": {
        "code_review": "anthropic",
        "code_generation": "anthropic",
        "translation": "google",
        "math": "deepseek",
        "quick_query": "google",
        "creative_writing": "anthropic",
        "data_analysis": "openai",
        "research": "anthropic",
    },
    "cost_tiers": {
        "frontier": {"anthropic": 15.0, "openai": 15.0, "google": 10.0},
        "mid": {"anthropic": 3.0, "openai": 5.0, "google": 2.5, "deepseek": 1.0},
        "economy": {"google": 0.1, "deepseek": 0.1, "groq": 0.05},
    },
}


def load_config() -> dict:
    """Load config from file, falling back to defaults."""
    config = DEFAULT_CONFIG.copy()
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
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_available_providers(config: dict) -> list[str]:
    """Check which providers have API keys set."""
    env_keys = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "groq": "GROQ_API_KEY",
        "xiaomi": "XIAOMI_API_KEY",
    }
    available = []
    for provider, env_var in env_keys.items():
        if os.environ.get(env_var):
            available.append(provider)
        elif config.get(f"{provider}_api_key"):
            available.append(provider)
    return available


def _deep_merge(base: dict, override: dict):
    """Deep merge override into base."""
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
