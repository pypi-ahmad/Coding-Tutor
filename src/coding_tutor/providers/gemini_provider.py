import os
from typing import Optional
from coding_tutor.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelOption


class GeminiProvider(BaseProvider):
    """Google Gemini provider configured only from GOOGLE_API_KEY."""

    def _key(self) -> str | None:
        return os.environ.get("GOOGLE_API_KEY")

    def is_configured(self) -> bool:
        return bool((self._key() or "").strip())

    def get_model_options(self) -> list[ModelOption]:
        from coding_tutor.providers.config import GEMINI_MODELS
        return GEMINI_MODELS

    def chat(self, messages: list[ChatMessage], model: ModelOption, system_prompt: Optional[str] = None) -> ChatResponse:
        if not model.verified:
            raise ValueError(
                f"Model {model.model_id} is not verified and cannot be used. "
                f"Reason: {model.unverified_reason}"
            )
        if not self.is_configured():
            raise RuntimeError("GOOGLE_API_KEY is not set.")
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=self._key())
        contents = [types.Content(role="model" if m.role == "assistant" else "user", parts=[types.Part(text=m.content)]) for m in messages if m.role != "system"]
        config = types.GenerateContentConfig(system_instruction=system_prompt)
        response = client.models.generate_content(model=model.model_id, contents=contents, config=config)
        return ChatResponse(content=response.text, model=model.model_id, provider="gemini")
