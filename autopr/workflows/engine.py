"""
AutoPR Workflow Engine

Orchestrates workflow execution and manages workflow lifecycle.
"""

import asyncio
from datetime import datetime
import logging
import time
from typing import Any

from autopr.config import AutoPRConfig
from autopr.exceptions import WorkflowError
from autopr.workflows.base import Workflow


logger = logging.getLogger(__name__)

# Configuration constants
MAX_WORKFLOW_HISTORY = 1000  # Maximum number of workflow executions to keep in history


class WorkflowEngine:
    """
    Workflow execution engine that manages and executes workflows.

    Handles workflow scheduling, execution, monitoring, and lifecycle management.
    """

    def __init__(self, config: AutoPRConfig) -> None:
        """
        Initialize the workflow engine.

        Args:
            config: AutoPR configuration object
        """
        self.config = config
        self.workflows: dict[str, Workflow] = {}
        self.running_workflows: dict[str, asyncio.Task] = {}
        self.workflow_history: list[dict[str, Any]] = []
        self._is_running = False
        
        # Metrics tracking
        self.metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "timeout_executions": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
        }

        logger.info("Workflow engine initialized")

    async def start(self) -> None:
        """Start the workflow engine."""
        self._is_running = True
        logger.info("Workflow engine started")

    async def stop(self) -> None:
        """Stop the workflow engine and cancel running workflows."""
        self._is_running = False

        # Cancel all running workflows
        for workflow_id, task in self.running_workflows.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled workflow {workflow_id}")

        self.running_workflows.clear()
        logger.info("Workflow engine stopped")

    def register_workflow(self, workflow: Workflow) -> None:
        """
        Register a workflow with the engine.

        Args:
            workflow: Workflow instance to register
        """
        self.workflows[workflow.name] = workflow
        logger.info(f"Registered workflow: {workflow.name}")

    def unregister_workflow(self, workflow_name: str) -> None:
        """
        Unregister a workflow from the engine.

        Args:
            workflow_name: Name of workflow to unregister
        """
        if workflow_name in self.workflows:
            del self.workflows[workflow_name]
            logger.info(f"Unregistered workflow: {workflow_name}")

    async def execute_workflow(
        self,
        workflow_name: str,
        context: dict[str, Any],
        workflow_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a workflow by name with retry logic.

        Args:
            workflow_name: Name of workflow to execute
            context: Execution context data
            workflow_id: Optional workflow execution ID

        Returns:
            Workflow execution result
        """
        if not self._is_running:
            msg = "Workflow engine is not running"
            raise WorkflowError(msg, workflow_name)

        if workflow_name not in self.workflows:
            msg = f"Workflow '{workflow_name}' not found"
            raise WorkflowError(msg, workflow_name)

        workflow = self.workflows[workflow_name]
        execution_id = workflow_id or f"{workflow_name}_{datetime.now().isoformat()}"
        
        # Retry logic with exponential backoff
        max_attempts = getattr(self.config, 'workflow_retry_attempts', 3)
        base_delay = getattr(self.config, 'workflow_retry_delay', 5)
        
        last_exception = None
        
        for attempt in range(max_attempts):
            start_time = time.time()
            
            try:
                if attempt > 0:
                    # Exponential backoff: delay * (2 ^ attempt)
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying workflow {execution_id} after {delay}s (attempt {attempt + 1}/{max_attempts})")
                    await asyncio.sleep(delay)
                
                logger.info("Starting workflow execution: %s (attempt %d/%d)", execution_id, attempt + 1, max_attempts)

                # Create execution task
                task = asyncio.create_task(
                    self._execute_workflow_task(workflow, context, execution_id)
                )

                # Track running workflow
                self.running_workflows[execution_id] = task

                # Wait for completion with timeout
                result = await asyncio.wait_for(task, timeout=self.config.workflow_timeout)

                # Update metrics
                execution_time = time.time() - start_time
                self._update_metrics("success", execution_time)

                # Record successful execution
                self._record_execution(execution_id, workflow_name, "completed", result)

                logger.info(f"Workflow execution completed: {execution_id}")
                return result

            except TimeoutError as e:
                last_exception = e
                execution_time = time.time() - start_time
                
                if attempt == max_attempts - 1:
                    # Final attempt failed
                    error_msg = f"Workflow execution timed out after {max_attempts} attempts: {execution_id}"
                    logger.exception("Workflow execution timed out: %s", execution_id)
                    
                    # Update metrics
                    self._update_metrics("timeout", execution_time)
                    
                    self._record_execution(
                        execution_id, workflow_name, "timeout", {"error": error_msg}
                    )
                    raise WorkflowError(error_msg, workflow_name)
                else:
                    logger.warning(f"Workflow execution timed out on attempt {attempt + 1}, will retry: {execution_id}")

            except Exception as e:
                last_exception = e
                execution_time = time.time() - start_time
                
                if attempt == max_attempts - 1:
                    # Final attempt failed
                    error_msg = f"Workflow execution failed after {max_attempts} attempts: {e}"
                    logger.exception("Workflow execution failed: %s - %s", execution_id, e)
                    
                    # Update metrics
                    self._update_metrics("failed", execution_time)
                    
                    self._record_execution(
                        execution_id, workflow_name, "failed", {"error": str(e)}
                    )
                    raise WorkflowError(error_msg, workflow_name)
                else:
                    logger.warning(f"Workflow execution failed on attempt {attempt + 1}, will retry: {execution_id} - {e}")

            finally:
                # Clean up running workflow tracking
                if execution_id in self.running_workflows:
                    del self.running_workflows[execution_id]
        
        # This should never be reached, but just in case
        if last_exception:
            raise WorkflowError(f"Workflow execution failed: {last_exception}", workflow_name)
        
        msg = f"Workflow execution failed for unknown reason: {execution_id}"
        raise WorkflowError(msg, workflow_name)

    async def _execute_workflow_task(
        self, workflow: Workflow, context: dict[str, Any], execution_id: str
    ) -> dict[str, Any]:
        """
        Internal method to execute workflow task.

        Args:
            workflow: Workflow instance to execute
            context: Execution context
            execution_id: Unique execution identifier

        Returns:
            Workflow execution result
        """
        try:
            # Validate workflow inputs
            await workflow.validate_inputs(context)

            # Execute workflow
            result = await workflow.execute(context)

            # Validate workflow outputs
            await workflow.validate_outputs(result)

            return result

        except Exception as e:
            logger.exception("Workflow task execution failed: %s - %s", execution_id, e)
            raise

    async def process_event(
        self, event_type: str, event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process an event and trigger appropriate workflows.

        Args:
            event_type: Type of event
            event_data: Event payload

        Returns:
            Processing result
        """
        results = []

        # Find workflows that handle this event type
        for workflow_name, workflow in self.workflows.items():
            if workflow.handles_event(event_type):
                try:
                    result = await self.execute_workflow(
                        workflow_name,
                        {"event_type": event_type, "event_data": event_data},
                    )
                    results.append(
                        {
                            "workflow": workflow_name,
                            "status": "success",
                            "result": result,
                        }
                    )
                except Exception as e:
                    logger.exception(
                        "Failed to execute workflow %s for event %s: %s",
                        workflow_name,
                        event_type,
                        e,
                    )
                    results.append(
                        {"workflow": workflow_name, "status": "error", "error": str(e)}
                    )

        return {
            "event_type": event_type,
            "processed_workflows": len(results),
            "results": results,
        }

    def _record_execution(
        self, execution_id: str, workflow_name: str, status: str, result: dict[str, Any]
    ) -> None:
        """Record workflow execution in history."""
        self.workflow_history.append(
            {
                "execution_id": execution_id,
                "workflow_name": workflow_name,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "result": result,
            }
        )

        # Keep only last MAX_WORKFLOW_HISTORY executions
        if len(self.workflow_history) > MAX_WORKFLOW_HISTORY:
            self.workflow_history = self.workflow_history[-MAX_WORKFLOW_HISTORY:]

    def _update_metrics(self, status: str, execution_time: float) -> None:
        """
        Update workflow execution metrics.
        
        Args:
            status: Execution status (success, failed, timeout)
            execution_time: Time taken for execution in seconds
        """
        self.metrics["total_executions"] += 1
        self.metrics["total_execution_time"] += execution_time
        
        if status == "success":
            self.metrics["successful_executions"] += 1
        elif status == "failed":
            self.metrics["failed_executions"] += 1
        elif status == "timeout":
            self.metrics["timeout_executions"] += 1
        
        # Update average execution time
        if self.metrics["total_executions"] > 0:
            self.metrics["average_execution_time"] = (
                self.metrics["total_execution_time"] / self.metrics["total_executions"]
            )

    def get_status(self) -> dict[str, Any]:
        """Get workflow engine status."""
        return {
            "running": self._is_running,
            "registered_workflows": len(self.workflows),
            "running_workflows": len(self.running_workflows),
            "total_executions": len(self.workflow_history),
            "workflows": list(self.workflows.keys()),
            "metrics": self.metrics,
        }

    def get_metrics(self) -> dict[str, Any]:
        """
        Get workflow execution metrics.
        
        Returns:
            Dictionary containing execution metrics
        """
        success_rate = 0.0
        if self.metrics["total_executions"] > 0:
            success_rate = (
                self.metrics["successful_executions"] / self.metrics["total_executions"]
            ) * 100
        
        return {
            **self.metrics,
            "success_rate_percent": round(success_rate, 2),
        }

    def get_workflow_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get workflow execution history."""
        return self.workflow_history[-limit:]

    def get_running_workflows(self) -> list[str]:
        """Get list of currently running workflow execution IDs."""
        return list(self.running_workflows.keys())
