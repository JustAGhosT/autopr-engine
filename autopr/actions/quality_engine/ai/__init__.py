"""
AI-Enhanced Quality Analysis Module

This module provides AI-powered code analysis capabilities for the Quality Engine,
integrating with the AutoPR LLM provider system.
"""

from autopr.actions.quality_engine.ai.ai_analyzer import AICodeAnalyzer, CodeSuggestion


try:  # Provide resilient exports; these modules may be optional in some environments
    from autopr.actions.quality_engine.ai.ai_handler import (
        AIHandler,
    )  # type: ignore[import-not-found,attr-defined]
except Exception:  # pragma: no cover
    AIHandler = None  # type: ignore[assignment]

try:
    from autopr.actions.quality_engine.ai.ai_modes import (
        QualityMode,
        analyze_code_architecture,
        analyze_security_issues,
        create_tool_result_from_ai_analysis,
        initialize_llm_manager,
        run_ai_analysis,
    )
except Exception:  # pragma: no cover
    QualityMode = None  # type: ignore[assignment]
    analyze_code_architecture = None  # type: ignore[assignment]
    analyze_security_issues = None  # type: ignore[assignment]
    create_tool_result_from_ai_analysis = None  # type: ignore[assignment]
    initialize_llm_manager = None  # type: ignore[assignment]
    run_ai_analysis = None  # type: ignore[assignment]

__all__ = [
    "AICodeAnalyzer",
    "AIHandler",
    "CodeSuggestion",
    "QualityMode",
    "analyze_code_architecture",
    "analyze_security_issues",
    "create_tool_result_from_ai_analysis",
    "initialize_llm_manager",
    "run_ai_analysis",
]
