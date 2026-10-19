import os
from unittest.mock import patch

import httpx
import pytest

from omniagent import config


def test_update_config_writes_private_file(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("fine-grained POSIX permissions are not available on Windows")
    config_dir = tmp_path / "omniagent"
    config_file = config_dir / "config.yaml"
    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)

    config.update_config({"monthly_budget": 0.0})

    assert config.load_config()["monthly_budget"] == 0.0
    assert os.stat(config_file).st_mode & 0o777 == 0o600


def test_update_config_preserves_nested_defaults(tmp_path, monkeypatch):
    config_dir = tmp_path / "omniagent"
    config_file = config_dir / "config.yaml"
    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)

    config.update_config({"routing": {"math": "ollama"}})
    loaded = config.load_config()

    assert loaded["routing"]["math"] == "ollama"
    assert loaded["routing"]["translation"] == config.DEFAULT_CONFIG["routing"]["translation"]


def test_update_config_rejects_non_finite_budget_without_replacing_file(tmp_path, monkeypatch):
    config_dir = tmp_path / "omniagent"
    config_file = config_dir / "config.yaml"
    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)
    config.update_config({"monthly_budget": 25})
    original = config_file.read_bytes()

    with pytest.raises(ValueError, match="monthly_budget"):
        config.update_config({"monthly_budget": float("inf")})

    assert config_file.read_bytes() == original


def test_load_config_rejects_non_mapping_yaml(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("- not a mapping\n", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)

    with pytest.raises(ValueError, match="YAML mapping"):
        config.load_config()


def test_load_config_rejects_malformed_yaml(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("routing: [\n", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)

    with pytest.raises(ValueError, match="invalid or inaccessible YAML"):
        config.load_config()


def test_dry_run_provider_discovery_does_not_probe_localhost(monkeypatch):
    for env_name in config.API_KEY_PROVIDERS.values():
        monkeypatch.delenv(env_name, raising=False)
    with patch("httpx.get") as get:
        assert config.get_available_providers(config.DEFAULT_CONFIG, probe_ollama=False) == []
    get.assert_not_called()


def test_ollama_probe_ignores_network_failure(monkeypatch):
    for env_name in config.API_KEY_PROVIDERS.values():
        monkeypatch.delenv(env_name, raising=False)
    with patch("httpx.get", side_effect=httpx.ConnectError("offline")):
        assert config.get_available_providers(config.DEFAULT_CONFIG) == []


def test_update_config_refuses_to_follow_a_config_symlink(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("symlink creation may require elevated privileges on Windows")
    config_dir = tmp_path / "omniagent"
    config_dir.mkdir()
    target = tmp_path / "external.yaml"
    target.write_text("monthly_budget: 9\n", encoding="utf-8")
    config_file = config_dir / "config.yaml"
    config_file.symlink_to(target)
    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)

    with pytest.raises(OSError, match="symbolic link"):
        config.update_config({"monthly_budget": 10})

    assert target.read_text(encoding="utf-8") == "monthly_budget: 9\n"


def test_load_config_refuses_to_read_a_config_symlink(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("symlink creation may require elevated privileges on Windows")
    config_dir = tmp_path / "omniagent"
    config_dir.mkdir()
    target = tmp_path / "external.yaml"
    target.write_text("monthly_budget: 9\n", encoding="utf-8")
    config_file = config_dir / "config.yaml"
    config_file.symlink_to(target)
    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)

    with pytest.raises(ValueError, match="symbolic-link configuration file"):
        config.load_config()


def test_config_directory_symlink_is_rejected(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("symlink creation may require elevated privileges on Windows")
    target = tmp_path / "real-config"
    target.mkdir()
    config_dir = tmp_path / "omniagent"
    config_dir.symlink_to(target, target_is_directory=True)
    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", config_dir / "config.yaml")

    with pytest.raises(OSError, match="symbolic-link configuration directory"):
        config.update_config({"monthly_budget": 10})


def test_user_directory_override_must_be_absolute(tmp_path, monkeypatch):
    fallback = tmp_path / "default"
    monkeypatch.setenv("OMNIAGENT_TEST_DIR", "relative/path")
    assert config._user_directory("OMNIAGENT_TEST_DIR", fallback) == fallback

    absolute = tmp_path / "custom"
    monkeypatch.setenv("OMNIAGENT_TEST_DIR", str(absolute))
    assert config._user_directory("OMNIAGENT_TEST_DIR", fallback) == absolute
