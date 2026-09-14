"""Google Gemini provider adapter via the google-genai SDK.

INVARIANT: chat() only forwards *user*-role messages; assistant turns in
the messages list are silently dropped. All user messages are joined into
a single string with double-newline separators and passed as one
`input` argument to client.interactions.create() — the SDK does not accept
a multi-turn history. store=False prevents session persistence on Google's
servers. See config.py for available model options.
"""
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
        client = genai.Client(api_key=self._key())
        thinking_level = model.extra_params.get("thinking_level")
        # Non-user roles are intentionally excluded; see module docstring.
        user_input = "\n\n".join(
            message.content for message in messages if message.role == "user"
        )
        if not user_input:
            raise ValueError("Gemini requires at least one user message.")
        interaction = client.interactions.create(
            model=model.model_id,
            input=user_input,
            system_instruction=system_prompt,
            generation_config={"thinking_level": thinking_level},
            store=False,
        )
        return ChatResponse(
            content=interaction.output_text,
            model=model.model_id,
            provider="gemini",
        )
