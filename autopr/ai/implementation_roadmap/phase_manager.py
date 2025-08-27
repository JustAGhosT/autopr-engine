"""
Phase Manager for Implementation Roadmap
Handles phase orchestration, dependency management, and execution flow
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from implementation_roadmap.task_definitions import (
    ImplementationPhases,
    Phase,
    TaskRegistry,
)
from implementation_roadmap.task_executor import TaskExecution, TaskExecutor


@dataclass
class PhaseExecution:
    """Result of phase execution"""

    phase_name: str
    status: str  # "running", "completed", "failed", "paused"
    start_time: datetime
    end_time: datetime | None = None
    completed_tasks: list[str] = field(default_factory=list)
    failed_tasks: list[str] = field(default_factory=list)
    skipped_tasks: list[str] = field(default_factory=list)
    task_executions: dict[str, TaskExecution] = field(default_factory=dict)
    error_message: str | None = None

    @property
    def duration(self) -> float | None:
        """Get phase execution duration in seconds"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def total_tasks(self) -> int:
        """Get total number of tasks in this phase"""
        return (
            len(self.completed_tasks) + len(self.failed_tasks) + len(self.skipped_tasks)
        )

    @property
    def success_rate(self) -> float:
        """Get success rate for this phase"""
        if self.total_tasks == 0:
            return 0.0
        return len(self.completed_tasks) / self.total_tasks


class PhaseManager:
    """Manages implementation phases and their execution"""

    def __init__(
        self, task_registry: TaskRegistry, task_executor: TaskExecutor
    ) -> None:
        self.task_registry = task_registry
        self.task_executor = task_executor
        self.phases = ImplementationPhases()
        self.phase_executions: dict[str, PhaseExecution] = {}
        self.current_phase: str | None = None
        self._paused = False

    async def execute_phase(
        self, phase_name: str, dry_run: bool = False
    ) -> PhaseExecution:
        """Execute a specific implementation phase"""
        phase = self.phases.get_phase(phase_name)
        if not phase:
            msg = f"Unknown phase: {phase_name}"
            raise ValueError(msg)

        # Check dependencies
        if not await self._check_phase_dependencies(phase):
            msg = f"Phase dependencies not met for: {phase_name}"
            raise ValueError(msg)

        # Initialize phase execution
        execution = PhaseExecution(
            phase_name=phase_name, status="running", start_time=datetime.now()
        )

        self.phase_executions[phase_name] = execution
        self.current_phase = phase_name

        try:
            # Execute tasks in dependency order
            task_order = self._resolve_task_dependencies(phase.tasks)

            for task_name in task_order:
                if self._paused:
                    execution.status = "paused"
                    return execution

                task_execution = await self.task_executor.execute_task(
                    task_name, dry_run
                )
                execution.task_executions[task_name] = task_execution

                if task_execution.status == "success":
                    execution.completed_tasks.append(task_name)
                elif task_execution.status == "error":
                    execution.failed_tasks.append(task_name)
                    # Continue with other tasks unless it's a critical failure
                    if self._is_critical_task(task_name):
                        execution.status = "failed"
                        execution.error_message = f"Critical task failed: {task_name}"
                        break
                else:  # skipped
                    execution.skipped_tasks.append(task_name)

            # Determine final status
            if execution.status == "running":
                if execution.failed_tasks and not execution.completed_tasks:
                    execution.status = "failed"
                elif execution.completed_tasks:
                    execution.status = "completed"
                else:
                    execution.status = "completed"  # All tasks were skipped

        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)

        finally:
            execution.end_time = datetime.now()
            if execution.status != "paused":
                self.current_phase = None

        return execution

    async def execute_all_phases(
        self, dry_run: bool = False
    ) -> dict[str, PhaseExecution]:
        """Execute all phases in dependency order"""
        phase_order = ["immediate", "medium", "strategic"]
        results = {}

        for phase_name in phase_order:
            if self._paused:
                break

            try:
                execution = await self.execute_phase(phase_name, dry_run)
                results[phase_name] = execution

                # Stop if phase failed critically
                if execution.status == "failed" and execution.error_message:
                    break

            except Exception as e:
                # Create failed execution record
                results[phase_name] = PhaseExecution(
                    phase_name=phase_name,
                    status="failed",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_message=str(e),
                )
                break

        return results

    async def _check_phase_dependencies(self, phase: Phase) -> bool:
        """Check if phase dependencies are satisfied"""
        for dep_phase_name in phase.dependencies:
            dep_execution = self.phase_executions.get(dep_phase_name)
            if not dep_execution or dep_execution.status != "completed":
                return False
        return True

    def _resolve_task_dependencies(self, task_names: list[str]) -> list[str]:
        """Resolve task execution order based on dependencies"""
        # Simple topological sort for task dependencies
        visited = set()
        temp_visited = set()
        result = []

        def visit(task_name: str):
            if task_name in temp_visited:
                # Circular dependency detected, ignore for now
                return
            if task_name in visited:
                return

            temp_visited.add(task_name)

            # Visit dependencies first
            task = self.task_registry.get_task(task_name)
            if task:
                for dep in task.dependencies:
                    if (
                        dep in task_names
                    ):  # Only consider dependencies within this phase
                        visit(dep)

            temp_visited.remove(task_name)
            visited.add(task_name)
            result.append(task_name)

        for task_name in task_names:
            if task_name not in visited:
                visit(task_name)

        return result

    def _is_critical_task(self, task_name: str) -> bool:
        """Determine if a task is critical for phase success"""
        # For now, consider all immediate phase tasks as critical
        immediate_phase = self.phases.get_phase("immediate")
        return bool(immediate_phase and task_name in immediate_phase.tasks)

    def pause_execution(self) -> None:
        """Pause phase execution"""
        self._paused = True

    def resume_execution(self) -> None:
        """Resume phase execution"""
        self._paused = False

    def reset_phase(self, phase_name: str) -> None:
        """Reset a phase execution state"""
        if phase_name in self.phase_executions:
            del self.phase_executions[phase_name]

        # Also reset task executions for this phase
        phase = self.phases.get_phase(phase_name)
        if phase:
            for task_name in phase.tasks:
                if task_name in self.task_executor.executions:
                    del self.task_executor.executions[task_name]

    def get_phase_progress(self, phase_name: str) -> dict[str, Any]:
        """Get progress information for a specific phase"""
        execution = self.phase_executions.get(phase_name)
        if not execution:
            return {
                "phase_name": phase_name,
                "status": "not_started",
                "progress_percentage": 0.0,
                "completed_tasks": 0,
                "total_tasks": 0,
            }

        phase = self.phases.get_phase(phase_name)
        total_tasks = len(phase.tasks) if phase else execution.total_tasks

        return {
            "phase_name": phase_name,
            "status": execution.status,
            "progress_percentage": (
                (len(execution.completed_tasks) / total_tasks * 100)
                if total_tasks > 0
                else 0.0
            ),
            "completed_tasks": len(execution.completed_tasks),
            "failed_tasks": len(execution.failed_tasks),
            "skipped_tasks": len(execution.skipped_tasks),
            "total_tasks": total_tasks,
            "success_rate": execution.success_rate,
            "duration": execution.duration,
            "start_time": (
                execution.start_time.isoformat() if execution.start_time else None
            ),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
        }

    def get_overall_progress(self) -> dict[str, Any]:
        """Get overall implementation progress across all phases"""
        all_phases = ["immediate", "medium", "strategic"]
        total_tasks = 0
        completed_tasks = 0
        failed_tasks = 0

        phase_progress = {}
        for phase_name in all_phases:
            progress = self.get_phase_progress(phase_name)
            phase_progress[phase_name] = progress
            total_tasks += progress["total_tasks"]
            completed_tasks += progress["completed_tasks"]
            failed_tasks += progress["failed_tasks"]

        return {
            "overall_progress_percentage": (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
            ),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": (completed_tasks / total_tasks) if total_tasks > 0 else 0.0,
            "current_phase": self.current_phase,
            "is_paused": self._paused,
            "phases": phase_progress,
        }

    def get_next_steps(self) -> list[dict[str, Any]]:
        """Get recommended next steps based on current progress"""
        next_steps = []

        # Check immediate phase
        immediate_progress = self.get_phase_progress("immediate")
        if immediate_progress["status"] == "not_started":
            next_steps.append(
                {
                    "action": "start_immediate_phase",
                    "description": "Start implementing immediate priority tasks",
                    "priority": "high",
                    "estimated_time": "2-4 hours",
                }
            )
        elif immediate_progress["status"] == "running":
            next_steps.append(
                {
                    "action": "continue_immediate_phase",
                    "description": f"Continue immediate phase ({immediate_progress['progress_percentage']:.1f}% complete)",
                    "priority": "high",
                    "estimated_time": "1-2 hours",
                }
            )
        elif immediate_progress["status"] == "completed":
            # Check medium phase
            medium_progress = self.get_phase_progress("medium")
            if medium_progress["status"] == "not_started":
                next_steps.append(
                    {
                        "action": "start_medium_phase",
                        "description": "Start implementing medium priority tasks",
                        "priority": "medium",
                        "estimated_time": "4-8 hours",
                    }
                )

        # Check for failed tasks that need attention
        for phase_name in ["immediate", "medium", "strategic"]:
            execution = self.phase_executions.get(phase_name)
            if execution and execution.failed_tasks:
                next_steps.append(
                    {
                        "action": f"fix_failed_tasks_{phase_name}",
                        "description": f"Fix {len(execution.failed_tasks)} failed tasks in {phase_name} phase",
                        "priority": "high" if phase_name == "immediate" else "medium",
                        "failed_tasks": execution.failed_tasks,
                    }
                )

        # If no specific next steps, suggest strategic planning
        if not next_steps:
            strategic_progress = self.get_phase_progress("strategic")
            if strategic_progress["status"] == "not_started":
                next_steps.append(
                    {
                        "action": "start_strategic_phase",
                        "description": "Begin strategic enhancement implementation",
                        "priority": "low",
                        "estimated_time": "8-16 hours",
                    }
                )

        return next_steps

    def get_phase_summary(self) -> dict[str, Any]:
        """Get comprehensive summary of all phases"""
        summary = {
            "execution_summary": self.get_overall_progress(),
            "phase_details": {},
            "next_steps": self.get_next_steps(),
            "recommendations": [],
        }

        # Add detailed phase information
        for phase_name in ["immediate", "medium", "strategic"]:
            phase = self.phases.get_phase(phase_name)
            execution = self.phase_executions.get(phase_name)

            phase_detail = {
                "name": phase_name,
                "description": phase.description if phase else "",
                "total_tasks": len(phase.tasks) if phase else 0,
                "status": execution.status if execution else "not_started",
                "progress": self.get_phase_progress(phase_name),
            }

            if execution:
                phase_detail.update(
                    {
                        "completed_tasks": execution.completed_tasks,
                        "failed_tasks": execution.failed_tasks,
                        "task_details": {
                            name: {
                                "status": exec.status,
                                "duration": exec.duration,
                                "error": exec.error_message,
                            }
                            for name, exec in execution.task_executions.items()
                        },
                    }
                )

            summary["phase_details"][phase_name] = phase_detail

        # Add recommendations based on current state
        overall_progress = summary["execution_summary"]["overall_progress_percentage"]
        if overall_progress < 25:
            summary["recommendations"].append(
                "Focus on completing immediate priority tasks first for quick wins"
            )
        elif overall_progress < 75:
            summary["recommendations"].append(
                "Consider running medium priority tasks in parallel where possible"
            )
        else:
            summary["recommendations"].append(
                "Excellent progress! Consider strategic enhancements for long-term benefits"
            )

        return summary
