import os
from typing import Optional
from coding_tutor.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelOption


class OpenAIProvider(BaseProvider):
    """OpenAI provider — uses OPENAI_API_KEY and OPENAI_BASE_URL env vars."""

    def is_configured(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    def get_model_options(self) -> list[ModelOption]:
        from coding_tutor.providers.config import OPENAI_MODELS
        return OPENAI_MODELS

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
            raise RuntimeError("OPENAI_API_KEY is not set.")

        from openai import OpenAI

        client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ.get("OPENAI_BASE_URL"),
        )

        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        for m in messages:
            formatted.append({"role": m.role, "content": m.content})

        params = {"model": model.model_id, "messages": formatted}
        params.update(model.extra_params)

        response = client.chat.completions.create(**params)
        return ChatResponse(
            content=response.choices[0].message.content,
            model=model.model_id,
            provider="openai",
        )
