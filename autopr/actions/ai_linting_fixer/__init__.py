"""
AI Linting Fixer Package.

A comprehensive AI-powered linting fixer with modular architecture.
"""

from collections.abc import Callable
from typing import Any

# Optional CodeAnalyzer (psutil optional dep)
try:
    from autopr.actions.ai_linting_fixer.code_analyzer import \
        CodeAnalyzer as _CodeAnalyzer

    CODE_ANALYZER_AVAILABLE = True
except Exception:
    _CodeAnalyzer = None  # type: ignore[assignment]
    CODE_ANALYZER_AVAILABLE = False
from autopr.actions.ai_linting_fixer.detection import IssueDetector
from autopr.actions.ai_linting_fixer.display import (DisplayConfig,
                                                     DisplayFormatter,
                                                     ErrorDisplay, OutputMode)
from autopr.actions.ai_linting_fixer.error_handler import (
    ErrorCategory, ErrorContext, ErrorHandler, ErrorInfo,
    ErrorRecoveryStrategy, ErrorSeverity, create_error_context,
    get_default_error_handler)
from autopr.actions.ai_linting_fixer.file_manager import FileManager
from autopr.actions.ai_linting_fixer.issue_fixer import IssueFixer
from autopr.actions.ai_linting_fixer.models import (AILintingFixerInputs,
                                                    AILintingFixerOutputs,
                                                    FixAttemptLog,
                                                    LintingFixResult,
                                                    LintingIssue,
                                                    OrchestrationConfig,
                                                    PerformanceMetrics,
                                                    WorkflowContext,
                                                    WorkflowEvent,
                                                    WorkflowResult)
from autopr.actions.ai_linting_fixer.orchestration import (
    create_workflow_context, detect_available_orchestrators,
    execute_with_orchestration, get_orchestration_config,
    validate_orchestration_config)
from autopr.actions.ai_linting_fixer.performance_tracker import \
    PerformanceTracker

# Optional symbols (pre-declared as variables)
AIAgentManager: Any | None = None
AILintingFixer: Any | None = None
create_ai_linting_fixer: Callable[..., Any] | None = None
run_ai_linting_fixer: Callable[..., Any] | None = None

# AI Components (optional imports)
try:
    from autopr.actions.ai_linting_fixer.ai_agent_manager import \
        AIAgentManager as _AIAgentManager

    AIAgentManager = _AIAgentManager
    AI_COMPONENTS_AVAILABLE = True
except ImportError:
    AI_COMPONENTS_AVAILABLE = False

# Main class (optional AI imports)
try:
    from autopr.actions.ai_linting_fixer.ai_linting_fixer import \
        AILintingFixer as _AILintingFixer
    from autopr.actions.ai_linting_fixer.ai_linting_fixer import \
        create_ai_linting_fixer as _create_ai_linting_fixer
    from autopr.actions.ai_linting_fixer.ai_linting_fixer import \
        run_ai_linting_fixer as _run_ai_linting_fixer

    AILintingFixer = _AILintingFixer
    create_ai_linting_fixer = _create_ai_linting_fixer
    run_ai_linting_fixer = _run_ai_linting_fixer
    AI_LINTING_FIXER_AVAILABLE = True
except ImportError:
    AI_LINTING_FIXER_AVAILABLE = False

__all__ = [
    "AIAgentManager",
    "AILintingFixer",
    "AILintingFixerInputs",
    "AILintingFixerOutputs",
    "CodeAnalyzer",
    "DisplayConfig",
    "DisplayFormatter",
    "ErrorCategory",
    "ErrorContext",
    "ErrorDisplay",
    "ErrorHandler",
    "ErrorInfo",
    "ErrorRecoveryStrategy",
    "ErrorSeverity",
    "FileManager",
    "FixAttemptLog",
    "IssueDetector",
    "IssueFixer",
    "LintingFixResult",
    "LintingIssue",
    "OrchestrationConfig",
    "OutputMode",
    "PerformanceMetrics",
    "PerformanceTracker",
    "WorkflowContext",
    "WorkflowEvent",
    "WorkflowResult",
    "create_ai_linting_fixer",
    "create_error_context",
    "create_workflow_context",
    "detect_available_orchestrators",
    "execute_with_orchestration",
    "get_default_error_handler",
    "get_orchestration_config",
    "run_ai_linting_fixer",
    "validate_orchestration_config",
]

# Remove optional components from __all__ if not available
if not AI_COMPONENTS_AVAILABLE:
    __all__ = [item for item in __all__ if item != "AIAgentManager"]

if not AI_LINTING_FIXER_AVAILABLE:
    __all__ = [
        item
        for item in __all__
        if item
        not in ["AILintingFixer", "create_ai_linting_fixer", "run_ai_linting_fixer"]
    ]

if not CODE_ANALYZER_AVAILABLE:
    __all__ = [item for item in __all__ if item != "CodeAnalyzer"]

# Public name binding (if available)
if CODE_ANALYZER_AVAILABLE:
    CodeAnalyzer = _CodeAnalyzer  # type: ignore[misc]
