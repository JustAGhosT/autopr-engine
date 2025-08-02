"""
AutoPR LLM Provider Manager

Manages multiple LLM providers and provides unified access.
"""

from collections.abc import AsyncGenerator
import logging
from typing import Any

from ..base import AnthropicProvider, LLMMessage, LLMProvider, LLMResponse, OpenAIProvider

logger = logging.getLogger(__name__)


class LLMProviderManager:
    """
    Manager for LLM providers.

    Handles registration, initialization, and routing of LLM requests
    to appropriate providers.
    """

    def __init__(self, config: Any) -> None:
        """
        Initialize the LLM provider manager.

        Args:
            config: AutoPR configuration object
        """
        self.config = config
        self.providers: dict[str, LLMProvider] = {}
        self.default_provider: str | None = None

        # Register built-in providers
        self._register_builtin_providers()

        logger.info("LLM provider manager initialized")

    def _register_builtin_providers(self) -> None:
        """Register built-in LLM providers."""
        try:
            # Register OpenAI provider
            openai_provider = OpenAIProvider()
            self.providers[openai_provider.name] = openai_provider

            # Register Anthropic provider
            anthropic_provider = AnthropicProvider()
            self.providers[anthropic_provider.name] = anthropic_provider

            logger.info("Built-in LLM providers registered")

        except Exception as e:
            logger.exception(f"Failed to register built-in providers: {e}")

    async def initialize(self) -> None:
        """Initialize all configured LLM providers."""
        # Initialize OpenAI if configured
        if hasattr(self.config, "openai_api_key") and self.config.openai_api_key:
            try:
                await self.providers["openai"].initialize({"api_key": self.config.openai_api_key})
                if not self.default_provider:
                    self.default_provider = "openai"
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.exception(f"Failed to initialize OpenAI provider: {e}")

        # Initialize Anthropic if configured
        if hasattr(self.config, "anthropic_api_key") and self.config.anthropic_api_key:
            try:
                await self.providers["anthropic"].initialize(
                    {"api_key": self.config.anthropic_api_key}
                )
                if not self.default_provider:
                    self.default_provider = "anthropic"
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.exception(f"Failed to initialize Anthropic provider: {e}")

        # Set default provider from config
        if hasattr(self.config, "default_llm_provider") and self.config.default_llm_provider:
            if self.config.default_llm_provider in self.providers:
                provider = self.providers[self.config.default_llm_provider]
                if hasattr(provider, "is_initialized") and provider.is_initialized:
                    self.default_provider = self.config.default_llm_provider

    async def cleanup(self) -> None:
        """Clean up all LLM providers."""
        for provider_name, provider in self.providers.items():
            try:
                await provider.cleanup()
                logger.info(f"Cleaned up LLM provider: {provider_name}")
            except Exception as e:
                logger.exception(f"Error cleaning up provider '{provider_name}': {e}")

    def register_provider(self, provider: LLMProvider) -> None:
        """
        Register a custom LLM provider.

        Args:
            provider: LLM provider instance
        """
        self.providers[provider.name] = provider
        logger.info(f"Registered custom LLM provider: {provider.name}")

    def get_provider(self, provider_name: str | None = None) -> LLMProvider | None:
        """
        Get an LLM provider by name.

        Args:
            provider_name: Name of provider to get (uses default if None)

        Returns:
            LLM provider instance or None
        """
        if provider_name is None:
            provider_name = self.default_provider

        if provider_name and provider_name in self.providers:
            provider = self.providers[provider_name]
            # Check if provider is initialized
            if hasattr(provider, "is_initialized") and provider.is_initialized:
                return provider

        return None

    async def generate_completion(
        self,
        messages: list[LLMMessage],
        provider_name: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> LLMResponse | None:
        """
        Generate a completion using the specified or default provider.

        Args:
            messages: List of conversation messages
            provider_name: Provider to use (defaults to configured default)
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            LLM response or None if failed
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return None

        try:
            response = await provider.generate_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            logger.info(f"Generated completion using provider: {provider.name}")
            return response

        except Exception as e:
            logger.exception(f"Failed to generate completion with provider '{provider.name}': {e}")
            return None

    async def generate_stream_completion(
        self,
        messages: list[LLMMessage],
        provider_name: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> AsyncGenerator[LLMResponse]:
        """
        Generate a streaming completion using the specified or default provider.

        Args:
            messages: List of conversation messages
            provider_name: Provider to use (defaults to configured default)
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Yields:
            Partial LLM responses
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return

        try:
            stream = await provider.generate_stream_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            async for response in stream:
                yield response

        except Exception as e:
            logger.exception(
                f"Failed to generate streaming completion with provider '{provider.name}': {e}"
            )
            return  # Exit generator on error

    def get_available_providers(self) -> list[str]:
        """
        Get list of available (initialized) providers.

        Returns:
            List of provider names
        """
        return [
            name
            for name, provider in self.providers.items()
            if hasattr(provider, "is_initialized") and provider.is_initialized
        ]

    def get_all_providers(self) -> list[str]:
        """
        Get list of all registered providers.

        Returns:
            List of provider names
        """
        return list(self.providers.keys())

    async def health_check_all(self) -> dict[str, dict]:
        """
        Perform health check on all providers.

        Returns:
            Dictionary mapping provider names to health status
        """
        health_status = {}

        for provider_name, provider in self.providers.items():
            try:
                status = await provider.health_check()
                health_status[provider_name] = status
            except Exception as e:
                health_status[provider_name] = {
                    "status": "error",
                    "message": f"Health check failed: {e}",
                }

        return health_status

    def get_manager_stats(self) -> dict[str, Any]:
        """
        Get manager statistics.

        Returns:
            Dictionary with manager statistics
        """
        return {
            "total_providers": len(self.providers),
            "initialized_providers": len(self.get_available_providers()),
            "default_provider": self.default_provider,
            "providers": {
                name: provider.get_metadata() for name, provider in self.providers.items()
            },
        }
