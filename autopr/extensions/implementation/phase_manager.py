"""
Phase Manager Module

Handles phase orchestration, workflow management, and progress tracking for implementation roadmap.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .task_definitions import TaskRegistry
from .task_executor import TaskExecution, TaskExecutor

logger = logging.getLogger(__name__)


@dataclass
class PhaseExecution:
    """Represents a phase execution instance."""

    phase_id: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str = "pending"  # pending, running, completed, failed, paused
    task_executions: dict[str, TaskExecution] = field(default_factory=dict)
    progress_percentage: float = 0.0

    @property
    def duration(self) -> timedelta | None:
        """Get phase execution duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def is_completed(self) -> bool:
        """Check if phase completed successfully."""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if phase failed."""
        return self.status == "failed"

    def update_progress(self) -> None:
        """Update progress percentage based on task completion."""
        if not self.task_executions:
            self.progress_percentage = 0.0
            return

        completed_tasks = sum(
            1 for execution in self.task_executions.values() if execution.is_completed
        )
        total_tasks = len(self.task_executions)
        self.progress_percentage = (completed_tasks / total_tasks) * 100.0


class PhaseManager:
    """Manages implementation phases and their execution."""

    def __init__(self, task_executor: TaskExecutor) -> None:
        self.task_executor = task_executor
        self.phase_executions: dict[str, PhaseExecution] = {}
        self.current_phase: str | None = None
        self.phase_definitions = TaskRegistry.get_phase_definitions()

    async def execute_phase(
        self, phase_id: str, dry_run: bool = False, force: bool = False
    ) -> PhaseExecution:
        """Execute a specific phase."""
        if phase_id not in self.phase_definitions:
            msg = f"Unknown phase: {phase_id}"
            raise ValueError(msg)

        # Check dependencies unless forced
        if not force and not await self._check_phase_dependencies(phase_id):
            msg = f"Phase dependencies not satisfied for: {phase_id}"
            raise ValueError(msg)

        # Initialize phase execution
        if phase_id not in self.phase_executions:
            self.phase_executions[phase_id] = PhaseExecution(phase_id=phase_id)

        phase_execution = self.phase_executions[phase_id]
        phase_definition = self.phase_definitions[phase_id]

        try:
            phase_execution.start_time = datetime.now()
            phase_execution.status = "running"
            self.current_phase = phase_id

            logger.info(f"Starting phase: {phase_id}")

            # Get tasks for this phase
            task_ids = phase_definition.get("tasks", [])

            # Execute tasks with dependencies
            task_executions = await self.task_executor.execute_tasks_with_dependencies(
                task_ids, dry_run
            )

            # Update phase execution with task results
            phase_execution.task_executions.update(task_executions)
            phase_execution.update_progress()

            # Determine phase status based on task results
            failed_tasks = [
                task_id for task_id, execution in task_executions.items() if execution.is_failed
            ]

            if failed_tasks:
                phase_execution.status = "failed"
                logger.error(f"Phase {phase_id} failed due to failed tasks: {failed_tasks}")
            else:
                phase_execution.status = "completed"
                logger.info(f"Phase {phase_id} completed successfully")

            phase_execution.end_time = datetime.now()

        except Exception as e:
            phase_execution.end_time = datetime.now()
            phase_execution.status = "failed"
            logger.exception(f"Phase {phase_id} failed with exception: {e}")
            raise

        return phase_execution

    async def execute_all_phases(
        self, dry_run: bool = False, stop_on_failure: bool = True
    ) -> dict[str, PhaseExecution]:
        """Execute all phases in order."""
        # Get phases sorted by priority
        phases = sorted(self.phase_definitions.items(), key=lambda x: x[1].get("priority", 999))

        for phase_id, _phase_definition in phases:
            try:
                await self.execute_phase(phase_id, dry_run)

                if self.phase_executions[phase_id].is_failed and stop_on_failure:
                    logger.error(f"Stopping execution due to failed phase: {phase_id}")
                    break

            except Exception as e:
                logger.exception(f"Failed to execute phase {phase_id}: {e}")
                if stop_on_failure:
                    break

        return self.phase_executions

    async def _check_phase_dependencies(self, phase_id: str) -> bool:
        """Check if phase dependencies are satisfied."""
        phase_definition = self.phase_definitions[phase_id]
        dependencies = phase_definition.get("depends_on", [])

        for dep_phase_id in dependencies:
            if dep_phase_id not in self.phase_executions:
                logger.warning(f"Dependency phase {dep_phase_id} not executed")
                return False

            if not self.phase_executions[dep_phase_id].is_completed:
                logger.warning(f"Dependency phase {dep_phase_id} not completed")
                return False

        return True

    def get_phase_status(self, phase_id: str) -> dict[str, Any]:
        """Get detailed status of a specific phase."""
        if phase_id not in self.phase_executions:
            return {"phase_id": phase_id, "status": "not_started", "progress_percentage": 0.0}

        execution = self.phase_executions[phase_id]
        phase_definition = self.phase_definitions[phase_id]

        return {
            "phase_id": phase_id,
            "name": phase_definition.get("name", phase_id),
            "description": phase_definition.get("description", ""),
            "status": execution.status,
            "progress_percentage": execution.progress_percentage,
            "start_time": execution.start_time.isoformat() if execution.start_time else None,
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "duration_seconds": execution.duration.total_seconds() if execution.duration else None,
            "total_tasks": len(phase_definition.get("tasks", [])),
            "completed_tasks": sum(1 for e in execution.task_executions.values() if e.is_completed),
            "failed_tasks": sum(1 for e in execution.task_executions.values() if e.is_failed),
            "task_status": {
                task_id: {
                    "status": task_execution.status,
                    "duration_seconds": (
                        task_execution.duration.total_seconds() if task_execution.duration else None
                    ),
                    "error": task_execution.error_message,
                }
                for task_id, task_execution in execution.task_executions.items()
            },
        }

    def get_overall_status(self) -> dict[str, Any]:
        """Get overall implementation status across all phases."""
        total_phases = len(self.phase_definitions)
        completed_phases = sum(
            1 for execution in self.phase_executions.values() if execution.is_completed
        )
        failed_phases = sum(
            1 for execution in self.phase_executions.values() if execution.is_failed
        )

        # Calculate overall progress
        if total_phases == 0:
            overall_progress = 0.0
        else:
            phase_weights = {"immediate": 0.4, "medium": 0.4, "strategic": 0.2}

            weighted_progress = 0.0
            total_weight = 0.0

            for phase_id, execution in self.phase_executions.items():
                weight = phase_weights.get(phase_id, 1.0 / total_phases)
                weighted_progress += execution.progress_percentage * weight
                total_weight += weight

            overall_progress = weighted_progress / total_weight if total_weight > 0 else 0.0

        # Determine overall status
        if failed_phases > 0:
            overall_status = "failed"
        elif completed_phases == total_phases:
            overall_status = "completed"
        elif any(e.status == "running" for e in self.phase_executions.values()):
            overall_status = "running"
        else:
            overall_status = "pending"

        return {
            "overall_status": overall_status,
            "overall_progress_percentage": overall_progress,
            "current_phase": self.current_phase,
            "total_phases": total_phases,
            "completed_phases": completed_phases,
            "failed_phases": failed_phases,
            "phases": {
                phase_id: self.get_phase_status(phase_id) for phase_id in self.phase_definitions
            },
        }

    def get_next_steps(self) -> list[dict[str, Any]]:
        """Get recommended next steps based on current progress."""
        next_steps = []

        # Find the next phase to execute
        for phase_id in ["immediate", "medium", "strategic"]:
            if phase_id not in self.phase_executions:
                phase_definition = self.phase_definitions[phase_id]
                next_steps.append(
                    {
                        "type": "phase",
                        "action": f"Execute {phase_definition.get('name', phase_id)}",
                        "description": phase_definition.get("description", ""),
                        "priority": "high" if phase_id == "immediate" else "medium",
                        "estimated_duration_days": phase_definition.get("duration_days", 0),
                    }
                )
                break
            if not self.phase_executions[phase_id].is_completed:
                # Find failed tasks in current phase
                execution = self.phase_executions[phase_id]
                failed_tasks = [
                    task_id
                    for task_id, task_execution in execution.task_executions.items()
                    if task_execution.is_failed
                ]

                if failed_tasks:
                    next_steps.append(
                        {
                            "type": "retry",
                            "action": f"Retry failed tasks in {phase_id}",
                            "description": f"Retry tasks: {', '.join(failed_tasks)}",
                            "priority": "high",
                            "tasks": failed_tasks,
                        }
                    )
                break

        # Add general recommendations
        if not next_steps:
            next_steps.append(
                {
                    "type": "maintenance",
                    "action": "Monitor and maintain implemented features",
                    "description": "All phases completed. Focus on monitoring and optimization.",
                    "priority": "low",
                }
            )

        return next_steps

    def pause_phase(self, phase_id: str) -> bool:
        """Pause execution of a specific phase."""
        if phase_id in self.phase_executions:
            execution = self.phase_executions[phase_id]
            if execution.status == "running":
                execution.status = "paused"
                logger.info(f"Phase {phase_id} paused")
                return True
        return False

    def resume_phase(self, phase_id: str) -> bool:
        """Resume execution of a paused phase."""
        if phase_id in self.phase_executions:
            execution = self.phase_executions[phase_id]
            if execution.status == "paused":
                execution.status = "running"
                logger.info(f"Phase {phase_id} resumed")
                return True
        return False

    def reset_phase(self, phase_id: str) -> bool:
        """Reset a phase to allow re-execution."""
        if phase_id in self.phase_executions:
            del self.phase_executions[phase_id]
            logger.info(f"Phase {phase_id} reset")
            return True
        return False
