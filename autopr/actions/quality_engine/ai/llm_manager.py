"""
LLM Manager Initialization for AI-Enhanced Quality Analysis

This module provides initialization and configuration for the LLM provider manager
used in AI-enhanced quality analysis.
"""

import logging
from typing import Any

from autopr.actions.llm.manager import LLMProviderManager

logger = logging.getLogger(__name__)


async def initialize_llm_manager() -> LLMProviderManager | None:
    """
    Initialize the LLM provider manager for AI-enhanced quality analysis.

    Returns:
        LLMProviderManager: Configured LLM manager or None if initialization fails
    """
    try:
        # Basic configuration for quality analysis
        config = {
            "providers": {
                "openai": {
                    "api_key": "${OPENAI_API_KEY}",
                    "default_model": "gpt-4",
                    "max_tokens": 4000,
                    "temperature": 0.1,
                },
                "anthropic": {
                    "api_key": "${ANTHROPIC_API_KEY}",
                    "default_model": "claude-3-sonnet-20240229",
                    "max_tokens": 4000,
                    "temperature": 0.1,
                },
            },
            "fallback_order": ["openai", "anthropic"],
            "default_provider": "openai",
        }

        llm_manager = LLMProviderManager(config)

        # Test the connection
        test_response = await llm_manager.call_llm(
            "openai",
            "Test message",
            system_prompt="You are a helpful assistant.",
            temperature=0.1,
        )

        if test_response and test_response.content:
            logger.info("LLM manager initialized successfully")
            return llm_manager
        else:
            logger.warning("LLM manager test failed - no response received")
            return None

    except Exception as e:
        logger.error(f"Failed to initialize LLM manager: {e}")
        return None


def get_llm_config_for_quality_analysis() -> dict[str, Any]:
    """
    Get configuration for LLM-based quality analysis.

    Returns:
        dict: Configuration for quality analysis LLM usage
    """
    return {
        "max_tokens": 4000,
        "temperature": 0.1,
        "system_prompt": """You are CodeQualityGPT, an expert code review assistant specialized in identifying improvements,
optimizations, and potential issues in code. Your task is to analyze code snippets and provide detailed,
actionable feedback that goes beyond what static analysis tools can find.

Focus on the following aspects:
1. Architecture and design patterns
2. Performance optimization opportunities
3. Security vulnerabilities or risks
4. Maintainability and readability concerns
5. Edge case handling and robustness
6. Business logic flaws or inconsistencies
7. API design and usability

Provide your feedback in a structured JSON format with:
- Specific issues identified
- Why they matter
- How to fix them
- A confidence score (0-1) for each suggestion""",
        "preferred_providers": ["openai", "anthropic"],
        "fallback_providers": ["groq", "mistral"],
    }
