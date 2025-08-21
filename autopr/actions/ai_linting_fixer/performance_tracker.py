"""
Performance Tracker Module

This module tracks performance metrics for the AI linting fixer.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric."""

    operation: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

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
        self.metrics: List[PerformanceMetric] = []
        self.session_start = time.time()
        self.session_id = f"session_{int(self.session_start)}"

    def start_operation(
        self, operation: str, metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Start tracking an operation."""
        metric = PerformanceMetric(
            operation=operation, start_time=time.time(), metadata=metadata or {}
        )
        self.metrics.append(metric)
        return f"{operation}_{len(self.metrics)}"

    def end_operation(
        self,
        operation_id: str,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """End tracking an operation."""
        for metric in self.metrics:
            if metric.operation == operation_id.split("_")[0]:
                metric.end_time = time.time()
                metric.success = success
                metric.error_message = error_message
                break

    def get_operation_stats(self, operation: str) -> Dict[str, float]:
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

    def get_session_summary(self) -> Dict[str, any]:
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
        report += f"Completed Operations: {summary['completed_operations']}\n"
        report += f"Success Rate: {summary['success_rate']:.1%}\n"
        report += f"Average Operation Duration: {summary['average_operation_duration']:.3f} seconds\n\n"

        # Group by operation type
        operation_groups: Dict[str, List[PerformanceMetric]] = {}
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
        self.session_start = time.time()
        self.session_id = f"session_{int(self.session_start)}"
