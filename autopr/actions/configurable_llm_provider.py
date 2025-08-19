"""
AutoPR Action: Configurable LLM Provider
Unified interface for multiple LLM providers (OpenAI, Anthropic, Mistral, Groq, Perplexity, etc.)

This file has been refactored into a modular structure under autopr.actions.llm.
This module maintains backward compatibility by re-exporting the modular components.
"""

# Re-export everything from the modular LLM package for backward compatibility
from .llm import (  # Types; Base classes; Manager; Providers; Factory functions
    AnthropicProvider,
    BaseLLMProvider,
    GroqProvider,
    LLMConfig,
    LLMProviderManager,
    LLMProviderType,
    LLMResponse,
    Message,
    MessageRole,
    MistralProvider,
    OpenAIProvider,
    PerplexityProvider,
    TogetherAIProvider,
    complete_chat,
    get_llm_provider_manager,
)

# Maintain the same public API
__all__ = [
    "AnthropicProvider",
    # Base classes
    "BaseLLMProvider",
    "GroqProvider",
    "LLMConfig",
    # Manager
    "LLMProviderManager",
    "LLMProviderType",
    "LLMResponse",
    "Message",
    # Types
    "MessageRole",
    "MistralProvider",
    # Providers
    "OpenAIProvider",
    "PerplexityProvider",
    "TogetherAIProvider",
    "complete_chat",
    # Factory functions
    "get_llm_provider_manager",
]
