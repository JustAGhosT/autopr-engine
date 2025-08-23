"""
Performance Tracker Module

This module tracks performance metrics for the AI linting fixer.
"""

from dataclasses import dataclass, field
import logging
import time
from typing import Any
from uuid import uuid4


logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric."""

    operation: str
    start_time: float
    end_time: float | None = None
    success: bool = False
    error_message: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    operation_id: str | None = None

    @property
    def duration(self) -> float:
        """Calculate duration of the operation."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    @property
    def is_completed(self) -> bool:
        """Check if the operation is completed."""
        return self.end_time is not None


class PerformanceTracker:
    """Tracks performance metrics for operations."""

    def __init__(self):
        """Initialize the performance tracker."""
        self.metrics: list[PerformanceMetric] = []
        self.session_start = time.time()
        self.session_id = f"session_{int(self.session_start)}"
        self._by_id: dict[str, PerformanceMetric] = {}

    def start_operation(
        self, operation: str, metadata: dict[str, str] | None = None
    ) -> str:
        """Start tracking an operation."""
        operation_id = f"{operation}_{uuid4().hex[:8]}"
        metric = PerformanceMetric(
            operation=operation, start_time=time.time(), metadata=metadata or {}
        )
        metric.operation_id = operation_id
        self.metrics.append(metric)
        self._by_id[operation_id] = metric
        return operation_id

    def end_operation(
        self,
        operation_id: str,
        success: bool = True,
        error_message: str | None = None,
    ) -> None:
        """End tracking an operation."""
        metric = self._by_id.get(operation_id)
        if metric:
            metric.end_time = time.time()
            metric.success = success
            metric.error_message = error_message
        else:
            logger.warning(f"Operation ID not found: {operation_id}")

    def get_operation_stats(self, operation: str) -> dict[str, float]:
        """Get statistics for a specific operation."""
        operation_metrics = [m for m in self.metrics if m.operation == operation]

        if not operation_metrics:
            return {}

        completed_metrics = [m for m in operation_metrics if m.is_completed]

        if not completed_metrics:
            return {}

        durations = [m.duration for m in completed_metrics]
        successes = [m for m in completed_metrics if m.success]

        return {
            "total_operations": len(operation_metrics),
            "completed_operations": len(completed_metrics),
            "successful_operations": len(successes),
            "success_rate": (
                len(successes) / len(completed_metrics) if completed_metrics else 0.0
            ),
            "average_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
        }

    def get_session_summary(self) -> dict[str, Any]:
        """Get a summary of the current session."""
        if not self.metrics:
            return {
                "session_id": self.session_id,
                "total_operations": 0,
                "session_duration": time.time() - self.session_start,
                "success_rate": 0.0,
            }

        completed_metrics = [m for m in self.metrics if m.is_completed]
        successful_metrics = [m for m in completed_metrics if m.success]

        return {
            "session_id": self.session_id,
            "total_operations": len(self.metrics),
            "completed_operations": len(completed_metrics),
            "successful_operations": len(successful_metrics),
            "session_duration": time.time() - self.session_start,
            "success_rate": (
                len(successful_metrics) / len(completed_metrics)
                if completed_metrics
                else 0.0
            ),
            "average_operation_duration": (
                sum(m.duration for m in completed_metrics) / len(completed_metrics)
                if completed_metrics
                else 0.0
            ),
        }

    def generate_report(self) -> str:
        """Generate a human-readable performance report."""
        summary = self.get_session_summary()

        report = f"Performance Report - Session {summary['session_id']}\n"
        report += "=" * 50 + "\n"
        report += f"Session Duration: {summary['session_duration']:.2f} seconds\n"
        report += f"Total Operations: {summary['total_operations']}\n"
        report += f"Completed Operations: {summary.get('completed_operations', 0)}\n"
        report += f"Success Rate: {summary['success_rate']:.1%}\n"
        report += f"Average Operation Duration: {summary.get('average_operation_duration', 0.0):.3f} seconds\n\n"

        # Group by operation type
        operation_groups: dict[str, list[PerformanceMetric]] = {}
        for metric in self.metrics:
            if metric.operation not in operation_groups:
                operation_groups[metric.operation] = []
            operation_groups[metric.operation].append(metric)

        for operation, metrics in operation_groups.items():
            stats = self.get_operation_stats(operation)
            if stats:
                report += f"Operation: {operation}\n"
                report += f"  Success Rate: {stats['success_rate']:.1%}\n"
                report += f"  Average Duration: {stats['average_duration']:.3f}s\n"
                report += f"  Min/Max Duration: {stats['min_duration']:.3f}s / {stats['max_duration']:.3f}s\n\n"

        return report

    def reset(self) -> None:
        """Reset the performance tracker."""
        self.metrics.clear()
        self._by_id.clear()
        self.session_start = time.time()
        self.session_id = f"session_{int(self.session_start)}"
