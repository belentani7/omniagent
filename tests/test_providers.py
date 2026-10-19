import httpx
import pytest

from omniagent.providers import ProviderError, ProviderResponse, execute


def _response(payload):
    request = httpx.Request("POST", "https://example.test/api")
    return httpx.Response(200, json=payload, request=request)


def test_google_api_key_is_sent_in_header_not_url_and_usage_is_reported(monkeypatch):
    secret = "google-test-secret"
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    payload = {
        "modelVersion": "gemini-3.8-flash",
        "responseId": "request-1",
        "candidates": [{"content": {"parts": [{"text": "Hello"}]}}],
        "usageMetadata": {
            "promptTokenCount": 12,
            "candidatesTokenCount": 5,
            "thoughtsTokenCount": 2,
        },
    }
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return _response(payload)

    monkeypatch.setattr(httpx, "post", fake_post)
    result = execute("google", "hello", {"google_api_key": secret})

    assert isinstance(result, ProviderResponse)
    assert result.text == "Hello"
    assert result.input_tokens == 12
    assert result.output_tokens == 7
    assert result.request_id == "request-1"
    assert secret not in captured["url"]
    assert "key=" not in captured["url"]
    assert captured["headers"]["x-goog-api-key"] == secret


def test_openai_compatible_provider_returns_usage_and_model(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    payload = {
        "id": "chat-1",
        "model": "openai/gpt-oss-120b",
        "choices": [{"message": {"content": "A useful answer"}}],
        "usage": {"prompt_tokens": 20, "completion_tokens": 30},
    }
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return _response(payload)

    monkeypatch.setattr(httpx, "post", fake_post)
    result = execute("groq", "question", {"groq_api_key": "groq-secret"})

    assert result.text == "A useful answer"
    assert result.model == "openai/gpt-oss-120b"
    assert result.input_tokens == 20
    assert result.output_tokens == 30
    assert captured["headers"]["Authorization"] == "Bearer groq-secret"
    assert captured["json"]["max_completion_tokens"] == 2048
    assert "max_tokens" not in captured["json"]
    assert "groq-secret" not in captured["url"]


def test_http_error_does_not_expose_response_body_or_credential(monkeypatch):
    secret = "deepseek-secret"
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    request = httpx.Request("POST", "https://api.deepseek.com/chat/completions")
    response = httpx.Response(401, request=request, text=f"invalid key {secret}")

    def fake_post(*args, **kwargs):
        response.raise_for_status()

    monkeypatch.setattr(httpx, "post", fake_post)
    with pytest.raises(ProviderError) as caught:
        execute("deepseek", "question", {"deepseek_api_key": secret})

    assert "401" in str(caught.value)
    assert secret not in str(caught.value)
    assert "invalid key" not in str(caught.value)


def test_request_error_is_sanitized(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    def fail_request(*args, **kwargs):
        raise httpx.ConnectError("key=secret")

    monkeypatch.setattr(httpx, "post", fail_request)

    with pytest.raises(ProviderError, match="network request failed") as caught:
        execute("groq", "question", {"groq_api_key": "groq-secret"})

    assert "secret" not in str(caught.value)


def test_missing_credentials_and_unknown_provider_raise_errors(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="no credential configured"):
        execute("openrouter", "question", {})
    with pytest.raises(ProviderError, match="unknown provider"):
        execute("not-a-provider", "question", {})


def test_ollama_response_includes_reported_token_usage(monkeypatch):
    payload = {
        "model": "qwen2.5-coder:7b",
        "message": {"content": "local response"},
        "prompt_eval_count": 8,
        "eval_count": 13,
    }
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        return _response(payload)

    monkeypatch.setattr(httpx, "post", fake_post)
    result = execute("ollama", "question", {})

    assert result.text == "local response"
    assert result.input_tokens == 8
    assert result.output_tokens == 13
    assert captured["url"] == "http://localhost:11434/api/chat"


def test_openai_compatible_provider_rejects_empty_content(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: _response({"choices": [{"message": {"content": "  "}}]}),
    )

    with pytest.raises(ProviderError, match="no text content"):
        execute("groq", "question", {"groq_api_key": "secret"})


def test_google_provider_rejects_empty_content(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: _response(
            {"candidates": [{"content": {"parts": [{"text": " "}]}}]}
        ),
    )

    with pytest.raises(ProviderError, match="no text content"):
        execute("google", "question", {"google_api_key": "secret"})


def test_ollama_provider_rejects_empty_content(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: _response({"message": {"content": ""}}),
    )

    with pytest.raises(ProviderError, match="no text content"):
        execute("ollama", "question", {})


def test_provider_response_rejects_invalid_usage_counts():
    with pytest.raises(ValueError, match="input_tokens"):
        ProviderResponse("answer", "model", input_tokens=-1)
    with pytest.raises(ValueError, match="output_tokens"):
        ProviderResponse("answer", "model", output_tokens=10**13)
