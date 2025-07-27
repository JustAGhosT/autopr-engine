"""
Abstract base class for LLM providers.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict

from .types import LLMResponse


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.api_key = config.get("api_key") or os.getenv(config.get("api_key_env", ""))
        self.base_url = config.get("base_url")
        self.default_model = config.get("default_model")

    @abstractmethod
    def complete(self, request: Dict[str, Any]) -> LLMResponse:
        """Complete a chat conversation."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured and available."""
        pass
