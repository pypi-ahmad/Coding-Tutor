"""Central registry of provider model options."""
from coding_tutor.providers.base import ModelOption

OPENAI_MODELS: list[ModelOption] = [
    ModelOption(
        provider="openai",
        model_id="gpt-5.6-luna",
        display_name="GPT-5.6 Luna (medium reasoning)",
        verified=True,
        documentation_url="https://developers.openai.com/api/docs/models/gpt-5.6-luna",
        extra_params={"reasoning_effort": "medium"},
    ),
]

AGNES_MODELS: list[ModelOption] = [
    ModelOption(
        provider="agnes",
        model_id="agnes-2.5-flash",
        display_name="Agnes 2.5 Flash",
        verified=True,
        documentation_url="https://www.agnes-ai.com/en/docs/agnes-25-flash",
        extra_params={},
    ),
]

GEMINI_MODELS: list[ModelOption] = [
    ModelOption(
        provider="gemini",
        model_id="gemini-3.5-flash-lite",
        display_name="Gemini 3.5 Flash Lite",
        verified=True,
        documentation_url=(
            "https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite"
        ),
        extra_params={"thinking_level": "medium"},
    ),
    ModelOption(
        provider="gemini",
        model_id="gemini-3.7-flash",
        display_name="Gemini 3.7 Flash",
        verified=True,
        documentation_url="https://ai.google.dev/gemini-api/docs/thinking",
        extra_params={"thinking_level": "medium"},
    ),
]

ALL_MODELS: list[ModelOption] = OPENAI_MODELS + AGNES_MODELS + GEMINI_MODELS


def get_verified_models() -> list[ModelOption]:
    return [m for m in ALL_MODELS if m.verified]


def get_models_for_provider(provider: str) -> list[ModelOption]:
    return [m for m in ALL_MODELS if m.provider == provider]
