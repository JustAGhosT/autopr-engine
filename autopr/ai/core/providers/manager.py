"""
LLM Provider Manager

Manages different LLM providers and their configurations.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from autopr.ai.core.base import LLMMessage, LLMProvider, LLMResponse
from autopr.config import AutoPRConfig

logger = logging.getLogger(__name__)


class LLMProviderManager:
    """Manages multiple LLM providers and routes requests appropriately."""

    def __init__(self, config: AutoPRConfig):
        self.config = config
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider: Optional[str] = None
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize available LLM providers."""
        # Implementation would go here
        pass

    def get_available_providers(self) -> List[str]:
        """Compatibility alias for list_providers to maintain Engine.get_status() compatibility."""
        return self.list_providers()

    async def initialize(self) -> None:
        """Initialize all registered providers (no-op if none)."""
        init_tasks = []
        for provider in self.providers.values():
            if hasattr(provider, "initialize"):
                cfg = getattr(provider, "config", {}) or {}
                init = provider.initialize(cfg)
                if asyncio.iscoroutine(init):
                    init_tasks.append(init)
        if init_tasks:
            await asyncio.gather(*init_tasks)

    async def cleanup(self) -> None:
        """Cleanup all registered providers."""
        tasks = []
        for provider in self.providers.values():
            if hasattr(provider, "cleanup"):
                c = provider.cleanup()
                if asyncio.iscoroutine(c):
                    tasks.append(c)
        if tasks:
            await asyncio.gather(*tasks)

    async def complete(
        self,
        messages: List[LLMMessage],
        provider: Optional[str] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Complete a conversation using the specified or default provider."""
        # Implementation would go here
        pass

    def get_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """Get a specific provider by name."""
        return self.providers.get(provider_name)

    def list_providers(self) -> List[str]:
        """List all available provider names."""
        return list(self.providers.keys())

    def get_default_provider(self) -> Optional[str]:
        """Get the default provider name."""
        return self.default_provider

    def set_default_provider(self, provider_name: str) -> None:
        """Set the default provider."""
        if provider_name in self.providers:
            self.default_provider = provider_name
        else:
            raise ValueError(f"Provider '{provider_name}' not found")
