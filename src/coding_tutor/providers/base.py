from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelOption:
    """A selectable model with verification status."""
    provider: str
    model_id: str
    display_name: str
    verified: bool  # True only when confirmed from official docs
    unverified_reason: str = ""  # shown when verified=False
    extra_params: dict = field(default_factory=dict)


@dataclass
class ChatMessage:
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class ChatResponse:
    content: str
    model: str
    provider: str


class BaseProvider(ABC):
    """Common interface for all AI providers."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if env vars are present (never reveal the values)."""
        ...

    @abstractmethod
    def get_model_options(self) -> list[ModelOption]:
        """Return the list of models this provider offers."""
        ...

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage],
        model: ModelOption,
        system_prompt: Optional[str] = None,
    ) -> ChatResponse:
        """Send a chat request and return a response."""
        ...
