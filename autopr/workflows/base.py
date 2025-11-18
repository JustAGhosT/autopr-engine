"""
AutoPR Workflow Base Classes

Base classes and interfaces for workflow implementation.
"""

from abc import ABC, abstractmethod
import asyncio
import logging
from typing import Any


logger = logging.getLogger(__name__)


class Workflow(ABC):
    """
    Base class for all AutoPR workflows.

    Workflows define automated processes that can be triggered by events
    or executed manually. Each workflow has inputs, outputs, and execution logic.
    """

    def __init__(
        self, name: str, description: str = "", version: str = "1.0.0"
    ) -> None:
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
        return

    async def validate_outputs(self, result: dict[str, Any]) -> None:
        """
        Validate workflow outputs.

        Args:
            result: Workflow execution result to validate

        Raises:
            ValidationError: If outputs are invalid
        """
        # Default implementation - can be overridden
        return

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

        logger.info("Executing YAML workflow: %s", self.name)

        for i, step in enumerate(self.steps):
            step_name = step.get("name", f"step_{i}")
            step_type = step.get("type", "unknown")

            logger.info("Executing step: %s (type: %s)", step_name, step_type)

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

            except Exception as err:
                logger.exception("Step %s failed", step_name)
                results.append(
                    {
                        "step": step_name,
                        "type": step_type,
                        "status": "error",
                        "error": str(err),
                    }
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

    async def _execute_step(
        self, step: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
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
        self, step: dict[str, Any], _context: dict[str, Any]
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

        # Implement condition evaluation
        result = False
        error_msg = None
        
        try:
            if not condition:
                result = False
                error_msg = "No condition specified"
            elif isinstance(condition, bool):
                result = condition
            elif isinstance(condition, str):
                # Simple condition evaluation using context variables
                # Support basic comparisons: var == value, var != value, var in list, etc.
                result = self._evaluate_string_condition(condition, context)
            elif isinstance(condition, dict):
                # Support complex conditions with operators
                result = self._evaluate_dict_condition(condition, context)
            else:
                result = bool(condition)
        except Exception as e:
            logger.warning(f"Error evaluating condition: {e}")
            error_msg = str(e)
            result = False

        return {
            "condition": condition,
            "result": result,
            "message": f"Condition evaluated to {result}" + (f" (error: {error_msg})" if error_msg else ""),
        }
    
    def _evaluate_string_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """Evaluate a string-based condition."""
        # Simple variable substitution and evaluation
        for key, value in context.items():
            condition = condition.replace(f"{{{key}}}", repr(value))
        
        # Safe evaluation of basic boolean expressions
        try:
            # Only allow specific safe operations
            allowed_names = {"True": True, "False": False, "None": None}
            return bool(eval(condition, {"__builtins__": {}}, allowed_names))
        except Exception:
            return False
    
    def _evaluate_dict_condition(self, condition: dict[str, Any], context: dict[str, Any]) -> bool:
        """Evaluate a dictionary-based condition with operators."""
        operator = condition.get("op", "eq")
        left = condition.get("left")
        right = condition.get("right")
        
        # Resolve variables from context
        if isinstance(left, str) and left.startswith("$"):
            left = context.get(left[1:], None)
        if isinstance(right, str) and right.startswith("$"):
            right = context.get(right[1:], None)
        
        # Evaluate based on operator
        if operator == "eq":
            return left == right
        elif operator == "ne":
            return left != right
        elif operator == "gt":
            return left > right
        elif operator == "lt":
            return left < right
        elif operator == "gte":
            return left >= right
        elif operator == "lte":
            return left <= right
        elif operator == "in":
            return left in right
        elif operator == "not_in":
            return left not in right
        elif operator == "contains":
            return right in left
        else:
            return False

    async def _execute_parallel_step(
        self, step: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute parallel steps."""
        parallel_steps = step.get("steps", [])

        # Implement parallel execution using asyncio.gather
        results = []
        errors = []
        
        try:
            # Create tasks for all parallel steps
            tasks = [self._execute_step(s, context) for s in parallel_steps]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Separate successful results from errors
            successful_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    errors.append({
                        "step_index": i,
                        "error": str(result),
                    })
                else:
                    successful_results.append(result)
            
            results = successful_results
            
        except Exception as e:
            logger.exception(f"Error executing parallel steps: {e}")
            errors.append({"error": str(e)})

        return {
            "parallel_steps": len(parallel_steps),
            "completed": len(results),
            "errors": len(errors),
            "results": results,
            "error_details": errors if errors else None,
            "message": f"Executed {len(results)}/{len(parallel_steps)} parallel steps" 
                      + (f" with {len(errors)} errors" if errors else ""),
        }

    async def _execute_delay_step(
        self, step: dict[str, Any], _context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a delay step."""

        delay_seconds = step.get("seconds", 1)
        await asyncio.sleep(delay_seconds)

        return {
            "delay_seconds": delay_seconds,
            "message": f"Delayed for {delay_seconds} seconds",
        }
