import json
import os

import pytest

from omniagent import cost
from omniagent.providers import ProviderResponse


def _tracker(tmp_path, monkeypatch):
    data_dir = tmp_path / "usage"
    log_file = data_dir / "usage.jsonl"
    monkeypatch.setattr(cost, "DATA_DIR", data_dir)
    monkeypatch.setattr(cost, "LOG_FILE", log_file)
    return cost.CostTracker(), log_file


def test_log_uses_provider_usage_and_never_stores_prompt_or_response(tmp_path, monkeypatch):
    tracker, log_file = _tracker(tmp_path, monkeypatch)
    prompt = "private customer question"
    answer = "private generated answer"

    entry = tracker.log(
        "groq",
        "general",
        prompt,
        ProviderResponse(answer, "openai/gpt-oss-120b", input_tokens=100, output_tokens=200),
    )

    assert entry["usage_source"] == "provider"
    assert entry["estimated_cost_usd"] == pytest.approx(0.000135)
    assert entry["pricing_as_of"] == cost.PRICING_AS_OF
    raw = log_file.read_text(encoding="utf-8")
    assert prompt not in raw
    assert answer not in raw
    assert tracker.get_entries()[0]["model"] == "openai/gpt-oss-120b"


def test_missing_price_is_unknown_not_zero():
    assert cost.CostTracker._estimate_cost("groq", "custom/model", 100, 100) is None
    assert cost.CostTracker._estimate_cost("google", "gemini-3.8-flash", 100, 100) == pytest.approx(
        0.00045
    )


def test_word_count_fallback_is_explicitly_marked(tmp_path, monkeypatch):
    tracker, _ = _tracker(tmp_path, monkeypatch)
    entry = tracker.log(
        "deepseek",
        "math",
        "solve this equation please",
        ProviderResponse("The answer is 42.", "deepseek-flash"),
    )

    assert entry["usage_source"] == "word_count_heuristic"
    assert entry["input_tokens"] > 0
    assert entry["output_tokens"] > 0
    assert entry["estimated_cost_usd"] is not None
    assert "peak" in entry["pricing_note"]


def test_deepseek_peak_rate_estimate_is_not_silently_zero():
    amount = cost.CostTracker._estimate_cost("deepseek", "deepseek-flash", 1000, 1000)
    assert amount == pytest.approx(0.0015)


def test_legacy_usage_log_remains_readable(tmp_path, monkeypatch):
    tracker, log_file = _tracker(tmp_path, monkeypatch)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00",
                "provider": "groq",
                "task_type": "general",
                "prompt_tokens": 10.4,
                "response_tokens": 5.2,
                "estimated_cost": 0.0003,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    entry = tracker.get_entries()[0]

    assert entry["estimated_cost_usd"] == pytest.approx(0.0003)
    assert entry["input_tokens"] == 11
    assert entry["output_tokens"] == 6
    assert "Legacy" in entry["pricing_note"]


def test_malformed_usage_log_reports_line_number(tmp_path, monkeypatch):
    tracker, log_file = _tracker(tmp_path, monkeypatch)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("not-json\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line 1"):
        tracker.get_entries()


def test_extreme_legacy_numbers_are_safely_marked_unknown(tmp_path, monkeypatch):
    tracker, log_file = _tracker(tmp_path, monkeypatch)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "estimated_cost": 10**1000,
        "prompt_tokens": 10**1000,
        "response_tokens": 2,
    }
    log_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    normalized = tracker.get_entries()[0]

    assert normalized["estimated_cost_usd"] is None
    assert normalized["input_tokens"] == "?"
    assert normalized["output_tokens"] == 2


def test_usage_log_permissions_are_private(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("fine-grained POSIX permissions are not available on Windows")
    tracker, log_file = _tracker(tmp_path, monkeypatch)
    tracker.log("ollama", "general", "hello", ProviderResponse("hi", "qwen2.5-coder:7b"))

    assert os.stat(log_file).st_mode & 0o777 == 0o600
    assert os.stat(log_file.parent).st_mode & 0o777 == 0o700


def test_data_directory_symlink_is_rejected(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("symlink creation may require elevated privileges on Windows")
    target = tmp_path / "real-data"
    target.mkdir()
    data_dir = tmp_path / "usage"
    data_dir.symlink_to(target, target_is_directory=True)
    monkeypatch.setattr(cost, "DATA_DIR", data_dir)
    monkeypatch.setattr(cost, "LOG_FILE", data_dir / "usage.jsonl")

    with pytest.raises(OSError, match="symbolic-link"):
        cost.CostTracker()


def test_user_data_directory_override_must_be_absolute(tmp_path, monkeypatch):
    fallback = tmp_path / "default"
    monkeypatch.setenv("OMNIAGENT_TEST_DATA_DIR", "relative/path")
    assert cost._user_directory("OMNIAGENT_TEST_DATA_DIR", fallback) == fallback

    absolute = tmp_path / "custom"
    monkeypatch.setenv("OMNIAGENT_TEST_DATA_DIR", str(absolute))
    assert cost._user_directory("OMNIAGENT_TEST_DATA_DIR", fallback) == absolute
