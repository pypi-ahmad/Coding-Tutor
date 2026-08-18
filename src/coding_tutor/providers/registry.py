"""Provider registry — maps provider name to provider instance."""
from coding_tutor.providers.openai_provider import OpenAIProvider
from coding_tutor.providers.agnes_provider import AgnesProvider
from coding_tutor.providers.gemini_provider import GeminiProvider
from coding_tutor.providers.base import BaseProvider

PROVIDERS: dict[str, BaseProvider] = {
    "openai": OpenAIProvider(),
    "agnes": AgnesProvider(),
    "gemini": GeminiProvider(),
}

PROVIDER_DISPLAY_NAMES = {
    "openai": "OpenAI",
    "agnes": "Agnes AI",
    "gemini": "Google Gemini",
}


def get_provider(name: str) -> BaseProvider:
    if name not in PROVIDERS:
        raise KeyError(f"Unknown provider: {name}")
    return PROVIDERS[name]
