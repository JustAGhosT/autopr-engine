"""
AI Linting Fixer Package.

A comprehensive AI-powered linting fixer with modular architecture.
"""

# AI Components (optional imports)
try:
    from .ai_agent_manager import AIAgentManager

    AI_COMPONENTS_AVAILABLE = True
except ImportError:
    AIAgentManager = None  # type: ignore
    AI_COMPONENTS_AVAILABLE = False

# Main class (optional AI imports)
try:
    from .ai_linting_fixer import AILintingFixer, create_ai_linting_fixer, run_ai_linting_fixer

    AI_LINTING_FIXER_AVAILABLE = True
except ImportError:
    AILintingFixer = None  # type: ignore
    create_ai_linting_fixer = None  # type: ignore
    run_ai_linting_fixer = None  # type: ignore
    AI_LINTING_FIXER_AVAILABLE = False

from .code_analyzer import CodeAnalyzer

# Core components
from .detection import IssueDetector

# Display and error handling
from .display import DisplayConfig, DisplayFormatter, ErrorDisplay, OutputMode
from .error_handler import (
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorInfo,
    ErrorRecoveryStrategy,
    ErrorSeverity,
    create_error_context,
    get_default_error_handler,
)
from .file_manager import FileManager
from .issue_fixer import IssueFixer

# Models
from .models import (
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

# Orchestration
from .orchestration import (
    create_workflow_context,
    detect_available_orchestrators,
    execute_with_orchestration,
    get_orchestration_config,
    validate_orchestration_config,
)
from .performance_tracker import PerformanceTracker

__all__ = [
    "AIAgentManager",
    # Main class
    "AILintingFixer",
    # Models
    "AILintingFixerInputs",
    "AILintingFixerOutputs",
    "CodeAnalyzer",
    # Display and error handling
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
    "IssueFixer",
    # Core components
    "IssueDetector",
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
    # Orchestration
    "detect_available_orchestrators",
    "execute_with_orchestration",
    "get_default_error_handler",
    "get_orchestration_config",
    "run_ai_linting_fixer",
    "validate_orchestration_config",
]

# Remove AI components from __all__ if not available
if not AI_COMPONENTS_AVAILABLE:
    __all__ = [item for item in __all__ if item != "AIAgentManager"]

if not AI_LINTING_FIXER_AVAILABLE:
    __all__ = [
        item
        for item in __all__
        if item not in ["AILintingFixer", "create_ai_linting_fixer", "run_ai_linting_fixer"]
    ]
