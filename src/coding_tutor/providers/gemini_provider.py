import os
from typing import Optional
from coding_tutor.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelOption


class GeminiProvider(BaseProvider):
    """Google Gemini provider — uses GOOGLE_API_KEY env var."""

    def is_configured(self) -> bool:
        return bool(os.environ.get("GOOGLE_API_KEY"))

    def get_model_options(self) -> list[ModelOption]:
        from coding_tutor.providers.config import GEMINI_MODELS
        return GEMINI_MODELS

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
            raise RuntimeError("GOOGLE_API_KEY is not set.")

        import google.generativeai as genai

        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        gmodel = genai.GenerativeModel(model.model_id)

        history = []
        for m in messages:
            role = "user" if m.role == "user" else "model"
            history.append({"role": role, "parts": [m.content]})

        chat = gmodel.start_chat(history=history[:-1])
        response = chat.send_message(history[-1]["parts"][0])

        return ChatResponse(
            content=response.text,
            model=model.model_id,
            provider="gemini",
        )
