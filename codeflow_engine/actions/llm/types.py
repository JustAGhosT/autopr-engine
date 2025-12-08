"""
Base types, enums, and data classes for LLM providers.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class MessageRole(StrEnum):
    """Role of a message in a chat conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """A message in a chat conversation."""

    role: MessageRole
    content: str
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


class LLMProviderType(StrEnum):
    """Supported LLM providers."""

    GROQ = "groq"
    MISTRAL = "mistral"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    TOGETHER = "together"


class LLMConfig(BaseModel):
    """Configuration for an LLM provider."""

    provider: LLMProviderType
    model: str
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list[str] | None = None


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    finish_reason: str
    usage: dict[str, int] | None = None
    error: str | None = None

    @classmethod
    def from_error(cls, error: str, model: str = "unknown") -> "LLMResponse":
        """Create an error response."""
        return cls(content="", model=model, finish_reason="error", error=error)
