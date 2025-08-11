"""
AutoPR Workflow Base Classes

Base classes and interfaces for workflow implementation.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any

logger = logging.getLogger(__name__)


class Workflow(ABC):
    """
    Base class for all AutoPR workflows.

    Workflows define automated processes that can be triggered by events
    or executed manually. Each workflow has inputs, outputs, and execution logic.
    """

    def __init__(self, name: str, description: str = "", version: str = "1.0.0") -> None:
        """
        Initialize the workflow.

        Args:
            name: Unique workflow name
            description: Human-readable description
            version: Workflow version
        """
        self.name = name
        self.description = description
        self.version = version
        self.supported_events: list[str] = []

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the workflow with given context.

        Args:
            context: Execution context containing inputs and environment data

        Returns:
            Workflow execution result
        """

    async def validate_inputs(self, context: dict[str, Any]) -> None:
        """
        Validate workflow inputs.

        Args:
            context: Execution context to validate

        Raises:
            ValidationError: If inputs are invalid
        """
        # Default implementation - can be overridden

    async def validate_outputs(self, result: dict[str, Any]) -> None:
        """
        Validate workflow outputs.

        Args:
            result: Workflow execution result to validate

        Raises:
            ValidationError: If outputs are invalid
        """
        # Default implementation - can be overridden

    def handles_event(self, event_type: str) -> bool:
        """
        Check if this workflow handles the given event type.

        Args:
            event_type: Event type to check

        Returns:
            True if workflow handles this event type
        """
        return event_type in self.supported_events

    def add_supported_event(self, event_type: str) -> None:
        """
        Add a supported event type to this workflow.

        Args:
            event_type: Event type to add
        """
        if event_type not in self.supported_events:
            self.supported_events.append(event_type)

    def get_metadata(self) -> dict[str, Any]:
        """
        Get workflow metadata.

        Returns:
            Dictionary containing workflow metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "supported_events": self.supported_events,
        }

    def __str__(self) -> str:
        return f"Workflow(name='{self.name}', version='{self.version}')"

    def __repr__(self) -> str:
        return self.__str__()


class YAMLWorkflow(Workflow):
    """
    Workflow implementation that loads configuration from YAML files.

    This class provides a way to define workflows declaratively using YAML
    configuration files instead of writing Python code.
    """

    def __init__(self, name: str, yaml_config: dict[str, Any]) -> None:
        """
        Initialize YAML-based workflow.

        Args:
            name: Workflow name
            yaml_config: YAML configuration dictionary
        """
        description = yaml_config.get("description", "")
        version = yaml_config.get("version", "1.0.0")

        super().__init__(name, description, version)

        self.config = yaml_config
        self.supported_events = yaml_config.get("triggers", {}).get("events", [])
        self.steps = yaml_config.get("steps", [])

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute YAML-defined workflow steps.

        Args:
            context: Execution context

        Returns:
            Workflow execution result
        """
        results = []
        workflow_context = context.copy()

        logger.info(f"Executing YAML workflow: {self.name}")

        for i, step in enumerate(self.steps):
            step_name = step.get("name", f"step_{i}")
            step_type = step.get("type", "unknown")

            logger.info(f"Executing step: {step_name} (type: {step_type})")

            try:
                step_result = await self._execute_step(step, workflow_context)
                results.append(
                    {
                        "step": step_name,
                        "type": step_type,
                        "status": "success",
                        "result": step_result,
                    }
                )

                # Update context with step results
                if isinstance(step_result, dict):
                    workflow_context.update(step_result)

            except Exception as e:
                logger.exception(f"Step {step_name} failed: {e}")
                results.append(
                    {"step": step_name, "type": step_type, "status": "error", "error": str(e)}
                )

                # Check if workflow should continue on error
                if not step.get("continue_on_error", False):
                    break

        return {
            "workflow": self.name,
            "steps_executed": len(results),
            "steps": results,
            "final_context": workflow_context,
        }

    async def _execute_step(self, step: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a single workflow step.

        Args:
            step: Step configuration
            context: Current workflow context

        Returns:
            Step execution result
        """
        step_type = step.get("type")

        if step_type == "action":
            return await self._execute_action_step(step, context)
        if step_type == "condition":
            return await self._execute_condition_step(step, context)
        if step_type == "parallel":
            return await self._execute_parallel_step(step, context)
        if step_type == "delay":
            return await self._execute_delay_step(step, context)
        # For now, return a placeholder result
        return {"message": f"Step type '{step_type}' not implemented yet"}

    async def _execute_action_step(
        self, step: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute an action step."""
        action_name = step.get("action")
        action_inputs = step.get("inputs", {})

        # TODO: Integrate with action registry to execute actual actions
        return {
            "action": action_name,
            "inputs": action_inputs,
            "message": f"Action '{action_name}' executed (placeholder)",
        }

    async def _execute_condition_step(
        self, step: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a conditional step."""
        condition = step.get("condition")

        # TODO: Implement condition evaluation
        return {
            "condition": condition,
            "result": True,
            "message": "Condition evaluated (placeholder)",
        }

    async def _execute_parallel_step(
        self, step: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute parallel steps."""
        parallel_steps = step.get("steps", [])

        # TODO: Implement parallel execution
        return {
            "parallel_steps": len(parallel_steps),
            "message": "Parallel steps executed (placeholder)",
        }

    async def _execute_delay_step(
        self, step: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a delay step."""
        import asyncio

        delay_seconds = step.get("seconds", 1)
        await asyncio.sleep(delay_seconds)

        return {"delay_seconds": delay_seconds, "message": f"Delayed for {delay_seconds} seconds"}
