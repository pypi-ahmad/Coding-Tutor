import pytest
import os


@pytest.fixture(autouse=True)
def clear_provider_env(monkeypatch):
    """Remove all provider env vars before each test."""
    for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "AGNES_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(key, raising=False)
