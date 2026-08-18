"""Tests for app configuration and core module imports."""
import pytest


def test_coding_tutor_imports():
    import coding_tutor
    from coding_tutor.providers import base, config, registry
    from coding_tutor.providers.base import ModelOption, ChatMessage, ChatResponse, BaseProvider


def test_all_model_options_have_required_fields():
    from coding_tutor.providers.config import ALL_MODELS
    for model in ALL_MODELS:
        assert model.provider, f"Missing provider for {model}"
        assert model.model_id, f"Missing model_id for {model}"
        assert model.display_name, f"Missing display_name for {model}"
        if not model.verified:
            assert model.unverified_reason, f"Unverified model {model.model_id} must have a reason"


def test_agnes_model_is_verified():
    from coding_tutor.providers.config import AGNES_MODELS
    assert len(AGNES_MODELS) == 1
    assert AGNES_MODELS[0].model_id == "agnes-2.5-flash"
    assert AGNES_MODELS[0].verified is True


def test_openai_model_is_unverified():
    from coding_tutor.providers.config import OPENAI_MODELS
    assert all(not m.verified for m in OPENAI_MODELS)


def test_gemini_models_are_unverified():
    from coding_tutor.providers.config import GEMINI_MODELS
    assert all(not m.verified for m in GEMINI_MODELS)
    model_ids = {m.model_id for m in GEMINI_MODELS}
    assert "gemini-3.5-flash-lite" in model_ids
    assert "gemini-3.7-flash" in model_ids


def test_streamlit_config_exists():
    import os
    import tomllib
    config_path = os.path.join(os.path.dirname(__file__), "..", ".streamlit", "config.toml")
    assert os.path.exists(config_path), ".streamlit/config.toml must exist"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)
    assert cfg["server"]["port"] == 8551
    assert cfg["server"]["address"] == "127.0.0.1"
