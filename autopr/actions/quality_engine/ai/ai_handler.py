"""
AI Handler for Quality Engine

Handles AI interactions for quality analysis.
"""

import asyncio
import os
import time
from typing import Any

import structlog

from autopr.actions.quality_engine.models import ToolResult

logger = structlog.get_logger(__name__)


async def run_ai_analysis(
    files: list[str],
    llm_manager: Any,
    provider_name: str = "openai",
    model: str = "gpt-4",
) -> dict[str, Any] | None:
    """Run AI-enhanced code analysis.

    Args:
        files: List of files to analyze
        llm_manager: The LLM provider manager
        provider_name: Optional specific provider to use
        model: Optional specific model to use

    Returns:
        Dictionary with analysis results or None if analysis fails
    """
    try:
        # Lazy import to avoid circular dependencies
        from autopr.actions.quality_engine.ai.ai_modes import \
            run_ai_analysis as run_analysis

        # Resolve provider/model against what's actually registered in the manager
        available = (
            llm_manager.list_providers()
            if hasattr(llm_manager, "list_providers")
            else llm_manager.get_available_providers()
        ) or []
        selected_provider = provider_name
        if selected_provider not in available:
            # Prefer manager default, else the first available
            selected_provider = getattr(llm_manager, "default_provider", None) or (
                llm_manager.get_default_provider()  # type: ignore[attr-defined]
                if hasattr(llm_manager, "get_default_provider")
                else (available[0] if available else None)
            )
            logger.info(
                "Provider not available; falling back",
                requested=provider_name,
                fallback=selected_provider,
            )
            provider_name = selected_provider or provider_name
            # Align model to provider default if provided/known
            prov = (
                llm_manager.get_provider(provider_name)
                if hasattr(llm_manager, "get_provider")
                else None
            )
            if prov and hasattr(prov, "default_model"):
                model = getattr(prov, "default_model") or model

        logger.info("Starting AI-enhanced analysis", file_count=len(files), provider=provider_name, model=model)
        start_time = time.time()

        # Run the AI analysis
        result = await run_analysis(files, llm_manager, provider_name, model)
        if result is None:
            logger.warning("AI analysis returned None result")
            return None
        else:
            execution_time = time.time() - start_time
            logger.info(
                "AI analysis completed",
                issues_found=len(result.get("issues", [])),
                execution_time=f"{execution_time:.2f}s",
            )

            # Add execution time to the result
            result["execution_time"] = execution_time

            return result

    except Exception as e:
        logger.exception("Error running AI analysis", error=str(e))
        return None


async def initialize_llm_manager() -> Any | None:
    """Initialize the LLM manager for AI analysis.

    Returns:
        Initialized LLM manager or None if initialization fails
    """
    try:
        from autopr.ai.core.providers.manager import LLMProviderManager

        # Basic configuration for quality analysis
        config: dict[str, Any] = {
            "providers": {
                "openai": {
                    "api_key": os.getenv("OPENAI_API_KEY", ""),
                    "default_model": "gpt-4",
                    "max_tokens": 4000,
                    "temperature": 0.1,
                },
                "anthropic": {
                    "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                    "default_model": "claude-3-sonnet-20240229",
                    "max_tokens": 4000,
                    "temperature": 0.1,
                },
            },
            "fallback_order": ["openai", "anthropic"],
            "default_provider": "openai",
        }

        # Create an AutoPRConfig object with the required attributes
        from autopr.config import AutoPRConfig

        config_obj = AutoPRConfig(
            openai_api_key=config["providers"]["openai"]["api_key"],
            anthropic_api_key=config["providers"]["anthropic"]["api_key"],
            default_llm_provider=config.get("default_provider", "openai")
        )
        llm_manager = LLMProviderManager(config_obj)

        # Configure existing providers if they are available
        if config["providers"]["openai"]["api_key"]:
            openai_provider = llm_manager.get_provider("openai")
            if openai_provider:
                openai_provider.default_model = config["providers"]["openai"]["default_model"]
                logger.info("OpenAI provider configured")
            else:
                logger.info("OpenAI provider not found in manager")

        if config["providers"]["anthropic"]["api_key"]:
            anthropic_provider = llm_manager.get_provider("anthropic")
            if anthropic_provider:
                anthropic_provider.default_model = config["providers"]["anthropic"]["default_model"]
                logger.info("Anthropic provider configured")
            else:
                logger.info("Anthropic provider not found in manager")

        # Set fallback order and default provider
        if config["providers"]["openai"]["api_key"]:
            llm_manager.set_default_provider("openai")
        elif config["providers"]["anthropic"]["api_key"]:
            llm_manager.set_default_provider("anthropic")

        # Initialize the LLM manager
        try:
            if hasattr(llm_manager, "initialize"):
                initializer = llm_manager.initialize
                if asyncio.iscoroutinefunction(initializer):
                    await initializer()
                else:
                    # Handle case where initializer may return a coroutine
                    result = initializer()
                    if asyncio.iscoroutine(result):
                        await result
                logger.info("LLM provider manager initialized successfully")
            else:
                logger.info("LLM provider manager does not require initialization")
        except Exception:
            logger.exception("Failed to initialize LLM manager")
            return None
        else:
            # Get available providers after initialization
            if hasattr(llm_manager, "list_providers"):
                available_providers = llm_manager.list_providers()
            else:
                available_providers = llm_manager.get_available_providers()
            logger.info(
                "LLM provider manager ready", available_providers=available_providers
            )

            if not available_providers:
                logger.warning("No LLM providers available for AI-enhanced analysis")
                return None

            return llm_manager

    except Exception as e:
        logger.exception("Failed to initialize LLM provider manager", error=str(e))
        return None


def create_tool_result_from_ai_analysis(ai_result: dict[str, Any]) -> ToolResult:
    """Convert AI analysis results to a ToolResult.

    Args:
        ai_result: The raw AI analysis result

    Returns:
        A ToolResult instance containing the AI analysis results
    """
    return ToolResult(
        issues=ai_result.get("issues", []),
        files_with_issues=ai_result.get("files_with_issues", []),
        summary=ai_result.get("summary", "AI analysis completed"),
        execution_time=ai_result.get("execution_time", 0.0),
    )
