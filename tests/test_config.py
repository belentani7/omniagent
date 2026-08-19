import os

from omniagent import config


def test_update_config_writes_private_file(tmp_path, monkeypatch):
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
