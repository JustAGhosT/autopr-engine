"""
AI Linting Fixer Package.

A comprehensive AI-powered linting fixer with modular architecture.
"""

from collections.abc import Callable
from typing import Any

from autopr.actions.ai_linting_fixer.ai_fix_applier import AIFixApplier

# Import all module components for re-export
from autopr.actions.ai_linting_fixer.detection import IssueDetector
from autopr.actions.ai_linting_fixer.display import (
    DisplayConfig,
    DisplayFormatter,
    ErrorDisplay,
    OutputMode,
)
from autopr.actions.ai_linting_fixer.error_handler import (
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorInfo,
    ErrorRecoveryStrategy,
    ErrorSeverity,
    create_error_context,
    get_default_error_handler,
)
from autopr.actions.ai_linting_fixer.file_manager import FileManager
from autopr.actions.ai_linting_fixer.file_persistence import FilePersistenceManager
from autopr.actions.ai_linting_fixer.fix_strategy import (
    BasicFixStrategy,
    FixStrategy,
    StrategySelector,
    ValidationStrategy,
)
from autopr.actions.ai_linting_fixer.issue_fixer import IssueFixer

# New modular components
from autopr.actions.ai_linting_fixer.llm_client import LLMClient
from autopr.actions.ai_linting_fixer.models import (
    AILintingFixerInputs,
    AILintingFixerOutputs,
    FixAttemptLog,
    LintingFixResult,
    LintingIssue,
    OrchestrationConfig,
    PerformanceMetrics,
    WorkflowContext,
    WorkflowEvent,
    WorkflowResult,
)
from autopr.actions.ai_linting_fixer.orchestration import (
    create_workflow_context,
    detect_available_orchestrators,
    execute_with_orchestration,
    get_orchestration_config,
    validate_orchestration_config,
)
from autopr.actions.ai_linting_fixer.performance_tracker import PerformanceTracker
from autopr.actions.ai_linting_fixer.response_parser import ResponseParser


# Optional CodeAnalyzer (psutil optional dep)
CODE_ANALYZER_AVAILABLE = False
try:
    from autopr.actions.ai_linting_fixer.code_analyzer import CodeAnalyzer as _CodeAnalyzer
    CODE_ANALYZER_AVAILABLE = True
except Exception:
    _CodeAnalyzer = None  # type: ignore[assignment]

# Optional symbols (pre-declared as variables)
AIAgentManager: Any | None = None
AILintingFixer: Any | None = None
create_ai_linting_fixer: Callable[..., Any] | None = None
run_ai_linting_fixer: Callable[..., Any] | None = None

# AI Components (optional imports)
AI_COMPONENTS_AVAILABLE = False
try:
    from autopr.actions.ai_linting_fixer.ai_agent_manager import AIAgentManager as _AIAgentManager

    AIAgentManager = _AIAgentManager
    AI_COMPONENTS_AVAILABLE = True
except ImportError:
    pass

# Main class (optional AI imports)
AI_LINTING_FIXER_AVAILABLE = False
try:
    from autopr.actions.ai_linting_fixer.ai_linting_fixer import AILintingFixer as _AILintingFixer
    from autopr.actions.ai_linting_fixer.ai_linting_fixer import (
        create_ai_linting_fixer as _create_ai_linting_fixer,
    )
    from autopr.actions.ai_linting_fixer.ai_linting_fixer import (
        run_ai_linting_fixer as _run_ai_linting_fixer,
    )

    AILintingFixer = _AILintingFixer
    create_ai_linting_fixer = _create_ai_linting_fixer
    run_ai_linting_fixer = _run_ai_linting_fixer
    AI_LINTING_FIXER_AVAILABLE = True
except ImportError:
    pass

# Define __all__ directly - we'll modify it later
__all__ = [
    # Main components
    "AIAgentManager",
    "AILintingFixer",
    "AILintingFixerInputs",
    "AILintingFixerOutputs",
    "CodeAnalyzer",
    "create_ai_linting_fixer",
    "run_ai_linting_fixer",
    # Display components
    "DisplayConfig",
    "DisplayFormatter",
    "ErrorDisplay",
    "OutputMode",
    # Error handling
    "ErrorCategory",
    "ErrorContext",
    "ErrorHandler",
    "ErrorInfo",
    "ErrorRecoveryStrategy",
    "ErrorSeverity",
    "create_error_context",
    "get_default_error_handler",
    # Core components
    "FileManager",
    "FixAttemptLog",
    "IssueDetector",
    "IssueFixer",
    "LintingFixResult",
    "LintingIssue",
    # Orchestration
    "OrchestrationConfig",
    "PerformanceMetrics",
    "WorkflowContext",
    "WorkflowEvent",
    "WorkflowResult",
    "create_workflow_context",
    "detect_available_orchestrators",
    "execute_with_orchestration",
    "get_orchestration_config",
    "validate_orchestration_config",
    # Performance
    "PerformanceTracker",
    # New modular components
    "LLMClient",
    "FilePersistenceManager",
    "ResponseParser",
    "FixStrategy",
    "BasicFixStrategy",
    "ValidationStrategy",
    "StrategySelector",
    "AIFixApplier",
]

# Remove optional components from __all__
_all_set = set(__all__)

if not AI_COMPONENTS_AVAILABLE:
    _all_set.discard("AIAgentManager")

if not AI_LINTING_FIXER_AVAILABLE:
    _all_set.discard("AILintingFixer")
    _all_set.discard("create_ai_linting_fixer")
    _all_set.discard("run_ai_linting_fixer")

if not CODE_ANALYZER_AVAILABLE:
    _all_set.discard("CodeAnalyzer")

# Rebuild __all__ from the modified set
__all__ = sorted(_all_set)

# Public name binding (if available)
if CODE_ANALYZER_AVAILABLE:
    CodeAnalyzer = _CodeAnalyzer  # type: ignore[misc]
