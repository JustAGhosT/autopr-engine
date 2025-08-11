"""
Abstract base class for LLM providers.
"""

from abc import ABC, abstractmethod
import os
from typing import Any

from .types import LLMResponse


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.api_key = config.get("api_key") or os.getenv(config.get("api_key_env", ""))
        self.base_url = config.get("base_url")
        self.default_model = config.get("default_model")

    @abstractmethod
    def complete(self, request: dict[str, Any]) -> LLMResponse:
        """Complete a chat conversation."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured and available."""
