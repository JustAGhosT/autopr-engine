"""
LLM Provider Manager

Manages different LLM providers and their configurations.
"""

import asyncio
import logging
import os
from typing import Any

from codeflow_engine.ai.core.base import (CompletionRequest, LLMMessage, LLMProvider,
                                 LLMResponse)
from codeflow_engine.config import AutoPRConfig
from codeflow_engine.utils.resilience import CircuitBreaker, CircuitBreakerOpenError

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
                from codeflow_engine.ai.core.base import OpenAIProvider

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
                from codeflow_engine.ai.core.base import AnthropicProvider

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
            success_threshold=2,
            timeout=60.0,
            half_open_timeout=30.0,
        )
        
        logger.info("Registered provider: %s with circuit breaker protection", name)

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
        circuit_breaker = self.circuit_breakers[target_provider]

        # Check if circuit breaker allows the request
        if not circuit_breaker.is_available():
            # Try to find an alternative provider
            alternative_provider = self._find_alternative_provider(target_provider)
            if alternative_provider:
                logger.warning(
                    "Provider '%s' circuit breaker is OPEN, using alternative provider '%s'",
                    target_provider, alternative_provider
                )
                target_provider = alternative_provider
                provider_instance = self.providers[target_provider]
                circuit_breaker = self.circuit_breakers[target_provider]
            else:
                # No alternative available, let the circuit breaker handle it
                logger.error(
                    "Provider '%s' circuit breaker is OPEN and no alternative providers available",
                    target_provider
                )

        # Initialize provider if not already initialized
        if not getattr(provider_instance, "_is_initialized", False):
            await provider_instance.initialize(provider_instance.config)

        # Call the provider's generate_completion method with circuit breaker protection
        async def _call_provider():
            return await provider_instance.generate_completion(
                messages=request.messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                **kwargs,
            )
        
        try:
            return await circuit_breaker.call(_call_provider)
        except CircuitBreakerOpenError:
            # Circuit breaker is open, try to find alternative
            alternative_provider = self._find_alternative_provider(target_provider)
            if alternative_provider:
                logger.warning(
                    "Falling back to alternative provider '%s' due to circuit breaker",
                    alternative_provider
                )
                # Recursive call with alternative provider
                return await self.complete_async(request, provider=alternative_provider, **kwargs)
            raise

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
    
    def _find_alternative_provider(self, excluded_provider: str) -> str | None:
        """
        Find an alternative provider that is available (circuit breaker not open).
        
        Args:
            excluded_provider: Provider to exclude from search
            
        Returns:
            Name of alternative provider, or None if none available
        """
        for provider_name, circuit_breaker in self.circuit_breakers.items():
            if provider_name != excluded_provider and circuit_breaker.is_available():
                return provider_name
        return None
    
    def get_circuit_breaker_status(self) -> dict[str, Any]:
        """
        Get status of all circuit breakers.
        
        Returns:
            Dictionary mapping provider names to their circuit breaker stats
        """
        return {
            name: breaker.get_stats()
            for name, breaker in self.circuit_breakers.items()
        }
    
    async def reset_circuit_breaker(self, provider_name: str) -> None:
        """
        Reset circuit breaker for a specific provider.
        
        Args:
            provider_name: Name of the provider
        """
        if provider_name in self.circuit_breakers:
            await self.circuit_breakers[provider_name].reset()
            logger.info("Reset circuit breaker for provider '%s'", provider_name)
        else:
            logger.warning("Provider '%s' not found, cannot reset circuit breaker", provider_name)
