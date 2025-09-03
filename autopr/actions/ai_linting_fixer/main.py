"""
Main AI Linting Fixer Module (Refactored)

This is the clean entry point that imports and uses the refactored
modular components for AI-powered linting fixes.
"""

from autopr.actions.ai_linting_fixer.display import display_provider_status, print_feature_status
from autopr.actions.ai_linting_fixer.models import AILintingFixerInputs, AILintingFixerOutputs
from autopr.actions.ai_linting_fixer.workflow_orchestrator import orchestrate_ai_linting_workflow


# Legacy compatibility exports
__all__ = [
    "ai_linting_fixer",
    "print_feature_status",
    "display_provider_status",
]


# =============================================================================
# MAIN FUNCTION (Clean Entry Point)
# =============================================================================


async def ai_linting_fixer(inputs: AILintingFixerInputs) -> AILintingFixerOutputs:
    """
    Main AI linting function - clean entry point using refactored modules.

    This function now delegates to the WorkflowOrchestrator for clean
    separation of concerns and maintainability.
    """
    return await orchestrate_ai_linting_workflow(inputs)
