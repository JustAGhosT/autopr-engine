"""
AI-enhanced analysis functionality for the quality engine
"""

import time
from typing import Any

import structlog

from .models import ToolResult

logger = structlog.get_logger(__name__)


async def run_ai_analysis(
    files: list[str],
    llm_manager: Any,
    provider_name: str | None = None,
    model: str | None = None,
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
        from .ai_modes import run_ai_analysis as run_analysis

        logger.info("Starting AI-enhanced analysis", file_count=len(files))
        start_time = time.time()

        # Run the AI analysis
        result = await run_analysis(files, llm_manager, provider_name, model)

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
        logger.error("Error running AI analysis", error=str(e))
        return None


async def initialize_llm_manager() -> Any | None:
    """Initialize the LLM manager for AI analysis.

    Returns:
        Initialized LLM manager or None if initialization fails
    """
    try:
        from autopr.ai.providers.manager import LLMProviderManager
        from autopr.config.settings import AutoPRConfig

        config = AutoPRConfig()
        llm_manager = LLMProviderManager(config)
        await llm_manager.initialize()

        available_providers = llm_manager.get_available_providers()
        logger.info("Initialized LLM provider manager", available_providers=available_providers)

        if not available_providers:
            logger.warning("No LLM providers available for AI-enhanced analysis")
            return None

        return llm_manager

    except Exception as e:
        logger.error("Failed to initialize LLM provider manager", error=str(e))
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
