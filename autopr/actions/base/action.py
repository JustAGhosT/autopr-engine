"""
Base Action class for AutoPR.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

# Type variables for generic Action class
TInputs = TypeVar("TInputs")
TOutputs = TypeVar("TOutputs")


class Action(ABC, Generic[TInputs, TOutputs]):
    """
    Base class for all AutoPR actions.

    Actions are discrete units of work that can be executed as part of workflows.
    Each action has a name, description, inputs, and outputs.
    """

    def __init__(self, name: str, description: str = "", version: str = "1.0.0"):
        """
        Initialize the action.

        Args:
            name: Unique action name
            description: Human-readable description
            version: Action version
        """
        self.name = name
        self.description = description
        self.version = version
        self.required_permissions: list[str] = []
        self.supported_platforms: list[str] = ["github"]

    @abstractmethod
    async def execute(self, inputs: TInputs, context: dict[str, Any]) -> TOutputs:
        """
        Execute the action with given inputs.

        Args:
            inputs: Action inputs
            context: Execution context containing environment data

        Returns:
            Action execution result
        """

    async def validate_inputs(self, inputs: TInputs) -> None:
        """
        Validate action inputs.

        Args:
            inputs: Action inputs to validate

        Raises:
            ValidationError: If inputs are invalid
        """
        # Default implementation - can be overridden

    async def validate_outputs(self, outputs: TOutputs) -> None:
        """
        Validate action outputs.

        Args:
            outputs: Action outputs to validate

        Raises:
            ValidationError: If outputs are invalid
        """
        # Default implementation - can be overridden

    async def run(self, inputs: TInputs) -> TOutputs:
        """
        Run the action with given inputs (alternative method name for compatibility).

        Args:
            inputs: Action inputs

        Returns:
            Action execution result
        """
        # Default implementation calls execute with empty context
        return await self.execute(inputs, {})

    def get_input_schema(self) -> dict[str, Any]:
        """
        Get JSON schema for action inputs.

        Returns:
            JSON schema dictionary
        """
        # Default implementation - can be overridden
        return {"type": "object", "properties": {}, "required": []}

    def get_output_schema(self) -> dict[str, Any]:
        """
        Get JSON schema for action outputs.

        Returns:
            JSON schema dictionary
        """
        # Default implementation
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {"type": "object"},
            },
            "required": ["success"],
        }

    def supports_platform(self, platform: str) -> bool:
        """
        Check if this action supports the given platform.

        Args:
            platform: Platform name (e.g., 'github', 'gitlab')

        Returns:
            True if action supports this platform
        """
        return platform in self.supported_platforms

    def requires_permission(self, permission: str) -> bool:
        """
        Check if this action requires a specific permission.

        Args:
            permission: Permission name

        Returns:
            True if action requires this permission
        """
        return permission in self.required_permissions

    def get_metadata(self) -> dict[str, Any]:
        """
        Get action metadata.

        Returns:
            Dictionary containing action metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "required_permissions": self.required_permissions,
            "supported_platforms": self.supported_platforms,
            "input_schema": self.get_input_schema(),
            "output_schema": self.get_output_schema(),
        }

    def __str__(self) -> str:
        return f"Action(name='{self.name}', version='{self.version}')"

    def __repr__(self) -> str:
        return self.__str__()
