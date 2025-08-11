"""
Report Generator for Implementation Roadmap
Handles analytics, reporting, and progress visualization
"""

import operator
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .phase_manager import PhaseManager
from .task_definitions import ImplementationPhases, TaskRegistry
from .task_executor import TaskExecutor


class ReportGenerator:
    """Generates comprehensive reports for implementation progress"""

    def __init__(
        self, task_registry: TaskRegistry, task_executor: TaskExecutor, phase_manager: PhaseManager
    ) -> None:
        self.task_registry = task_registry
        self.task_executor = task_executor
        self.phase_manager = phase_manager
        self.phases = ImplementationPhases()

    def generate_executive_summary(self) -> dict[str, Any]:
        """Generate high-level executive summary"""
        overall_progress = self.phase_manager.get_overall_progress()

        # Calculate health scores
        health_scores = self._calculate_health_scores()

        # Get timeline estimates
        timeline = self._estimate_completion_timeline()

        return {
            "generated_at": datetime.now().isoformat(),
            "overall_health_score": health_scores["overall"],
            "progress_percentage": overall_progress["overall_progress_percentage"],
            "phases_completed": sum(
                1 for phase in overall_progress["phases"].values() if phase["status"] == "completed"
            ),
            "total_phases": len(overall_progress["phases"]),
            "tasks_completed": overall_progress["completed_tasks"],
            "total_tasks": overall_progress["total_tasks"],
            "success_rate": overall_progress["success_rate"],
            "estimated_completion": timeline["estimated_completion"],
            "time_remaining": timeline["time_remaining_hours"],
            "current_phase": overall_progress["current_phase"],
            "health_breakdown": health_scores,
            "key_metrics": {
                "velocity": self._calculate_velocity(),
                "quality_score": self._calculate_quality_score(),
                "risk_level": self._assess_risk_level(),
            },
            "next_milestones": self._get_next_milestones(),
        }

    def generate_detailed_report(self) -> dict[str, Any]:
        """Generate comprehensive detailed report"""
        executive_summary = self.generate_executive_summary()
        phase_analysis = self._analyze_phases()
        task_analysis = self._analyze_tasks()

        return {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "detailed_implementation_report",
                "version": "1.0",
            },
            "executive_summary": executive_summary,
            "phase_analysis": phase_analysis,
            "task_analysis": task_analysis,
            "performance_metrics": self._calculate_performance_metrics(),
            "recommendations": self._generate_recommendations(),
            "timeline_analysis": self._analyze_timeline(),
            "resource_utilization": self._analyze_resource_utilization(),
        }

    def generate_html_report(self, output_path: str | None = None) -> str:
        """Generate HTML report for stakeholder viewing"""
        report_data = self.generate_detailed_report()

        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoPR Implementation Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .content { padding: 30px; }
        .metric-card { background: #f8f9fa; border-radius: 6px; padding: 20px; margin: 10px 0; border-left: 4px solid #667eea; }
        .progress-bar { background: #e9ecef; border-radius: 10px; height: 20px; overflow: hidden; margin: 10px 0; }
        .progress-fill { background: linear-gradient(90deg, #28a745, #20c997); height: 100%; transition: width 0.3s ease; }
        .phase-section { margin: 30px 0; padding: 20px; border: 1px solid #dee2e6; border-radius: 6px; }
        .task-list { list-style: none; padding: 0; }
        .task-item { padding: 10px; margin: 5px 0; border-radius: 4px; }
        .task-success { background: #d4edda; border-left: 4px solid #28a745; }
        .task-error { background: #f8d7da; border-left: 4px solid #dc3545; }
        .task-skipped { background: #fff3cd; border-left: 4px solid #ffc107; }
        .recommendations { background: #e7f3ff; border-radius: 6px; padding: 20px; margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }
        th { background: #f8f9fa; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AutoPR Implementation Report</h1>
            <p>Generated on {generated_at}</p>
        </div>

        <div class="content">
            <div class="metric-card">
                <h2>Executive Summary</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                    <div>
                        <h4>Overall Progress</h4>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {progress_percentage}%"></div>
                        </div>
                        <p>{progress_percentage:.1f}% Complete</p>
                    </div>
                    <div>
                        <h4>Health Score</h4>
                        <p style="font-size: 2em; color: {health_color};">{health_score}/100</p>
                    </div>
                    <div>
                        <h4>Success Rate</h4>
                        <p style="font-size: 2em; color: #28a745;">{success_rate:.1f}%</p>
                    </div>
                </div>
            </div>

            <div class="phase-section">
                <h2>Phase Progress</h2>
                {phase_content}
            </div>

            <div class="recommendations">
                <h2>Key Recommendations</h2>
                <ul>
                {recommendations_list}
                </ul>
            </div>

            <div class="metric-card">
                <h2>Performance Metrics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th><th>Status</th></tr>
                    <tr><td>Velocity (tasks/hour)</td><td>{velocity:.2f}</td><td>Good</td></tr>
                    <tr><td>Quality Score</td><td>{quality_score:.1f}</td><td>Excellent</td></tr>
                    <tr><td>Risk Level</td><td>{risk_level}</td><td>Low</td></tr>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
        """

        # Format the HTML with report data
        exec_summary = report_data["executive_summary"]

        # Generate phase content
        phase_content = ""
        for phase_name, phase_data in report_data["phase_analysis"].items():
            status_color = {
                "completed": "#28a745",
                "running": "#ffc107",
                "failed": "#dc3545",
                "not_started": "#6c757d",
            }
            phase_content += f"""
            <div style="margin: 20px 0;">
                <h3>{phase_name.title()} Phase</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {phase_data['progress_percentage']}%"></div>
                </div>
                <p>Status: <span style="color: {status_color.get(phase_data['status'], '#000')};">{phase_data['status'].title()}</span></p>
                <p>{phase_data['completed_tasks']}/{phase_data['total_tasks']} tasks completed</p>
            </div>
            """

        # Generate recommendations list
        recommendations_list = ""
        for rec in report_data["recommendations"]:
            recommendations_list += f"<li>{rec}</li>"

        # Determine health color
        health_score = exec_summary["overall_health_score"]
        if health_score >= 80:
            health_color = "#28a745"
        elif health_score >= 60:
            health_color = "#ffc107"
        else:
            health_color = "#dc3545"

        formatted_html = html_template.format(
            generated_at=exec_summary["generated_at"],
            progress_percentage=exec_summary["progress_percentage"],
            health_score=health_score,
            health_color=health_color,
            success_rate=exec_summary["success_rate"] * 100,
            phase_content=phase_content,
            recommendations_list=recommendations_list,
            velocity=exec_summary["key_metrics"]["velocity"],
            quality_score=exec_summary["key_metrics"]["quality_score"],
            risk_level=exec_summary["key_metrics"]["risk_level"],
        )

        # Save to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_html)
            return str(output_file)

        return formatted_html

    def _calculate_health_scores(self) -> dict[str, float]:
        """Calculate health scores for different aspects"""
        overall_progress = self.phase_manager.get_overall_progress()

        # Progress health (0-40 points)
        progress_health = min(40, overall_progress["overall_progress_percentage"] * 0.4)

        # Success rate health (0-30 points)
        success_health = overall_progress["success_rate"] * 30

        # Velocity health (0-20 points) - based on task completion rate
        velocity_health = min(20, self._calculate_velocity() * 10)

        # Quality health (0-10 points) - based on error rate
        quality_health = max(
            0,
            10 - (overall_progress["failed_tasks"] / max(1, overall_progress["total_tasks"]) * 10),
        )

        overall_health = progress_health + success_health + velocity_health + quality_health

        return {
            "overall": round(overall_health, 1),
            "progress": round(progress_health, 1),
            "success_rate": round(success_health, 1),
            "velocity": round(velocity_health, 1),
            "quality": round(quality_health, 1),
        }

    def _estimate_completion_timeline(self) -> dict[str, Any]:
        """Estimate completion timeline based on current progress"""
        overall_progress = self.phase_manager.get_overall_progress()

        remaining_tasks = overall_progress["total_tasks"] - overall_progress["completed_tasks"]
        velocity = self._calculate_velocity()

        if velocity > 0:
            hours_remaining = remaining_tasks / velocity
            estimated_completion = datetime.now() + timedelta(hours=hours_remaining)
        else:
            hours_remaining = None
            estimated_completion = None

        return {
            "remaining_tasks": remaining_tasks,
            "current_velocity": velocity,
            "time_remaining_hours": hours_remaining,
            "estimated_completion": (
                estimated_completion.isoformat() if estimated_completion else None
            ),
        }

    def _calculate_velocity(self) -> float:
        """Calculate task completion velocity (tasks per hour)"""
        completed_executions = [
            exec
            for exec in self.task_executor.executions.values()
            if exec.status == "success" and exec.duration is not None
        ]

        if not completed_executions:
            return 0.0

        total_hours = sum(exec.duration for exec in completed_executions) / 3600  # Convert to hours
        return len(completed_executions) / max(total_hours, 0.1)  # Avoid division by zero

    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score based on success rates and error patterns"""
        overall_progress = self.phase_manager.get_overall_progress()

        if overall_progress["total_tasks"] == 0:
            return 100.0

        # Base score from success rate
        base_score = overall_progress["success_rate"] * 80

        # Bonus for completing phases
        phase_bonus = 0
        for phase_data in overall_progress["phases"].values():
            if phase_data["status"] == "completed":
                phase_bonus += 5

        # Penalty for critical failures
        critical_penalty = 0
        immediate_phase = overall_progress["phases"].get("immediate", {})
        if immediate_phase.get("failed_tasks", 0) > 0:
            critical_penalty = immediate_phase["failed_tasks"] * 5

        quality_score = min(100, base_score + phase_bonus - critical_penalty)
        return max(0, quality_score)

    def _assess_risk_level(self) -> str:
        """Assess overall project risk level"""
        overall_progress = self.phase_manager.get_overall_progress()

        # High risk conditions
        if overall_progress["failed_tasks"] > overall_progress["completed_tasks"]:
            return "High"

        immediate_phase = overall_progress["phases"].get("immediate", {})
        if immediate_phase.get("status") == "failed":
            return "High"

        # Medium risk conditions
        if overall_progress["success_rate"] < 0.7:
            return "Medium"

        if self._calculate_velocity() < 0.5:
            return "Medium"

        # Low risk (default)
        return "Low"

    def _get_next_milestones(self) -> list[dict[str, Any]]:
        """Get upcoming milestones and key deliverables"""
        milestones = []

        # Check phase completion milestones
        for phase_name in ["immediate", "medium", "strategic"]:
            phase_progress = self.phase_manager.get_phase_progress(phase_name)

            if phase_progress["status"] == "not_started":
                milestones.append(
                    {
                        "name": f"{phase_name.title()} Phase Start",
                        "type": "phase_start",
                        "priority": "high" if phase_name == "immediate" else "medium",
                        "estimated_date": self._estimate_milestone_date(phase_name, "start"),
                    }
                )
            elif phase_progress["status"] == "running":
                milestones.append(
                    {
                        "name": f"{phase_name.title()} Phase Completion",
                        "type": "phase_completion",
                        "priority": "high" if phase_name == "immediate" else "medium",
                        "progress": phase_progress["progress_percentage"],
                        "estimated_date": self._estimate_milestone_date(phase_name, "completion"),
                    }
                )

        return milestones[:5]  # Return top 5 milestones

    def _estimate_milestone_date(self, phase_name: str, milestone_type: str) -> str | None:
        """Estimate date for a specific milestone"""
        velocity = self._calculate_velocity()
        if velocity <= 0:
            return None

        phase = self.phases.get_phase(phase_name)
        if not phase:
            return None

        if milestone_type == "start":
            # Assume immediate start for not-started phases
            return datetime.now().isoformat()
        if milestone_type == "completion":
            phase_progress = self.phase_manager.get_phase_progress(phase_name)
            remaining_tasks = phase_progress["total_tasks"] - phase_progress["completed_tasks"]
            hours_to_completion = remaining_tasks / velocity
            completion_date = datetime.now() + timedelta(hours=hours_to_completion)
            return completion_date.isoformat()

        return None

    def _analyze_phases(self) -> dict[str, Any]:
        """Analyze each phase in detail"""
        phase_analysis = {}

        for phase_name in ["immediate", "medium", "strategic"]:
            phase = self.phases.get_phase(phase_name)
            execution = self.phase_manager.phase_executions.get(phase_name)
            progress = self.phase_manager.get_phase_progress(phase_name)

            analysis = {
                "name": phase_name,
                "description": phase.description if phase else "",
                "status": progress["status"],
                "progress_percentage": progress["progress_percentage"],
                "total_tasks": progress["total_tasks"],
                "completed_tasks": progress["completed_tasks"],
                "failed_tasks": progress["failed_tasks"],
                "success_rate": progress["success_rate"],
                "duration": progress["duration"],
                "estimated_time": phase.estimated_time if phase else "Unknown",
            }

            if execution:
                # Add task-level analysis
                task_performance = []
                for task_name, task_exec in execution.task_executions.items():
                    task = self.task_registry.get_task(task_name)
                    task_performance.append(
                        {
                            "name": task_name,
                            "status": task_exec.status,
                            "duration": task_exec.duration,
                            "complexity": task.complexity if task else "unknown",
                            "category": task.category if task else "unknown",
                        }
                    )

                analysis["task_performance"] = task_performance

                # Calculate phase-specific metrics
                if task_performance:
                    avg_duration = sum(t["duration"] or 0 for t in task_performance) / len(
                        task_performance
                    )
                    analysis["average_task_duration"] = avg_duration

                    complexity_breakdown = {}
                    for task in task_performance:
                        complexity = task["complexity"]
                        complexity_breakdown[complexity] = (
                            complexity_breakdown.get(complexity, 0) + 1
                        )
                    analysis["complexity_breakdown"] = complexity_breakdown

            phase_analysis[phase_name] = analysis

        return phase_analysis

    def _analyze_tasks(self) -> dict[str, Any]:
        """Analyze task-level performance and patterns"""
        all_executions = list(self.task_executor.executions.values())

        if not all_executions:
            return {"message": "No task executions found"}

        # Category analysis
        category_stats = {}
        for execution in all_executions:
            task = self.task_registry.get_task(execution.task_name)
            category = task.category if task else "unknown"

            if category not in category_stats:
                category_stats[category] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "avg_duration": 0,
                }

            category_stats[category]["total"] += 1
            if execution.status == "success":
                category_stats[category]["success"] += 1
            elif execution.status == "error":
                category_stats[category]["failed"] += 1

            if execution.duration:
                category_stats[category]["avg_duration"] += execution.duration

        # Calculate averages
        for stats in category_stats.values():
            if stats["total"] > 0:
                stats["success_rate"] = stats["success"] / stats["total"]
                stats["avg_duration"] /= stats["total"]

        # Complexity vs success rate correlation
        complexity_analysis = {}
        for execution in all_executions:
            task = self.task_registry.get_task(execution.task_name)
            complexity = task.complexity if task else "unknown"

            if complexity not in complexity_analysis:
                complexity_analysis[complexity] = {"total": 0, "success": 0}

            complexity_analysis[complexity]["total"] += 1
            if execution.status == "success":
                complexity_analysis[complexity]["success"] += 1

        for stats in complexity_analysis.values():
            if stats["total"] > 0:
                stats["success_rate"] = stats["success"] / stats["total"]

        return {
            "total_tasks_executed": len(all_executions),
            "category_performance": category_stats,
            "complexity_analysis": complexity_analysis,
            "longest_running_tasks": sorted(
                [
                    {"name": e.task_name, "duration": e.duration}
                    for e in all_executions
                    if e.duration
                ],
                key=operator.itemgetter("duration"),
                reverse=True,
            )[:5],
            "failed_tasks_analysis": [
                {"name": e.task_name, "error": e.error_message}
                for e in all_executions
                if e.status == "error"
            ],
        }

    def _calculate_performance_metrics(self) -> dict[str, Any]:
        """Calculate detailed performance metrics"""
        return {
            "velocity_metrics": {
                "current_velocity": self._calculate_velocity(),
                "target_velocity": 2.0,  # tasks per hour
                "velocity_trend": "stable",  # This would require historical data
            },
            "quality_metrics": {
                "overall_quality_score": self._calculate_quality_score(),
                "error_rate": self._calculate_error_rate(),
                "rework_rate": 0.0,  # Placeholder
            },
            "efficiency_metrics": {
                "resource_utilization": 85.0,  # Placeholder
                "time_to_completion": self._estimate_completion_timeline()["time_remaining_hours"],
                "cost_efficiency": "good",  # Placeholder
            },
        }

    def _calculate_error_rate(self) -> float:
        """Calculate overall error rate"""
        total_executions = len(self.task_executor.executions)
        if total_executions == 0:
            return 0.0

        failed_executions = sum(
            1 for e in self.task_executor.executions.values() if e.status == "error"
        )
        return failed_executions / total_executions

    def _generate_recommendations(self) -> list[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        overall_progress = self.phase_manager.get_overall_progress()
        velocity = self._calculate_velocity()
        quality_score = self._calculate_quality_score()

        # Progress-based recommendations
        if overall_progress["overall_progress_percentage"] < 25:
            recommendations.append(
                "Focus on completing immediate priority tasks to establish momentum"
            )

        # Velocity-based recommendations
        if velocity < 1.0:
            recommendations.append("Consider parallelizing independent tasks to improve velocity")

        # Quality-based recommendations
        if quality_score < 70:
            recommendations.append("Review failed tasks and implement better error handling")

        # Phase-specific recommendations
        immediate_phase = overall_progress["phases"].get("immediate", {})
        if immediate_phase.get("failed_tasks", 0) > 0:
            recommendations.append(
                "Address failed immediate priority tasks before proceeding to medium priority"
            )

        # Risk-based recommendations
        risk_level = self._assess_risk_level()
        if risk_level == "High":
            recommendations.append(
                "Implement risk mitigation strategies and increase monitoring frequency"
            )

        # Default recommendation if none generated
        if not recommendations:
            recommendations.append(
                "Continue with current implementation approach - progress is on track"
            )

        return recommendations

    def _analyze_timeline(self) -> dict[str, Any]:
        """Analyze timeline and scheduling aspects"""
        timeline_data = self._estimate_completion_timeline()

        return {
            "current_timeline": timeline_data,
            "milestone_tracking": self._get_next_milestones(),
            "schedule_variance": {
                "ahead_of_schedule": False,  # Would need baseline to calculate
                "behind_schedule": False,
                "variance_days": 0,
            },
            "critical_path": self._identify_critical_path(),
        }

    def _identify_critical_path(self) -> list[str]:
        """Identify critical path tasks that could delay completion"""
        # Simplified critical path - tasks with dependencies
        critical_tasks = []

        for phase_name in ["immediate", "medium", "strategic"]:
            phase = self.phases.get_phase(phase_name)
            if phase:
                for task_name in phase.tasks:
                    task = self.task_registry.get_task(task_name)
                    if task and task.dependencies:
                        critical_tasks.append(task_name)

        return critical_tasks[:10]  # Top 10 critical tasks

    def _analyze_resource_utilization(self) -> dict[str, Any]:
        """Analyze resource utilization patterns"""
        return {
            "task_distribution": self._analyze_task_distribution(),
            "time_allocation": self._analyze_time_allocation(),
            "bottlenecks": self._identify_bottlenecks(),
            "optimization_opportunities": self._identify_optimization_opportunities(),
        }

    def _analyze_task_distribution(self) -> dict[str, int]:
        """Analyze distribution of tasks across categories"""
        distribution = {}

        for task_name in self.task_registry.get_all_task_names():
            task = self.task_registry.get_task(task_name)
            if task:
                category = task.category
                distribution[category] = distribution.get(category, 0) + 1

        return distribution

    def _analyze_time_allocation(self) -> dict[str, float]:
        """Analyze time allocation across different task types"""
        time_allocation = {}

        for execution in self.task_executor.executions.values():
            if execution.duration:
                task = self.task_registry.get_task(execution.task_name)
                category = task.category if task else "unknown"
                time_allocation[category] = time_allocation.get(category, 0) + execution.duration

        return time_allocation

    def _identify_bottlenecks(self) -> list[str]:
        """Identify potential bottlenecks in the implementation"""
        bottlenecks = []

        # Tasks with many dependencies
        for task_name in self.task_registry.get_all_task_names():
            task = self.task_registry.get_task(task_name)
            if task and len(task.dependencies) > 2:
                bottlenecks.append(f"Task '{task_name}' has {len(task.dependencies)} dependencies")

        # Failed critical tasks
        immediate_phase = self.phase_manager.phase_executions.get("immediate")
        if immediate_phase:
            bottlenecks.extend(
                f"Critical task '{failed_task}' has failed"
                for failed_task in immediate_phase.failed_tasks
            )

        return bottlenecks

    def _identify_optimization_opportunities(self) -> list[str]:
        """Identify opportunities for optimization"""
        opportunities = []

        # Tasks that could be parallelized
        parallel_candidates = []
        for phase_name in ["immediate", "medium", "strategic"]:
            phase = self.phases.get_phase(phase_name)
            if phase:
                independent_tasks = [
                    task_name
                    for task_name in phase.tasks
                    if not self.task_registry.get_task(task_name).dependencies
                ]
                if len(independent_tasks) > 1:
                    parallel_candidates.extend(independent_tasks)

        if parallel_candidates:
            opportunities.append(
                f"Consider running {len(parallel_candidates)} independent tasks in parallel"
            )

        # Automation opportunities
        repetitive_categories = self._analyze_task_distribution()
        for category, count in repetitive_categories.items():
            if count > 3:
                opportunities.append(f"Consider automating {category} tasks ({count} instances)")

        return opportunities
