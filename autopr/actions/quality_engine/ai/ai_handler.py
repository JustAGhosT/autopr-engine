"""
AI Handler for Quality Engine

Handles AI interactions for quality analysis.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from autopr.actions.quality_engine.ai.ai_analyzer import AIAnalyzer
from autopr.actions.quality_engine.ai.llm_manager import LLMManager
from autopr.actions.quality_engine.models import QualityAnalysis, QualityIssue
from autopr.ai.core.providers.manager import LLMProviderManager

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

        logger.info("Starting AI-enhanced analysis", file_count=len(files))
        start_time = time.time()

        # Run the AI analysis
        result = await run_analysis(files, llm_manager, provider_name, model)

        if result is None:
            logger.warning("AI analysis returned None result")
            return None

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
        from autopr.ai.providers.manager import LLMProviderManager

        # Basic configuration for quality analysis
        config = {
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

        # Create a simple config object with the required attributes
        class SimpleConfig:
            def __init__(self, config_dict):
                self.openai_api_key = config_dict["providers"]["openai"]["api_key"]
                self.anthropic_api_key = config_dict["providers"]["anthropic"][
                    "api_key"
                ]
                self.default_llm_provider = config_dict.get(
                    "default_provider", "openai"
                )

        config_obj = SimpleConfig(config)
        llm_manager = LLMProviderManager(config_obj)

        # Initialize the LLM manager
        try:
            await llm_manager.initialize()
            logger.info("LLM provider manager initialized successfully")
        except Exception as init_error:
            logger.exception(f"Failed to initialize LLM manager: {init_error}")
            return None

        # Get available providers after initialization
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
