"""
LLM-specific action class for AutoPR.
"""

from typing import Any

from autopr.actions.base.action import Action


class LLMAction(Action):
    """
    Base class for actions that use LLM providers.

    Provides common functionality for AI-powered actions.
    """

    def __init__(self, name: str, description: str = "", version: str = "1.0.0"):
        super().__init__(name, description, version)
        self.required_permissions.append("llm_access")

    def get_llm_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Extract LLM-specific context information.

        Args:
            context: Full execution context

        Returns:
            LLM context dictionary
        """
        return {
            "llm_provider": context.get("llm_provider"),
            "llm_config": context.get("llm_config"),
            "model_name": context.get("model_name"),
            "temperature": context.get("temperature", 0.7),
            "max_tokens": context.get("max_tokens", 2000),
        }
