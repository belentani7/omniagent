"""Configuration management for OmniAgent."""

import os
from pathlib import Path
import yaml

CONFIG_DIR = Path.home() / ".config" / "omniagent"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "monthly_budget": 50.0,
    "routing": {
        "code_review": "provider_a",
        "code_generation": "provider_a",
        "translation": "provider_c",
        "math": "provider_d",
        "quick_query": "provider_e",
        "creative_writing": "provider_a",
        "data_analysis": "provider_b",
        "research": "provider_a",
    },
    "cost_tiers": {
        "frontier": {"provider_a": 15.0, "provider_b": 15.0, "provider_c": 10.0},
        "mid": {"provider_a": 3.0, "provider_b": 5.0, "provider_c": 2.5, "provider_d": 1.0},
        "economy": {"provider_c": 0.1, "provider_d": 0.1, "provider_e": 0.05},
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
        "provider_a": "PROVIDER_A_API_KEY",
        "provider_b": "PROVIDER_B_API_KEY",
        "provider_c": "PROVIDER_C_API_KEY",
        "provider_d": "PROVIDER_D_API_KEY",
        "provider_e": "PROVIDER_E_API_KEY",
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
