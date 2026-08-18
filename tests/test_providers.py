"""Tests for provider configuration and secret handling."""
import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def test_openai_not_configured_when_no_key():
    from coding_tutor.providers.openai_provider import OpenAIProvider
    p = OpenAIProvider()
    assert not p.is_configured()


def test_openai_configured_when_key_present(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from coding_tutor.providers.openai_provider import OpenAIProvider
    p = OpenAIProvider()
    assert p.is_configured()


def test_openai_base_url_alone_does_not_configure_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid/v1")
    from coding_tutor.providers.openai_provider import OpenAIProvider

    assert not OpenAIProvider().is_configured()


def test_openai_passes_base_url_and_medium_reasoning_without_network(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-openai")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid/v1")
    from coding_tutor.providers.base import ChatMessage
    from coding_tutor.providers.config import OPENAI_MODELS
    from coding_tutor.providers.openai_provider import OpenAIProvider
    import openai

    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
    )
    client_factory = MagicMock(return_value=client)
    monkeypatch.setattr(openai, "OpenAI", client_factory)

    response = OpenAIProvider().chat(
        [ChatMessage(role="user", content="hello")],
        OPENAI_MODELS[0],
    )

    client_factory.assert_called_once_with(
        api_key="secret-openai",
        base_url="https://example.invalid/v1",
    )
    assert client.chat.completions.create.call_args.kwargs["reasoning_effort"] == "medium"
    assert response.content == "ok"


def test_openai_uses_official_default_when_base_url_is_blank(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-openai")
    monkeypatch.setenv("OPENAI_BASE_URL", "   ")
    from coding_tutor.providers.base import ChatMessage
    from coding_tutor.providers.config import OPENAI_MODELS
    from coding_tutor.providers.openai_provider import OpenAIProvider
    import openai

    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
    )
    client_factory = MagicMock(return_value=client)
    monkeypatch.setattr(openai, "OpenAI", client_factory)

    OpenAIProvider().chat(
        [ChatMessage(role="user", content="hello")],
        OPENAI_MODELS[0],
    )

    client_factory.assert_called_once_with(api_key="secret-openai", base_url=None)


def test_agnes_not_configured_when_no_key():
    from coding_tutor.providers.agnes_provider import AgnesProvider
    p = AgnesProvider()
    assert not p.is_configured()


def test_agnes_configured_when_key_present(monkeypatch):
    monkeypatch.setenv("AGNES_API_KEY", "ag-test")
    from coding_tutor.providers.agnes_provider import AgnesProvider
    p = AgnesProvider()
    assert p.is_configured()


def test_gemini_not_configured_when_no_key():
    from coding_tutor.providers.gemini_provider import GeminiProvider
    p = GeminiProvider()
    assert not p.is_configured()


def test_gemini_configured_when_key_present(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "gk-test")
    from coding_tutor.providers.gemini_provider import GeminiProvider
    p = GeminiProvider()
    assert p.is_configured()


def test_gemini_ignores_gemini_api_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "unsupported-key-name")
    from coding_tutor.providers.gemini_provider import GeminiProvider

    assert not GeminiProvider().is_configured()


@pytest.mark.parametrize(
    ("provider_module", "provider_class", "env_name"),
    [
        ("coding_tutor.providers.openai_provider", "OpenAIProvider", "OPENAI_API_KEY"),
        ("coding_tutor.providers.agnes_provider", "AgnesProvider", "AGNES_API_KEY"),
        ("coding_tutor.providers.gemini_provider", "GeminiProvider", "GOOGLE_API_KEY"),
    ],
)
def test_whitespace_key_is_not_configured(monkeypatch, provider_module, provider_class, env_name):
    monkeypatch.setenv(env_name, "   ")
    module = __import__(provider_module, fromlist=[provider_class])

    assert not getattr(module, provider_class)().is_configured()


def test_secret_values_not_in_is_configured_return():
    """is_configured() must return only bool, never the key value."""
    from coding_tutor.providers.openai_provider import OpenAIProvider
    from coding_tutor.providers.agnes_provider import AgnesProvider
    from coding_tutor.providers.gemini_provider import GeminiProvider
    os.environ["OPENAI_API_KEY"] = "secret-openai"
    os.environ["AGNES_API_KEY"] = "secret-agnes"
    os.environ["GOOGLE_API_KEY"] = "secret-google"
    try:
        for cls in (OpenAIProvider, AgnesProvider, GeminiProvider):
            result = cls().is_configured()
            assert isinstance(result, bool), "is_configured must return bool"
    finally:
        for k in ("OPENAI_API_KEY", "AGNES_API_KEY", "GOOGLE_API_KEY"):
            os.environ.pop(k, None)


def test_agnes_chat_raises_without_key():
    from coding_tutor.providers.agnes_provider import AgnesProvider
    from coding_tutor.providers.config import AGNES_MODELS
    from coding_tutor.providers.base import ChatMessage
    p = AgnesProvider()
    with pytest.raises(RuntimeError, match="AGNES_API_KEY"):
        p.chat([ChatMessage(role="user", content="hi")], AGNES_MODELS[0])


def test_unverified_gemini_model_is_rejected_before_client_creation(monkeypatch):
    from dataclasses import replace

    monkeypatch.setenv("GOOGLE_API_KEY", "secret-google")
    from coding_tutor.providers.base import ChatMessage
    from coding_tutor.providers.config import GEMINI_MODELS
    from coding_tutor.providers.gemini_provider import GeminiProvider
    from google import genai

    client_factory = MagicMock(side_effect=AssertionError("client must not be created"))
    monkeypatch.setattr(genai, "Client", client_factory)
    unverified = replace(
        GEMINI_MODELS[0], verified=False, unverified_reason="test-only unverified model"
    )

    with pytest.raises(ValueError, match="not verified"):
        GeminiProvider().chat(
            [ChatMessage(role="user", content="hello")],
            unverified,
        )
    client_factory.assert_not_called()


def test_get_verified_models_returns_all_currently_verified_models():
    from coding_tutor.providers.config import get_verified_models, ALL_MODELS

    verified = get_verified_models()
    assert all(m.verified for m in verified)
    assert verified == ALL_MODELS
    model_ids = {m.model_id for m in verified}
    assert "agnes-2.5-flash" in model_ids
    assert "gemini-3.7-flash" in model_ids
