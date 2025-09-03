"""
AI Linting Fixer Package

This package provides AI-powered linting fixes with a clean, modular architecture.
"""

from .core import AILintingFixer
from .display import display_provider_status, print_feature_status
from .main import ai_linting_fixer
from .models import AILintingFixerInputs, AILintingFixerOutputs, LintingIssue, create_empty_outputs
from .workflow_orchestrator import WorkflowOrchestrator, orchestrate_ai_linting_workflow


__all__ = [
    # Core classes
    "AILintingFixer",
    "WorkflowOrchestrator",

    # Main functions
    "ai_linting_fixer",
    "orchestrate_ai_linting_workflow",

    # Models
    "AILintingFixerInputs",
    "AILintingFixerOutputs",
    "LintingIssue",
    "create_empty_outputs",

    # Legacy compatibility
    "print_feature_status",
    "display_provider_status",
]
