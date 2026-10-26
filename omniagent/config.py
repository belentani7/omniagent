"""Configuration management with private, atomic writes for API credentials."""

from __future__ import annotations

import copy
import math
import os
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml


def _user_directory(environment_variable: str, fallback: Path) -> Path:
    """Use an absolute user-data directory override; ignore empty or relative values."""
    value = os.environ.get(environment_variable)
    if not value or not value.strip():
        return fallback
    candidate = Path(value).expanduser()
    return candidate if candidate.is_absolute() else fallback


if os.name == "nt":
    _CONFIG_ROOT = _user_directory("APPDATA", Path.home() / "AppData" / "Roaming")
else:
    _CONFIG_ROOT = _user_directory("XDG_CONFIG_HOME", Path.home() / ".config")
CONFIG_DIR = _CONFIG_ROOT / "omniagent"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

PROVIDER_NAMES = ("groq", "google", "openrouter", "deepseek", "ollama")
API_KEY_PROVIDERS = {
    "groq": "GROQ_API_KEY",
    "google": "GOOGLE_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}

DEFAULT_CONFIG: dict[str, Any] = {
    # This is a planning reference in EUR, not an API spend limit.
    "monthly_budget": None,
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
        "groq": "openai/gpt-oss-120b",
        "google": "gemini-3.8-flash",
        "openrouter": "qwen/qwen3.8-27b:free",
        "deepseek": "deepseek-flash",
        "ollama": "qwen2.5-coder:7b",
    },
    "max_output_tokens": 2048,
    "ollama_base_url": "http://localhost:11434",
}

# Providers are tried in this order only when the task's preferred provider is unavailable.
FALLBACK_ORDER = ["groq", "google", "deepseek", "openrouter", "ollama"]


def load_config() -> dict[str, Any]:
    """Load user configuration over defaults, with actionable validation errors."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    if CONFIG_DIR.is_symlink():
        raise ValueError(f"refusing to use symbolic-link configuration directory: {CONFIG_DIR}")
    if CONFIG_FILE.is_symlink():
        raise ValueError(f"refusing to read symbolic-link configuration file: {CONFIG_FILE}")
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open(encoding="utf-8") as stream:
                user_config = yaml.safe_load(stream)
        except (OSError, yaml.YAMLError) as exc:
            raise ValueError(f"Cannot read {CONFIG_FILE}: invalid or inaccessible YAML") from exc
        if user_config is None:
            user_config = {}
        if not isinstance(user_config, dict):
            raise ValueError(f"{CONFIG_FILE} must contain a YAML mapping at its root")
        _deep_merge(config, user_config)
    return validate_config(config)


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate fields used by routing, provider calls, and budget display."""
    if not isinstance(config, dict):
        raise ValueError("configuration must be a mapping")

    budget = config.get("monthly_budget")
    if budget is not None:
        if isinstance(budget, bool):
            raise ValueError("monthly_budget must be a finite, non-negative EUR amount or null")
        try:
            budget_value = float(budget)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(
                "monthly_budget must be a finite, non-negative EUR amount or null"
            ) from None
        if not math.isfinite(budget_value) or budget_value < 0:
            raise ValueError("monthly_budget must be a finite, non-negative EUR amount or null")
        config["monthly_budget"] = budget_value

    default_provider = config.get("default_provider")
    if default_provider not in PROVIDER_NAMES:
        raise ValueError(f"default_provider must be one of: {', '.join(PROVIDER_NAMES)}")

    routing = config.get("routing")
    if not isinstance(routing, dict):
        raise ValueError("routing must be a mapping of task names to providers")
    for task, provider in routing.items():
        if not isinstance(task, str) or provider not in PROVIDER_NAMES:
            raise ValueError(f"routing.{task} must name one of: {', '.join(PROVIDER_NAMES)}")

    models = config.get("models")
    if not isinstance(models, dict):
        raise ValueError("models must be a mapping of providers to model IDs")
    for provider, model in models.items():
        if provider not in PROVIDER_NAMES or not isinstance(model, str) or not model.strip():
            raise ValueError(
                "each models entry must use a supported provider and non-empty model ID"
            )
        models[provider] = model.strip()

    for provider in API_KEY_PROVIDERS:
        key = config.get(f"{provider}_api_key")
        if key is not None and not isinstance(key, str):
            raise ValueError(f"{provider}_api_key must be a string")

    token_limit = config.get("max_output_tokens")
    if (
        isinstance(token_limit, bool)
        or not isinstance(token_limit, int)
        or not 1 <= token_limit <= 65536
    ):
        raise ValueError("max_output_tokens must be an integer from 1 to 65536")

    base_url = config.get("ollama_base_url")
    if not isinstance(base_url, str):
        raise ValueError("ollama_base_url must be an HTTP(S) URL")
    parsed = urlsplit(base_url.strip())
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username
        or parsed.password
    ):
        raise ValueError("ollama_base_url must be an HTTP(S) URL without embedded credentials")
    return config


def update_config(updates: dict[str, Any]) -> dict[str, Any]:
    """Validate and atomically save configuration, keeping API keys private."""
    if not isinstance(updates, dict):
        raise ValueError("configuration updates must be a mapping")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    if CONFIG_DIR.is_symlink():
        raise OSError(f"refusing to use symbolic-link configuration directory: {CONFIG_DIR}")
    if os.name != "nt":
        CONFIG_DIR.chmod(0o700)
    if CONFIG_FILE.is_symlink():
        raise OSError(f"refusing to replace symbolic link: {CONFIG_FILE}")

    config = load_config()
    _deep_merge(config, updates)
    validate_config(config)
    text = yaml.safe_dump(
        config,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    fd, temporary = tempfile.mkstemp(dir=CONFIG_DIR, prefix=".config-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if os.name != "nt":
            os.chmod(temporary, 0o600)
        os.replace(temporary, CONFIG_FILE)
        if os.name != "nt":
            directory_fd = os.open(CONFIG_DIR, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return config


def get_available_providers(config: dict[str, Any], *, probe_ollama: bool = True) -> list[str]:
    """Return providers with credentials; optionally check the local Ollama server."""
    available = []
    for provider, env_var in API_KEY_PROVIDERS.items():
        env_key = os.environ.get(env_var, "")
        config_key = config.get(f"{provider}_api_key", "")
        if (isinstance(env_key, str) and env_key.strip()) or (
            isinstance(config_key, str) and config_key.strip()
        ):
            available.append(provider)

    if probe_ollama:
        base_url = config.get("ollama_base_url", DEFAULT_CONFIG["ollama_base_url"])
        if isinstance(base_url, str):
            try:
                import httpx

                response = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=1.5)
                if response.status_code == 200:
                    payload = response.json()
                    models = payload.get("models") if isinstance(payload, dict) else None
                    configured = config.get("models", {})
                    model = (
                        configured.get("ollama", DEFAULT_CONFIG["models"]["ollama"])
                        if isinstance(configured, dict)
                        else DEFAULT_CONFIG["models"]["ollama"]
                    )
                    if isinstance(model, str) and isinstance(models, list):
                        requested = model if ":" in model else f"{model}:latest"
                        if any(
                            isinstance(item, dict)
                            and (item.get("name") == requested or item.get("model") == requested)
                            for item in models
                        ):
                            available.append("ollama")
            except (httpx.RequestError, ValueError):
                pass
    return [provider for provider in FALLBACK_ORDER if provider in available]


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    """Deep merge a trusted, already parsed mapping into defaults."""
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
