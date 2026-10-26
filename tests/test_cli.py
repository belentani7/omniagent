from copy import deepcopy
from unittest.mock import Mock

from click.testing import CliRunner

import omniagent.cli as cli
from omniagent.config import DEFAULT_CONFIG
from omniagent.providers import ProviderError, ProviderResponse


def test_dry_run_routes_without_network_or_prompt_echo(monkeypatch):
    runner = CliRunner()
    config = deepcopy(DEFAULT_CONFIG)
    prompt = "translate this private message to Spanish"
    providers = Mock(return_value=[])
    execute = Mock(side_effect=AssertionError("dry-run must not execute a provider"))
    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "get_available_providers", providers)
    monkeypatch.setattr(cli, "execute", execute)

    result = runner.invoke(cli.main, ["run", prompt, "--dry-run"])

    assert result.exit_code == 0, result.output
    assert "translation" in result.output
    assert "google" in result.output
    assert prompt not in result.output
    assert "No prompt was sent" in result.output
    providers.assert_called_once_with(config, probe_ollama=False)
    execute.assert_not_called()


def test_run_rejects_empty_provider_set_without_sending_prompt(monkeypatch):
    runner = CliRunner()
    config = deepcopy(DEFAULT_CONFIG)
    execute = Mock()
    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "get_available_providers", lambda *args, **kwargs: [])
    monkeypatch.setattr(cli, "execute", execute)

    result = runner.invoke(cli.main, ["run", "hello"])

    assert result.exit_code != 0
    assert "No provider is available" in result.output
    execute.assert_not_called()


def test_invalid_forced_provider_fails_before_network(monkeypatch):
    runner = CliRunner()
    providers = Mock()
    monkeypatch.setattr(cli, "load_config", lambda: deepcopy(DEFAULT_CONFIG))
    monkeypatch.setattr(cli, "get_available_providers", providers)

    result = runner.invoke(cli.main, ["run", "hello", "--provider", "unknown"])

    assert result.exit_code != 0
    assert "unknown provider" in result.output
    providers.assert_not_called()


def test_successful_run_logs_only_provider_response_metadata(monkeypatch):
    runner = CliRunner()
    config = deepcopy(DEFAULT_CONFIG)
    tracker = Mock()
    response = ProviderResponse("safe answer", "openai/gpt-oss-120b", 5, 3)
    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "get_available_providers", lambda *args, **kwargs: ["groq"])
    monkeypatch.setattr(cli, "execute", lambda provider, prompt, cfg: response)
    monkeypatch.setattr(cli, "CostTracker", lambda: tracker)

    result = runner.invoke(cli.main, ["run", "private request", "--verbose"])

    assert result.exit_code == 0, result.output
    assert "safe answer" in result.output
    assert "private request" not in result.output
    tracker.log.assert_called_once_with("groq", "general", "private request", response)


def test_provider_failure_returns_nonzero_and_is_not_logged(monkeypatch):
    runner = CliRunner()
    tracker = Mock()
    monkeypatch.setattr(cli, "load_config", lambda: deepcopy(DEFAULT_CONFIG))
    monkeypatch.setattr(cli, "get_available_providers", lambda *args, **kwargs: ["groq"])
    monkeypatch.setattr(cli, "execute", Mock(side_effect=ProviderError("groq", "HTTP 429")))
    monkeypatch.setattr(cli, "CostTracker", lambda: tracker)

    result = runner.invoke(cli.main, ["run", "question"])

    assert result.exit_code != 0
    assert "HTTP 429" in result.output
    tracker.log.assert_not_called()


def test_cost_command_reports_invalid_local_log_without_traceback(monkeypatch):
    runner = CliRunner()

    def fail():
        raise OSError("usage log is not accessible")

    monkeypatch.setattr(cli, "CostTracker", fail)
    result = runner.invoke(cli.main, ["cost"])

    assert result.exit_code != 0
    assert "usage log is not accessible" in result.output
    assert "Traceback" not in result.output


def test_setup_hides_api_keys_and_never_prints_the_value(monkeypatch):
    runner = CliRunner()
    updates = {}
    monkeypatch.setattr(cli, "update_config", lambda values: updates.update(values))

    result = runner.invoke(cli.main, ["setup"], input="hidden-secret\n\n\n\n")

    assert result.exit_code == 0, result.output
    assert "hidden-secret" not in result.output
    assert updates == {"groq_api_key": "hidden-secret"}


def test_forced_ollama_unavailable_explains_server_or_model(monkeypatch):
    runner = CliRunner()
    execute = Mock()
    monkeypatch.setattr(cli, "load_config", lambda: deepcopy(DEFAULT_CONFIG))
    monkeypatch.setattr(cli, "get_available_providers", lambda *args, **kwargs: [])
    monkeypatch.setattr(cli, "execute", execute)

    result = runner.invoke(cli.main, ["run", "question", "--provider", "ollama"])

    assert result.exit_code != 0
    assert "configured model missing" in result.output
    execute.assert_not_called()


def test_provider_list_describes_ollama_model_availability(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(cli, "load_config", lambda: deepcopy(DEFAULT_CONFIG))
    monkeypatch.setattr(cli, "get_available_providers", lambda *args, **kwargs: [])

    result = runner.invoke(cli.main, ["providers-list"])

    assert result.exit_code == 0, result.output
    assert "configured model installed" in result.output
