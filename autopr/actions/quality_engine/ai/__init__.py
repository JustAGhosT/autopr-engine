"""
AI-Enhanced Quality Analysis Module

This module provides AI-powered code analysis capabilities for the Quality Engine,
integrating with the AutoPR LLM provider system.
"""

from .ai_analyzer import AICodeAnalyzer, CodeSuggestion
try:  # Provide resilient exports; these modules may be optional in some environments
    from .ai_handler import AIHandler  # type: ignore[import-not-found,attr-defined]
except Exception:  # pragma: no cover
    AIHandler = None  # type: ignore[assignment]

try:
    from .ai_modes import (  # type: ignore[import-not-found,attr-defined]
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
    "QualityMode",
    "run_ai_analysis",
    "initialize_llm_manager",
    "create_tool_result_from_ai_analysis",
    "analyze_code_architecture",
    "analyze_security_issues",
    "AICodeAnalyzer",
    "CodeSuggestion",
    "AIHandler",
]
