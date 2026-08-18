"""Tests for provider configuration and secret handling."""
import os
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


def test_unverified_model_raises_on_chat():
    from coding_tutor.providers.openai_provider import OpenAIProvider
    from coding_tutor.providers.config import OPENAI_MODELS
    from coding_tutor.providers.base import ChatMessage
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        p = OpenAIProvider()
        unverified = OPENAI_MODELS[0]
        assert not unverified.verified
        with pytest.raises(ValueError, match="not verified"):
            p.chat([ChatMessage(role="user", content="hi")], unverified)
    finally:
        os.environ.pop("OPENAI_API_KEY", None)


def test_agnes_chat_raises_without_key():
    from coding_tutor.providers.agnes_provider import AgnesProvider
    from coding_tutor.providers.config import AGNES_MODELS
    from coding_tutor.providers.base import ChatMessage
    p = AgnesProvider()
    with pytest.raises(RuntimeError, match="AGNES_API_KEY"):
        p.chat([ChatMessage(role="user", content="hi")], AGNES_MODELS[0])


def test_get_verified_models_excludes_unverified():
    from coding_tutor.providers.config import get_verified_models, ALL_MODELS
    verified = get_verified_models()
    assert all(m.verified for m in verified)
    assert len(verified) < len(ALL_MODELS)
    model_ids = {m.model_id for m in verified}
    assert "agnes-2.5-flash" in model_ids
