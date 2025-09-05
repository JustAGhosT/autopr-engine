"""
LLM Provider Manager

Manages different LLM providers and their configurations.
"""

import asyncio
import logging
import os
from typing import Any

from autopr.ai.core.base import (CompletionRequest, LLMMessage, LLMProvider,
                                 LLMResponse)
from autopr.config import AutoPRConfig

logger = logging.getLogger(__name__)


class LLMProviderManager:
    """Manages multiple LLM providers and routes requests appropriately."""

    def __init__(self, config: AutoPRConfig):
        self.config = config
        self.providers: dict[str, LLMProvider] = {}
        self.default_provider: str | None = None
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize available LLM providers based on environment and configuration."""
        # Check for OpenAI provider
        if os.getenv("OPENAI_API_KEY"):
            try:
                from autopr.ai.core.base import OpenAIProvider

                openai_provider = OpenAIProvider()
                openai_provider.config = {
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                }

                self.register_provider("openai", openai_provider)
                logger.info("OpenAI provider registered successfully")
            except ImportError:
                logger.warning("OpenAI provider module not available")
            except Exception as e:
                logger.warning("Failed to register OpenAI provider: %s", e)
        else:
            logger.debug("OpenAI API key not found, skipping OpenAI provider")

        # Check for Anthropic provider
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                from autopr.ai.core.base import AnthropicProvider

                anthropic_provider = AnthropicProvider()
                anthropic_provider.config = {
                    "api_key": os.getenv("ANTHROPIC_API_KEY"),
                    "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
                }

                self.register_provider("anthropic", anthropic_provider)
                logger.info("Anthropic provider registered successfully")
            except ImportError:
                logger.warning("Anthropic provider module not available")
            except Exception as e:
                logger.warning("Failed to register Anthropic provider: %s", e)
        else:
            logger.debug("Anthropic API key not found, skipping Anthropic provider")

        # Log final provider count
        provider_count = len(self.providers)
        if provider_count == 0:
            logger.warning("No LLM providers registered - AI flows will be disabled")
        else:
            logger.info(
                "Registered %d LLM provider(s): %s", provider_count, list(self.providers.keys())
            )

    def register_provider(self, name: str, provider: LLMProvider) -> None:
        """Register a provider with the manager.

        Args:
            name: Provider name/identifier
            provider: Provider instance to register
        """
        self.providers[name] = provider
        logger.info("Registered provider: %s", name)

        # Set as default if this is the first provider
        if self.default_provider is None:
            self.default_provider = name

    def get_available_providers(self) -> list[str]:
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

    async def complete_async(
        self, request: CompletionRequest, provider: str | None = None, **kwargs: Any
    ) -> LLMResponse:
        """Complete a conversation using the request object and specified or default provider."""
        # Use provider from request if not specified
        target_provider = provider or request.provider or self.default_provider

        if not target_provider:
            msg = "No provider specified and no default provider available"
            raise ValueError(msg)

        if target_provider not in self.providers:
            msg = f"Provider '{target_provider}' not found"
            raise ValueError(msg)

        provider_instance = self.providers[target_provider]

        # Initialize provider if not already initialized
        if not getattr(provider_instance, "_is_initialized", False):
            await provider_instance.initialize(provider_instance.config)

        # Call the provider's generate_completion method
        return await provider_instance.generate_completion(
            messages=request.messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            **kwargs,
        )

    async def complete(
        self,
        messages_or_request: list[LLMMessage] | CompletionRequest,
        provider: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Complete a conversation using either request object or legacy parameters."""
        # Detect if first argument is a request object or legacy messages list
        if isinstance(messages_or_request, CompletionRequest):
            # Request-style API
            return await self.complete_async(messages_or_request, provider, **kwargs)
        else:
            # Legacy API - convert to request object
            messages = messages_or_request
            request = CompletionRequest(messages=messages, provider=provider, **kwargs)
            return await self.complete_async(request)

    def get_provider(self, provider_name: str) -> LLMProvider | None:
        """Get a specific provider by name."""
        return self.providers.get(provider_name)

    def list_providers(self) -> list[str]:
        """List all available provider names."""
        return list(self.providers.keys())

    def get_default_provider(self) -> str | None:
        """Get the default provider name."""
        return self.default_provider

    def set_default_provider(self, provider_name: str) -> None:
        """Set the default provider."""
        if provider_name in self.providers:
            self.default_provider = provider_name
        else:
            error_msg = f"Provider '{provider_name}' not found"
            raise ValueError(error_msg)
