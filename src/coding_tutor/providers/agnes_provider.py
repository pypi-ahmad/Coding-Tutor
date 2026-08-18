import os
from typing import Optional
from coding_tutor.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelOption

AGNES_BASE_URL = "https://apihub.agnes-ai.com/v1"


class AgnesProvider(BaseProvider):
    """Agnes AI provider — uses AGNES_API_KEY env var.

    OpenAI-compatible API at https://apihub.agnes-ai.com/v1.
    Model: agnes-2.5-flash (verified).
    """

    def is_configured(self) -> bool:
        return bool(os.environ.get("AGNES_API_KEY", "").strip())

    def get_model_options(self) -> list[ModelOption]:
        from coding_tutor.providers.config import AGNES_MODELS
        return AGNES_MODELS

    def chat(
        self,
        messages: list[ChatMessage],
        model: ModelOption,
        system_prompt: Optional[str] = None,
    ) -> ChatResponse:
        if not model.verified:
            raise ValueError(
                f"Model {model.model_id} is not verified and cannot be used. "
                f"Reason: {model.unverified_reason}"
            )
        if not self.is_configured():
            raise RuntimeError("AGNES_API_KEY is not set.")

        from openai import OpenAI

        client = OpenAI(
            api_key=os.environ["AGNES_API_KEY"],
            base_url=AGNES_BASE_URL,
        )

        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        for m in messages:
            formatted.append({"role": m.role, "content": m.content})

        response = client.chat.completions.create(
            model=model.model_id,
            messages=formatted,
        )
        return ChatResponse(
            content=response.choices[0].message.content,
            model=model.model_id,
            provider="agnes",
        )
