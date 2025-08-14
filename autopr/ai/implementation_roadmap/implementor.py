"""
Main Implementation Roadmap Orchestrator
Coordinates all modular components and maintains backward compatibility
"""

from datetime import datetime
import logging
from pathlib import Path
import sys
from typing import Any

from .phase_manager import PhaseManager
from .report_generator import ReportGenerator
from .task_definitions import ImplementationPhases, TaskRegistry
from .task_executor import TaskExecutor

logger = logging.getLogger(__name__)


class Phase1ExtensionImplementor:
    """
    Main orchestrator for Phase 1 extension implementation
    Maintains backward compatibility with the original monolithic implementation
    """

    def __init__(self) -> None:
        """Initialize the modular implementation system"""
        self.task_registry = TaskRegistry()
        self.task_executor = TaskExecutor(self.task_registry)
        self.phase_manager = PhaseManager(self.task_registry, self.task_executor)
        self.report_generator = ReportGenerator(
            self.task_registry, self.task_executor, self.phase_manager
        )

        self.phases = ImplementationPhases()
        self.project_root = Path.cwd()
        self._initialized = True

        logger.info("Phase1ExtensionImplementor initialized with modular architecture")

    # Main execution methods (backward compatible API)

    async def run_implementation(
        self, phase: str = "immediate", dry_run: bool = False
    ) -> dict[str, Any]:
        """
        Run implementation for a specific phase

        Args:
            phase: Phase to run ("immediate", "medium", "strategic", or "all")
            dry_run: If True, only simulate the execution

        Returns:
            Dictionary containing execution results and status
        """
        logger.info(f"Starting implementation for phase: {phase} (dry_run={dry_run})")

        try:
            if phase == "all":
                results = await self.phase_manager.execute_all_phases(dry_run)
                return {
                    "status": "completed",
                    "phase_results": results,
                    "summary": self.get_implementation_status(),
                    "next_steps": self.phase_manager.get_next_steps(),
                }
            result = await self.phase_manager.execute_phase(phase, dry_run)
            return {
                "status": result.status,
                "phase": phase,
                "completed_tasks": result.completed_tasks,
                "failed_tasks": result.failed_tasks,
                "duration": result.duration,
                "summary": self.get_implementation_status(),
                "next_steps": self.phase_manager.get_next_steps(),
            }

        except Exception as e:
            logger.exception(f"Implementation failed for phase {phase}: {e}")
            return {
                "status": "error",
                "phase": phase,
                "error": str(e),
                "summary": self.get_implementation_status(),
            }

    async def run_all_phases(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Run all implementation phases in sequence

        Args:
            dry_run: If True, only simulate the execution

        Returns:
            Dictionary containing results for all phases
        """
        return await self.run_implementation("all", dry_run)

    async def run_specific_task(self, task_name: str, dry_run: bool = False) -> dict[str, Any]:
        """
        Run a specific implementation task

        Args:
            task_name: Name of the task to execute
            dry_run: If True, only simulate the execution

        Returns:
            Dictionary containing task execution result
        """
        logger.info(f"Running specific task: {task_name} (dry_run={dry_run})")

        try:
            execution = await self.task_executor.execute_task(task_name, dry_run)
            return {
                "status": execution.status,
                "task_name": task_name,
                "duration": execution.duration,
                "files_created": execution.files_created,
                "logs": execution.logs,
                "error": execution.error_message,
            }
        except Exception as e:
            logger.exception(f"Task execution failed for {task_name}: {e}")
            return {"status": "error", "task_name": task_name, "error": str(e)}

    # Status and progress methods

    def get_implementation_status(self) -> dict[str, Any]:
        """
        Get current implementation status across all phases

        Returns:
            Dictionary containing comprehensive status information
        """
        return self.phase_manager.get_overall_progress()

    def get_phase_status(self, phase_name: str) -> dict[str, Any]:
        """
        Get status for a specific phase

        Args:
            phase_name: Name of the phase to check

        Returns:
            Dictionary containing phase-specific status
        """
        return self.phase_manager.get_phase_progress(phase_name)

    def get_progress_percentage(self) -> float:
        """
        Get overall progress percentage

        Returns:
            Progress percentage as float (0.0 to 100.0)
        """
        status = self.get_implementation_status()
        return status["overall_progress_percentage"]

    def get_next_steps(self) -> list[dict[str, Any]]:
        """
        Get recommended next steps based on current progress

        Returns:
            List of recommended actions with priorities and descriptions
        """
        return self.phase_manager.get_next_steps()

    # Task and phase management

    def list_available_tasks(self, phase: str | None = None) -> list[dict[str, Any]]:
        """
        List all available tasks, optionally filtered by phase

        Args:
            phase: Optional phase name to filter tasks

        Returns:
            List of task information dictionaries
        """
        if phase:
            phase_obj = self.phases.get_phase(phase)
            if not phase_obj:
                return []
            task_names = phase_obj.tasks
        else:
            task_names = self.task_registry.get_all_task_names()

        tasks = []
        for task_name in task_names:
            task = self.task_registry.get_task(task_name)
            if task:
                tasks.append(
                    {
                        "name": task.name,
                        "description": task.description,
                        "category": task.category,
                        "complexity": task.complexity,
                        "estimated_time": task.estimated_time,
                        "dependencies": task.dependencies,
                        "packages_required": task.packages_required,
                    }
                )

        return tasks

    def list_available_phases(self) -> list[dict[str, Any]]:
        """
        List all available implementation phases

        Returns:
            List of phase information dictionaries
        """
        phases = []
        for phase_name in ["immediate", "medium", "strategic"]:
            phase = self.phases.get_phase(phase_name)
            if phase:
                phases.append(
                    {
                        "name": phase_name,
                        "description": phase.description,
                        "task_count": len(phase.tasks),
                        "estimated_time": phase.estimated_time,
                        "success_criteria": phase.success_criteria,
                        "dependencies": phase.dependencies,
                    }
                )

        return phases

    def get_task_details(self, task_name: str) -> dict[str, Any] | None:
        """
        Get detailed information about a specific task

        Args:
            task_name: Name of the task

        Returns:
            Dictionary containing task details or None if not found
        """
        task = self.task_registry.get_task(task_name)
        if not task:
            return None

        # Check if task has been executed
        execution = self.task_executor.executions.get(task_name)

        return {
            "name": task.name,
            "description": task.description,
            "category": task.category,
            "complexity": task.complexity,
            "estimated_time": task.estimated_time,
            "dependencies": task.dependencies,
            "packages_required": task.packages_required,
            "files_created": task.files_created,
            "execution_status": execution.status if execution else "not_started",
            "execution_duration": execution.duration if execution else None,
            "execution_error": execution.error_message if execution else None,
        }

    # Control methods

    def pause_implementation(self) -> None:
        """Pause the current implementation"""
        self.phase_manager.pause_execution()
        logger.info("Implementation paused")

    def resume_implementation(self) -> None:
        """Resume paused implementation"""
        self.phase_manager.resume_execution()
        logger.info("Implementation resumed")

    def reset_phase(self, phase_name: str) -> None:
        """
        Reset a specific phase to allow re-execution

        Args:
            phase_name: Name of the phase to reset
        """
        self.phase_manager.reset_phase(phase_name)
        logger.info(f"Phase {phase_name} has been reset")

    def reset_all_phases(self) -> None:
        """Reset all phases to initial state"""
        for phase_name in ["immediate", "medium", "strategic"]:
            self.reset_phase(phase_name)
        logger.info("All phases have been reset")

    # Reporting methods

    def generate_implementation_report(self, report_type: str = "detailed") -> dict[str, Any]:
        """
        Generate implementation report

        Args:
            report_type: Type of report ("summary", "detailed", "executive")

        Returns:
            Dictionary containing the requested report
        """
        if report_type == "executive":
            return self.report_generator.generate_executive_summary()
        if report_type == "detailed":
            return self.report_generator.generate_detailed_report()
        # summary
        return {
            "report_type": "summary",
            "generated_at": datetime.now().isoformat(),
            "status": self.get_implementation_status(),
            "next_steps": self.get_next_steps(),
            "phase_summary": self.phase_manager.get_phase_summary(),
        }

    def save_implementation_report(
        self, output_path: str | None = None, format: str = "html"
    ) -> str:
        """
        Save implementation report to file

        Args:
            output_path: Optional path to save the report
            format: Report format ("html", "json")

        Returns:
            Path to the saved report file
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"implementation_report_{timestamp}.{format}"

        if format == "html":
            return self.report_generator.generate_html_report(output_path)
        # json
        report_data = self.generate_implementation_report("detailed")
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)

        return str(output_file)

    # Utility methods

    def validate_environment(self) -> dict[str, Any]:
        """
        Validate the environment for implementation

        Returns:
            Dictionary containing validation results
        """
        validation_results = {"valid": True, "issues": [], "warnings": [], "recommendations": []}

        # Check Python version

        # Check project structure
        required_dirs = ["autopr", "autopr/actions", "autopr/ai"]
        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                validation_results["warnings"].append(f"Expected directory not found: {dir_name}")

        # Check for existing implementations
        existing_implementations = []
        for phase_name in ["immediate", "medium", "strategic"]:
            execution = self.phase_manager.phase_executions.get(phase_name)
            if execution and execution.status == "completed":
                existing_implementations.append(phase_name)

        if existing_implementations:
            validation_results["warnings"].append(
                f"Found existing implementations: {', '.join(existing_implementations)}"
            )

        # Add recommendations
        if not validation_results["issues"]:
            validation_results["recommendations"].append("Environment is ready for implementation")
            if not existing_implementations:
                validation_results["recommendations"].append(
                    "Start with 'immediate' phase for quick wins"
                )

        return validation_results

    def get_implementation_metrics(self) -> dict[str, Any]:
        """
        Get comprehensive implementation metrics

        Returns:
            Dictionary containing various performance and progress metrics
        """
        return self.report_generator._calculate_performance_metrics()

    def export_configuration(self) -> dict[str, Any]:
        """
        Export current configuration for backup or sharing

        Returns:
            Dictionary containing exportable configuration
        """
        return {
            "export_timestamp": datetime.now().isoformat(),
            "task_registry": {
                "total_tasks": len(self.task_registry.get_all_task_names()),
                "tasks_by_category": self.report_generator._analyze_task_distribution(),
            },
            "phase_configuration": {
                phase_name: {
                    "task_count": len(phase.tasks),
                    "estimated_time": phase.estimated_time,
                    "dependencies": phase.dependencies,
                }
                for phase_name in ["immediate", "medium", "strategic"]
                for phase in [self.phases.get_phase(phase_name)]
                if phase
            },
            "current_status": self.get_implementation_status(),
            "environment_info": {
                "project_root": str(self.project_root),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            },
        }

    # Legacy method aliases for backward compatibility

    async def implement_phase(self, phase: str, dry_run: bool = False) -> dict[str, Any]:
        """Legacy alias for run_implementation"""
        return await self.run_implementation(phase, dry_run)

    def get_status(self) -> dict[str, Any]:
        """Legacy alias for get_implementation_status"""
        return self.get_implementation_status()

    def get_progress(self) -> float:
        """Legacy alias for get_progress_percentage"""
        return self.get_progress_percentage()


# Factory function for global instance management
_global_implementor: Phase1ExtensionImplementor | None = None


def get_phase1_implementor() -> Phase1ExtensionImplementor:
    """
    Get or create global Phase1ExtensionImplementor instance

    Returns:
        Global implementor instance
    """
    global _global_implementor
    if _global_implementor is None:
        _global_implementor = Phase1ExtensionImplementor()
    return _global_implementor


def reset_global_implementor() -> None:
    """Reset the global implementor instance"""
    global _global_implementor
    _global_implementor = None
