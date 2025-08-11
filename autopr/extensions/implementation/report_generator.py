"""
Report Generator Module

Generates comprehensive reports and analytics for implementation roadmap execution.
"""

from datetime import datetime, timedelta
import json
import logging
import operator
from pathlib import Path
from typing import Any

from .phase_manager import PhaseManager
from .task_executor import TaskExecution, TaskExecutor

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates comprehensive reports for implementation progress."""

    def __init__(
        self, phase_manager: PhaseManager, task_executor: TaskExecutor, project_root: Path
    ) -> None:
        self.phase_manager = phase_manager
        self.task_executor = task_executor
        self.project_root = project_root

    def generate_progress_report(self) -> dict[str, Any]:
        """Generate a comprehensive progress report."""
        overall_status = self.phase_manager.get_overall_status()
        execution_summary = self.task_executor.get_execution_summary()

        return {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "progress_report",
                "version": "1.0",
            },
            "executive_summary": self._generate_executive_summary(
                overall_status, execution_summary
            ),
            "overall_status": overall_status,
            "execution_summary": execution_summary,
            "phase_details": self._generate_phase_details(),
            "task_analysis": self._generate_task_analysis(),
            "recommendations": self._generate_recommendations(),
            "next_steps": self.phase_manager.get_next_steps(),
            "metrics": self._generate_metrics(),
            "timeline": self._generate_timeline(),
        }

    def _generate_executive_summary(
        self, overall_status: dict[str, Any], execution_summary: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate executive summary."""
        total_phases = overall_status.get("total_phases", 0)
        completed_phases = overall_status.get("completed_phases", 0)
        failed_phases = overall_status.get("failed_phases", 0)

        total_tasks = execution_summary.get("total_tasks", 0)
        completed_tasks = execution_summary.get("completed", 0)
        failed_tasks = execution_summary.get("failed", 0)

        # Calculate health score
        phase_health = (completed_phases / total_phases * 100) if total_phases > 0 else 0
        task_health = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        overall_health = (phase_health + task_health) / 2

        # Determine status color
        if overall_health >= 80:
            status_color = "green"
        elif overall_health >= 60:
            status_color = "yellow"
        else:
            status_color = "red"

        return {
            "overall_health_score": round(overall_health, 1),
            "status_color": status_color,
            "current_phase": overall_status.get("current_phase"),
            "progress_percentage": round(overall_status.get("overall_progress_percentage", 0), 1),
            "phases_completed": f"{completed_phases}/{total_phases}",
            "tasks_completed": f"{completed_tasks}/{total_tasks}",
            "critical_issues": failed_phases + failed_tasks,
            "estimated_completion": self._estimate_completion_date(),
            "key_achievements": self._get_key_achievements(),
            "major_blockers": self._get_major_blockers(),
        }

    def _generate_phase_details(self) -> dict[str, Any]:
        """Generate detailed phase information."""
        phase_details = {}

        for phase_id in self.phase_manager.phase_definitions:
            status = self.phase_manager.get_phase_status(phase_id)
            phase_details[phase_id] = {
                **status,
                "success_criteria": self.phase_manager.phase_definitions[phase_id].get(
                    "success_criteria", []
                ),
                "risk_assessment": self._assess_phase_risk(phase_id),
                "resource_utilization": self._calculate_resource_utilization(phase_id),
                "quality_metrics": self._calculate_quality_metrics(phase_id),
            }

        return phase_details

    def _generate_task_analysis(self) -> dict[str, Any]:
        """Generate task-level analysis."""
        task_categories = {}
        task_complexity_analysis = {}

        # Group tasks by category
        from .task_definitions import TaskRegistry

        categories = TaskRegistry.get_task_categories()

        for category, task_ids in categories.items():
            completed = sum(
                1
                for task_id in task_ids
                if task_id in self.task_executor.executions
                and self.task_executor.executions[task_id].is_completed
            )
            failed = sum(
                1
                for task_id in task_ids
                if task_id in self.task_executor.executions
                and self.task_executor.executions[task_id].is_failed
            )

            task_categories[category] = {
                "total_tasks": len(task_ids),
                "completed": completed,
                "failed": failed,
                "success_rate": (completed / len(task_ids) * 100) if task_ids else 0,
            }

        # Analyze task complexity vs success rate
        task_definitions = TaskRegistry.get_task_definitions()
        complexity_levels = ["low", "medium", "high", "very_high"]

        for complexity in complexity_levels:
            matching_tasks = [
                task_id
                for task_id, task_info in task_definitions.items()
                if task_info.get("complexity") == complexity
            ]

            if matching_tasks:
                completed = sum(
                    1
                    for task_id in matching_tasks
                    if task_id in self.task_executor.executions
                    and self.task_executor.executions[task_id].is_completed
                )

                task_complexity_analysis[complexity] = {
                    "total_tasks": len(matching_tasks),
                    "completed": completed,
                    "success_rate": (
                        (completed / len(matching_tasks) * 100) if matching_tasks else 0
                    ),
                }

        return {
            "category_breakdown": task_categories,
            "complexity_analysis": task_complexity_analysis,
            "longest_running_tasks": self._get_longest_running_tasks(),
            "most_failed_tasks": self._get_most_failed_tasks(),
        }

    def _generate_recommendations(self) -> list[dict[str, Any]]:
        """Generate actionable recommendations."""
        recommendations = []

        # Analyze failed tasks
        failed_executions = [
            execution for execution in self.task_executor.executions.values() if execution.is_failed
        ]

        if failed_executions:
            recommendations.append(
                {
                    "type": "critical",
                    "title": "Address Failed Tasks",
                    "description": f"{len(failed_executions)} tasks have failed and need attention",
                    "action": "Review error logs and retry failed tasks",
                    "priority": "high",
                    "impact": "Blocks progress on dependent tasks",
                }
            )

        # Check for slow phases
        slow_phases = []
        for phase_id, execution in self.phase_manager.phase_executions.items():
            if execution.duration and execution.duration > timedelta(days=7):
                slow_phases.append(phase_id)

        if slow_phases:
            recommendations.append(
                {
                    "type": "performance",
                    "title": "Optimize Slow Phases",
                    "description": f"Phases {', '.join(slow_phases)} are taking longer than expected",
                    "action": "Review task dependencies and consider parallel execution",
                    "priority": "medium",
                    "impact": "Delays overall implementation timeline",
                }
            )

        # Check resource utilization
        overall_status = self.phase_manager.get_overall_status()
        if overall_status.get("overall_progress_percentage", 0) < 50:
            recommendations.append(
                {
                    "type": "strategic",
                    "title": "Accelerate Implementation",
                    "description": "Implementation progress is below 50%",
                    "action": "Consider allocating more resources or simplifying scope",
                    "priority": "medium",
                    "impact": "Affects delivery timeline",
                }
            )

        return recommendations

    def _generate_metrics(self) -> dict[str, Any]:
        """Generate key performance metrics."""
        execution_summary = self.task_executor.get_execution_summary()
        self.phase_manager.get_overall_status()

        # Calculate timeline metrics
        all_executions: list[TaskExecution] = []
        for phase_exec in self.phase_manager.phase_executions.values():
            all_executions.extend(phase_exec.task_executions.values())

        if all_executions:
            # Extract non-None start times directly
            start_times = [
                exec.start_time for exec in all_executions if exec.start_time is not None
            ]
            if start_times:
                earliest_start = min(start_times)
                # Extract non-None end times directly
                end_times = [exec.end_time for exec in all_executions if exec.end_time is not None]
                if end_times:
                    latest_end = max(end_times)
                    total_duration = latest_end - earliest_start
                else:
                    total_duration = None
            else:
                total_duration = None
        else:
            total_duration = None

        # Calculate velocity (tasks completed per day)
        completed_executions = [
            execution
            for execution in self.task_executor.executions.values()
            if execution.is_completed and execution.start_time
        ]

        if completed_executions:
            # Extract non-None start times directly
            start_times = [e.start_time for e in completed_executions if e.start_time is not None]
            if start_times:
                earliest_start = min(start_times)
                days_elapsed = (datetime.now() - earliest_start).days or 1
                velocity = len(completed_executions) / days_elapsed
            else:
                velocity = 0
        else:
            velocity = 0

        # Calculate average task duration
        completed_durations = [
            execution.duration.total_seconds() / 3600  # Convert to hours
            for execution in completed_executions
            if execution.duration
        ]
        avg_task_duration = (
            sum(completed_durations) / len(completed_durations) if completed_durations else 0
        )

        return {
            "velocity_tasks_per_day": round(velocity, 2),
            "average_task_duration_hours": round(avg_task_duration, 2),
            "success_rate_percentage": round(execution_summary.get("success_rate", 0) * 100, 1),
            "total_implementation_time_hours": round(
                execution_summary.get("total_duration_seconds", 0) / 3600, 2
            ),
            "phases_on_track": self._count_phases_on_track(),
            "critical_path_tasks": self._identify_critical_path_tasks(),
            "resource_efficiency": self._calculate_resource_efficiency(),
            "total_duration": total_duration,
        }

    def _generate_timeline(self) -> list[dict[str, Any]]:
        """Generate implementation timeline."""
        timeline = []

        for phase_id, phase_execution in self.phase_manager.phase_executions.items():
            if phase_execution.start_time:
                timeline.append(
                    {
                        "date": phase_execution.start_time.isoformat(),
                        "event": f"Started phase: {phase_id}",
                        "type": "phase_start",
                        "phase_id": phase_id,
                    }
                )

            if phase_execution.end_time:
                timeline.append(
                    {
                        "date": phase_execution.end_time.isoformat(),
                        "event": f"Completed phase: {phase_id}",
                        "type": "phase_end",
                        "phase_id": phase_id,
                        "status": phase_execution.status,
                    }
                )

        # Add task milestones
        for task_id, task_execution in self.task_executor.executions.items():
            if task_execution.is_completed and task_execution.end_time:
                timeline.append(
                    {
                        "date": task_execution.end_time.isoformat(),
                        "event": f"Completed task: {task_id}",
                        "type": "task_completion",
                        "task_id": task_id,
                    }
                )

        # Sort by date
        timeline.sort(key=operator.itemgetter("date"))

        return timeline

    def save_report(self, report: dict[str, Any], filename: str | None = None) -> Path:
        """Save report to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"implementation_report_{timestamp}.json"

        report_path = self.project_root / "reports" / filename
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Report saved to: {report_path}")
        return report_path

    def generate_html_report(self, report: dict[str, Any]) -> str:
        """Generate HTML version of the report."""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AutoPR Implementation Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background: #f5f5f5; padding: 20px; border-radius: 8px; }
                .status-green { color: #28a745; }
                .status-yellow { color: #ffc107; }
                .status-red { color: #dc3545; }
                .metric { display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
                .phase { margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; background: #f8f9fa; }
                .recommendation { margin: 10px 0; padding: 10px; border-radius: 5px; }
                .critical { background: #f8d7da; border: 1px solid #f5c6cb; }
                .performance { background: #fff3cd; border: 1px solid #ffeaa7; }
                .strategic { background: #d1ecf1; border: 1px solid #bee5eb; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>AutoPR Implementation Report</h1>
                <p>Generated: {generated_at}</p>
                <p class="status-{status_color}">Health Score: {health_score}%</p>
            </div>

            <h2>Executive Summary</h2>
            <div class="metric">Progress: {progress}%</div>
            <div class="metric">Phases: {phases_completed}</div>
            <div class="metric">Tasks: {tasks_completed}</div>
            <div class="metric">Success Rate: {success_rate}%</div>

            <h2>Recommendations</h2>
            {recommendations_html}

            <h2>Phase Status</h2>
            {phases_html}

        </body>
        </html>
        """

        # Format recommendations
        recommendations_html = ""
        for rec in report.get("recommendations", []):
            recommendations_html += f"""
            <div class="recommendation {rec['type']}">
                <strong>{rec['title']}</strong><br>
                {rec['description']}<br>
                <em>Action: {rec['action']}</em>
            </div>
            """

        # Format phases
        phases_html = ""
        for phase_id, phase_data in report.get("phase_details", {}).items():
            phases_html += f"""
            <div class="phase">
                <h3>{phase_data.get('name', phase_id)}</h3>
                <p>Status: {phase_data.get('status', 'unknown')}</p>
                <p>Progress: {phase_data.get('progress_percentage', 0)}%</p>
                <p>Tasks: {phase_data.get('completed_tasks', 0)}/{phase_data.get('total_tasks', 0)}</p>
            </div>
            """

        executive = report.get("executive_summary", {})

        return html_template.format(
            generated_at=report.get("report_metadata", {}).get("generated_at", ""),
            status_color=executive.get("status_color", "red"),
            health_score=executive.get("overall_health_score", 0),
            progress=executive.get("progress_percentage", 0),
            phases_completed=executive.get("phases_completed", "0/0"),
            tasks_completed=executive.get("tasks_completed", "0/0"),
            success_rate=report.get("metrics", {}).get("success_rate_percentage", 0),
            recommendations_html=recommendations_html,
            phases_html=phases_html,
        )

    # Helper methods

    def _estimate_completion_date(self) -> str | None:
        """Estimate completion date based on current velocity."""
        # Placeholder implementation
        return None

    def _get_key_achievements(self) -> list[str]:
        """Get list of key achievements."""
        achievements = [
            f"Completed {execution.task_id}"
            for execution in self.task_executor.executions.values()
            if execution.is_completed
        ]
        return achievements[:5]  # Return top 5

    def _get_major_blockers(self) -> list[str]:
        """Get list of major blockers."""
        blockers = [
            f"Failed {execution.task_id}: {execution.error_message}"
            for execution in self.task_executor.executions.values()
            if execution.is_failed
        ]
        return blockers[:3]  # Return top 3

    def _assess_phase_risk(self, phase_id: str) -> str:
        """Assess risk level for a phase."""
        if phase_id in self.phase_manager.phase_executions:
            execution = self.phase_manager.phase_executions[phase_id]
            failed_tasks = sum(1 for e in execution.task_executions.values() if e.is_failed)
            if failed_tasks > 2:
                return "high"
            if failed_tasks > 0:
                return "medium"
        return "low"

    def _calculate_resource_utilization(self, phase_id: str) -> float:
        """Calculate resource utilization for a phase."""
        # Placeholder implementation
        return 75.0

    def _calculate_quality_metrics(self, phase_id: str) -> dict[str, Any]:
        """Calculate quality metrics for a phase."""
        # Placeholder implementation
        return {"test_coverage": 85, "code_quality": 92}

    def _get_longest_running_tasks(self) -> list[dict[str, Any]]:
        """Get longest running tasks."""
        completed_tasks = [
            (task_id, execution)
            for task_id, execution in self.task_executor.executions.items()
            if execution.is_completed and execution.duration
        ]

        # Sort by duration, handling None values
        completed_tasks.sort(
            key=lambda x: x[1].duration.total_seconds() if x[1].duration else 0, reverse=True
        )

        return [
            {
                "task_id": task_id,
                "duration_hours": (
                    round(execution.duration.total_seconds() / 3600, 2) if execution.duration else 0
                ),
            }
            for task_id, execution in completed_tasks[:5]
        ]

    def _get_most_failed_tasks(self) -> list[str]:
        """Get most frequently failed tasks."""
        failed_tasks = [
            execution.task_id
            for execution in self.task_executor.executions.values()
            if execution.is_failed
        ]
        return list(set(failed_tasks))[:5]

    def _count_phases_on_track(self) -> int:
        """Count phases that are on track."""
        # Placeholder implementation
        return len(self.phase_manager.phase_executions)

    def _identify_critical_path_tasks(self) -> list[str]:
        """Identify tasks on the critical path."""
        # Placeholder implementation
        return ["setup_sentry_monitoring", "implement_structured_logging"]

    def _calculate_resource_efficiency(self) -> float:
        """Calculate overall resource efficiency."""
        # Placeholder implementation
        return 82.5
