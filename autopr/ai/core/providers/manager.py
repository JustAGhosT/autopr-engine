"""
LLM Provider Manager

Manages different LLM providers and their configurations.
"""

import asyncio
import logging
import os
from typing import Any

from autopr.ai.core.base import CompletionRequest, LLMMessage, LLMProvider, LLMResponse
from autopr.config import AutoPRConfig
from autopr.utils.resilience import CircuitBreaker, CircuitBreakerError


logger = logging.getLogger(__name__)


class LLMProviderManager:
    """Manages multiple LLM providers and routes requests appropriately."""

    def __init__(self, config: AutoPRConfig):
        self.config = config
        self.providers: dict[str, LLMProvider] = {}
        self.default_provider: str | None = None
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
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
        # Create circuit breaker for this provider
        self.circuit_breakers[name] = CircuitBreaker(
            name=f"llm_provider_{name}",
            failure_threshold=5,
            timeout_seconds=60,
            success_threshold=2,
        )
        logger.info("Registered provider: %s with circuit breaker", name)

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
        circuit_breaker = self.circuit_breakers.get(target_provider)

        # Initialize provider if not already initialized
        if not getattr(provider_instance, "_is_initialized", False):
            await provider_instance.initialize(provider_instance.config)

        # Call the provider's generate_completion method with circuit breaker protection
        async def make_completion_call():
            return await provider_instance.generate_completion(
                messages=request.messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                **kwargs,
            )

        if circuit_breaker:
            try:
                return await circuit_breaker.call(make_completion_call)
            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker open for provider '{target_provider}': {e}")
                # Try fallback to another provider if available
                fallback_result = await self._try_fallback_provider(
                    request, target_provider, **kwargs
                )
                if fallback_result:
                    return fallback_result
                raise
        else:
            return await make_completion_call()

    async def _try_fallback_provider(
        self, request: CompletionRequest, failed_provider: str, **kwargs: Any
    ) -> LLMResponse | None:
        """Try to use a fallback provider when primary fails."""
        available_providers = [p for p in self.providers.keys() if p != failed_provider]

        for fallback_provider in available_providers:
            breaker = self.circuit_breakers.get(fallback_provider)
            if breaker and breaker.state.value != "open":
                logger.info(
                    f"Attempting fallback to provider '{fallback_provider}' "
                    f"after '{failed_provider}' failure"
                )
                try:
                    return await self.complete_async(request, fallback_provider, **kwargs)
                except Exception as e:
                    logger.warning(f"Fallback provider '{fallback_provider}' also failed: {e}")
                    continue

        logger.error("All fallback providers exhausted")
        return None

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

    def get_circuit_breaker_status(self) -> dict[str, Any]:
        """
        Get status of all circuit breakers.

        Returns:
            Dictionary mapping provider names to their circuit breaker status
        """
        return {
            provider_name: breaker.get_status()
            for provider_name, breaker in self.circuit_breakers.items()
        }
