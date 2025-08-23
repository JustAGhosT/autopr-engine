"""
LLM Provider Manager - Manages multiple LLM providers with fallback support.
"""

import logging
from typing import Any

from autopr.actions.llm.base import BaseLLMProvider
from autopr.actions.llm.providers import (
    AnthropicProvider,
    GroqProvider,
    MistralProvider,
    OpenAIProvider,
    PerplexityProvider,
    TogetherAIProvider,
)
from autopr.actions.llm.providers.azure_openai import AzureOpenAIProvider
from autopr.actions.llm.types import LLMResponse


logger = logging.getLogger(__name__)


class ActionLLMProviderManager:
    """Manages multiple LLM providers with fallback support for action-driven use cases."""

    def __init__(self, config: dict[str, Any], display=None) -> None:
        self.providers: dict[str, BaseLLMProvider] = {}
        self.fallback_order: list[str] = config.get(
            "fallback_order", ["azure_openai", "openai", "anthropic", "mistral"]
        )
        self.default_provider: str = config.get("default_provider", "azure_openai")
        self.display = display

        # Initialize providers based on configuration
        provider_configs: dict[str, dict[str, Any]] = config.get("providers", {})

        # Default provider configurations
        default_configs: dict[str, dict[str, Any]] = {
            "openai": {
                "api_key_env": "OPENAI_API_KEY",
                "default_model": "gpt-4",
                "base_url": None,
            },
            "azure_openai": {
                "api_key_env": "AZURE_OPENAI_API_KEY",
                "default_model": "gpt-35-turbo",
                "azure_endpoint": "https://dev-saf-openai-phoenixvc-ai.openai.azure.com/",
                "api_version": "2024-02-01",
                "deployment_name": "gpt-35-turbo",
            },
            "anthropic": {
                "api_key_env": "ANTHROPIC_API_KEY",
                "default_model": "claude-3-sonnet-20240229",
                "base_url": None,
            },
            "mistral": {
                "api_key_env": "MISTRAL_API_KEY",
                "default_model": "mistral-large-latest",
                "base_url": None,
            },
            "groq": {
                "api_key_env": "GROQ_API_KEY",
                "default_model": "mixtral-8x7b-32768",
                "base_url": None,
            },
            "perplexity": {
                "api_key_env": "PERPLEXITY_API_KEY",
                "default_model": "llama-3.1-sonar-large-128k-online",
                "base_url": None,
            },
            "together": {
                "api_key_env": "TOGETHER_API_KEY",
                "default_model": "meta-llama/Llama-2-70b-chat-hf",
                "base_url": None,
            },
        }

        # Merge user configs with defaults
        for provider_name, default_config in default_configs.items():
            user_config: dict[str, Any] = provider_configs.get(provider_name, {})
            merged_config: dict[str, Any] = {**default_config, **user_config}

            # Initialize provider
            try:
                if provider_name == "openai":
                    self.providers[provider_name] = OpenAIProvider(merged_config)
                elif provider_name == "azure_openai":
                    self.providers[provider_name] = AzureOpenAIProvider(merged_config)
                elif provider_name == "anthropic":
                    self.providers[provider_name] = AnthropicProvider(merged_config)
                elif provider_name == "mistral":
                    self.providers[provider_name] = MistralProvider(merged_config)
                elif provider_name == "groq":
                    self.providers[provider_name] = GroqProvider(merged_config)
                elif provider_name == "perplexity":
                    self.providers[provider_name] = PerplexityProvider(merged_config)
                elif provider_name == "together":
                    self.providers[provider_name] = TogetherAIProvider(merged_config)
            except Exception as e:
                # Log the error for debugging
                logger.debug(f"Failed to initialize {provider_name} provider: {e}")

                # Only show warning if this provider is in the fallback order or is the default
                if (
                    provider_name in self.fallback_order
                    or provider_name == self.default_provider
                ):
                    if self.display:
                        self.display.error.show_warning(
                            f"Provider {provider_name} not available: {e!s}"
                        )
                    else:
                        # Fallback to logger if no display is available
                        logger.warning(
                            f"Failed to initialize {provider_name} provider: {e}"
                        )

    def get_provider(self, provider_name: str) -> BaseLLMProvider | None:
        """
        Get a provider by name.

        Args:
            provider_name: Name of the provider to retrieve (e.g., 'openai', 'anthropic')

        Returns:
            The provider instance if found and available, None otherwise
        """
        provider = self.providers.get(provider_name.lower())
        if provider is not None and provider.is_available():
            return provider
        return None

    # Backward-compatibility helpers used in tests
    def get_llm(self, provider_name: str) -> BaseLLMProvider | None:
        """Alias for get_provider to satisfy older code/tests."""
        return self.get_provider(provider_name)

    def complete(self, request: dict[str, Any]) -> LLMResponse:
        """
        Complete a chat conversation using the specified or default provider with fallback.

        Args:
            request: Dictionary containing the request parameters including:
                - provider: Optional provider name to use
                - model: Optional model name to use
                - messages: List of message dictionaries with 'role' and 'content'
                - Other provider-specific parameters

        Returns:
            LLMResponse containing the completion response or error
        """
        # Make a copy of the request to avoid modifying the original
        request = request.copy()

        # Get the requested provider or use default
        provider_name = request.pop("provider", self.default_provider)
        if not provider_name:
            return LLMResponse.from_error(
                "No provider specified and no default provider configured",
                request.get("model") or "unknown",
            )

        # Try to get the requested provider
        provider = self.get_provider(provider_name)
        if provider is None:
            # Try fallback providers
            for fallback_name in self.fallback_order:
                if fallback_name != provider_name:
                    fallback_provider = self.get_provider(fallback_name)
                    if fallback_provider is not None:
                        logger.info(
                            f"Using fallback provider '{fallback_name}' instead of '{provider_name}'"
                        )
                        provider = fallback_provider

            if provider is None:
                return LLMResponse.from_error(
                    f"Provider '{provider_name}' not found or not available, and no fallback providers available",
                    request.get("model") or "unknown",
                )

        # Ensure required fields are present
        if "messages" not in request:
            return LLMResponse.from_error(
                "Missing required field 'messages' in request",
                request.get("model") or "unknown",
            )

        # Set default model if not specified
        if "model" not in request and hasattr(provider, "default_model"):
            request["model"] = provider.default_model

        try:
            # Call the provider's complete method
            return provider.complete(request)
        except Exception as e:
            error_msg = f"Error calling provider '{provider_name}': {e!s}"
            logger.exception(error_msg)
            return LLMResponse.from_error(error_msg, request.get("model") or "unknown")

    def get_available_providers(self) -> list[str]:
        """Get list of available providers."""
        return [
            name for name, provider in self.providers.items() if provider.is_available()
        ]

    def get_provider_info(self) -> dict[str, Any]:
        """Get information about all providers."""
        info: dict[str, Any] = {
            "available_providers": self.get_available_providers(),
            "default_provider": self.default_provider,
            "fallback_order": self.fallback_order,
            "providers": {},
        }

        for name, provider in self.providers.items():
            info["providers"][name] = {
                "available": provider.is_available(),
                "default_model": getattr(provider, "default_model", "unknown"),
            }

        return info
