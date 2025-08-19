"""
Main Implementation Orchestrator

Provides the same interface as the original Phase1ExtensionImplementor while using modular components.
"""

import logging
from pathlib import Path
from typing import Any

from implementation.phase_manager import PhaseManager
from implementation.report_generator import ReportGenerator
from implementation.task_definitions import Task, TaskRegistry
from implementation.task_executor import TaskExecutor


logger = logging.getLogger(__name__)


class Phase1ExtensionImplementor:
    """
    Modular implementation orchestrator that maintains backward compatibility
    with the original Phase1ExtensionImplementor interface.
    """

    def __init__(self) -> None:
        self.project_root = Path.cwd()
        self.implementation_log: list[dict[str, Any]] = []
        self.current_phase: str | None = None
        self.tasks: dict[str, Task] = {}

        # Initialize modular components
        self.task_executor = TaskExecutor(self.project_root)
        self.phase_manager = PhaseManager(self.task_executor)
        self.report_generator = ReportGenerator(
            self.phase_manager, self.task_executor, self.project_root
        )

        # Maintain backward compatibility with original interface
        self.implementation_phases = TaskRegistry.get_phase_definitions()
        self._initialize_tasks()

    def _initialize_tasks(self) -> None:
        """Initialize task objects from task definitions."""
        task_definitions = TaskRegistry.get_task_definitions()

        for task_id, task_info in task_definitions.items():
            self.tasks[task_id] = Task(
                id=task_id,
                description=task_info.get("description", ""),
                dependencies=task_info.get("dependencies", []),
                metadata=task_info,
            )

    async def run_implementation(
        self, phase: str = "immediate", dry_run: bool = False
    ) -> None:
        """
        Run implementation for a specific phase.
        Maintains backward compatibility with original method signature.
        """
        try:
            self.current_phase = phase
            logger.info(f"Starting implementation phase: {phase}")

            # Log start of implementation
            self._log_implementation_event(
                {
                    "event": "phase_start",
                    "phase": phase,
                    "dry_run": dry_run,
                    "timestamp": self._get_timestamp(),
                }
            )

            # Execute the phase using the modular phase manager
            phase_execution = await self.phase_manager.execute_phase(
                phase_id=phase, dry_run=dry_run
            )

            # Update current phase based on execution result
            if phase_execution.is_completed:
                logger.info(f"Phase {phase} completed successfully")
                self._log_implementation_event(
                    {
                        "event": "phase_completed",
                        "phase": phase,
                        "duration_seconds": (
                            phase_execution.duration.total_seconds()
                            if phase_execution.duration
                            else 0
                        ),
                        "timestamp": self._get_timestamp(),
                    }
                )
            else:
                logger.error(f"Phase {phase} failed")
                self._log_implementation_event(
                    {
                        "event": "phase_failed",
                        "phase": phase,
                        "timestamp": self._get_timestamp(),
                    }
                )

        except Exception as e:
            logger.exception(f"Implementation failed for phase {phase}: {e}")
            self._log_implementation_event(
                {
                    "event": "phase_error",
                    "phase": phase,
                    "error": str(e),
                    "timestamp": self._get_timestamp(),
                }
            )
            raise

    async def run_all_phases(self, dry_run: bool = False) -> None:
        """Run all implementation phases in order."""
        try:
            logger.info("Starting all implementation phases")

            self._log_implementation_event(
                {
                    "event": "full_implementation_start",
                    "dry_run": dry_run,
                    "timestamp": self._get_timestamp(),
                }
            )

            # Execute all phases using the phase manager
            phase_executions = await self.phase_manager.execute_all_phases(
                dry_run=dry_run, stop_on_failure=True
            )

            # Log completion
            completed_phases = sum(
                1 for e in phase_executions.values() if e.is_completed
            )
            failed_phases = sum(1 for e in phase_executions.values() if e.is_failed)

            self._log_implementation_event(
                {
                    "event": "full_implementation_completed",
                    "completed_phases": completed_phases,
                    "failed_phases": failed_phases,
                    "timestamp": self._get_timestamp(),
                }
            )

            logger.info(
                f"Implementation completed: {completed_phases} phases successful, {failed_phases} failed"
            )

        except Exception as e:
            logger.exception(f"Full implementation failed: {e}")
            self._log_implementation_event(
                {
                    "event": "full_implementation_error",
                    "error": str(e),
                    "timestamp": self._get_timestamp(),
                }
            )
            raise

    def get_implementation_status(self) -> dict[str, Any]:
        """Get current implementation status."""
        overall_status = self.phase_manager.get_overall_status()
        execution_summary = self.task_executor.get_execution_summary()

        return {
            "current_phase": self.current_phase,
            "overall_progress": overall_status.get("overall_progress_percentage", 0),
            "phases": overall_status.get("phases", {}),
            "tasks": execution_summary.get("executions", {}),
            "implementation_log": self.implementation_log[-10:],  # Last 10 events
            "next_steps": self.phase_manager.get_next_steps(),
        }

    def generate_implementation_report(self) -> dict[str, Any]:
        """Generate comprehensive implementation report."""
        return self.report_generator.generate_progress_report()

    def save_implementation_report(self, filename: str | None = None) -> Path:
        """Save implementation report to file."""
        report = self.generate_implementation_report()
        return self.report_generator.save_report(report, filename)

    def get_phase_status(self, phase_id: str) -> dict[str, Any]:
        """Get status of a specific phase."""
        return self.phase_manager.get_phase_status(phase_id)

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """Get status of a specific task."""
        if task_id in self.task_executor.executions:
            execution = self.task_executor.executions[task_id]
            return {
                "task_id": task_id,
                "status": execution.status,
                "start_time": (
                    execution.start_time.isoformat() if execution.start_time else None
                ),
                "end_time": (
                    execution.end_time.isoformat() if execution.end_time else None
                ),
                "duration_seconds": (
                    execution.duration.total_seconds() if execution.duration else None
                ),
                "error_message": execution.error_message,
                "output": execution.output,
                "logs": execution.logs,
            }
        return {
            "task_id": task_id,
            "status": "not_started",
            "message": "Task has not been executed yet",
        }

    def pause_implementation(self, phase_id: str | None = None) -> bool:
        """Pause implementation of a specific phase or current phase."""
        target_phase = phase_id or self.current_phase
        if target_phase:
            return self.phase_manager.pause_phase(target_phase)
        return False

    def resume_implementation(self, phase_id: str | None = None) -> bool:
        """Resume implementation of a specific phase or current phase."""
        target_phase = phase_id or self.current_phase
        if target_phase:
            return self.phase_manager.resume_phase(target_phase)
        return False

    def reset_phase(self, phase_id: str) -> bool:
        """Reset a phase to allow re-execution."""
        return self.phase_manager.reset_phase(phase_id)

    def get_available_tasks(self) -> list[dict[str, Any]]:
        """Get list of all available tasks."""
        task_definitions = TaskRegistry.get_task_definitions()
        return [
            {
                "task_id": task_id,
                "name": task_info.get("name", task_id),
                "description": task_info.get("description", ""),
                "category": task_info.get("category", "uncategorized"),
                "complexity": task_info.get("complexity", "unknown"),
                "estimated_time": task_info.get("estimated_time", "unknown"),
                "dependencies": task_info.get("dependencies", []),
            }
            for task_id, task_info in task_definitions.items()
        ]

    def get_available_phases(self) -> list[dict[str, Any]]:
        """Get list of all available phases."""
        return [
            {
                "phase_id": phase_id,
                "name": phase_info.get("name", phase_id),
                "description": phase_info.get("description", ""),
                "priority": phase_info.get("priority", 999),
                "duration_days": phase_info.get("duration_days", 0),
                "tasks": phase_info.get("tasks", []),
                "depends_on": phase_info.get("depends_on", []),
            }
            for phase_id, phase_info in self.implementation_phases.items()
        ]

    def get_dependency_graph(self) -> dict[str, list[str]]:
        """Get the complete task dependency graph."""
        return TaskRegistry.get_dependency_graph()

    def validate_dependencies(self, task_ids: list[str]) -> dict[str, Any]:
        """Validate that task dependencies can be satisfied."""
        dependency_graph = self.get_dependency_graph()
        issues = []

        for task_id in task_ids:
            dependencies = dependency_graph.get(task_id, [])
            missing_deps = [dep for dep in dependencies if dep not in task_ids]

            if missing_deps:
                issues.append(
                    {"task_id": task_id, "missing_dependencies": missing_deps}
                )

        return {"valid": len(issues) == 0, "issues": issues}

    def _get_next_steps(self) -> list[dict[str, Any]]:
        """
        Get recommended next steps based on current progress.
        Maintains backward compatibility with original method.
        """
        return self.phase_manager.get_next_steps()

    def _log_implementation_event(self, event: dict[str, Any]) -> None:
        """Log an implementation event."""
        self.implementation_log.append(event)

        # Keep only the last 100 events to prevent memory bloat
        if len(self.implementation_log) > 100:
            self.implementation_log = self.implementation_log[-100:]

    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime

        return datetime.now().isoformat()

    # Backward compatibility methods

    @property
    def tasks_completed(self) -> int:
        """Get number of completed tasks (backward compatibility)."""
        return sum(1 for e in self.task_executor.executions.values() if e.is_completed)

    @property
    def tasks_failed(self) -> int:
        """Get number of failed tasks (backward compatibility)."""
        return sum(1 for e in self.task_executor.executions.values() if e.is_failed)

    @property
    def implementation_progress(self) -> float:
        """Get overall implementation progress percentage (backward compatibility)."""
        overall_status = self.phase_manager.get_overall_status()
        return (
            overall_status.get("overall_progress_percentage", 0.0)
            if overall_status
            else 0.0
        )

    def get_implementation_summary(self) -> dict[str, Any]:
        """
        Get implementation summary (backward compatibility).
        This method maintains the same interface as the original implementation.
        """
        overall_status = self.phase_manager.get_overall_status()
        execution_summary = self.task_executor.get_execution_summary()

        return {
            "current_phase": self.current_phase,
            "total_phases": overall_status.get("total_phases", 0),
            "completed_phases": overall_status.get("completed_phases", 0),
            "failed_phases": overall_status.get("failed_phases", 0),
            "total_tasks": execution_summary.get("total_tasks", 0),
            "completed_tasks": execution_summary.get("completed", 0),
            "failed_tasks": execution_summary.get("failed", 0),
            "success_rate": execution_summary.get("success_rate", 0.0),
            "overall_progress": overall_status.get("overall_progress_percentage", 0.0),
            "implementation_log": self.implementation_log,
            "next_steps": self._get_next_steps(),
        }

    def get_progress_percentage(self) -> float:
        """Get overall implementation progress percentage (backward compatibility)."""
        overall_status = self.phase_manager.get_overall_status()
        progress = overall_status.get("overall_progress_percentage", 0.0)
        return float(progress) if progress is not None else 0.0
