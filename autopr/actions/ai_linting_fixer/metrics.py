"""
Performance Metrics and Analytics

Comprehensive performance tracking and analysis for AI linting operations,
including timing, throughput, resource usage, and quality metrics.
"""

import logging
import time
from datetime import datetime
from typing import Any

import psutil
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PerformanceMetrics(BaseModel):
    """Detailed performance metrics for AI linting operations."""

    # Timing metrics
    total_duration: float
    flake8_duration: float
    ai_processing_duration: float
    file_io_duration: float

    # Throughput metrics
    files_per_second: float
    issues_per_second: float
    tokens_per_second: float

    # Resource metrics
    total_files_processed: int
    total_issues_found: int
    total_issues_fixed: int
    total_tokens_used: int
    average_file_size: float

    # Success metrics
    success_rate: float
    average_confidence_score: float
    fix_acceptance_rate: float

    # API metrics
    api_calls_made: int
    average_api_response_time: float
    api_error_rate: float

    # Parallelization metrics
    workers_used: int
    parallel_efficiency: float  # 0-1, how well parallel processing worked
    queue_wait_time: float


class SessionMetrics(BaseModel):
    """Session-level performance metrics for tracking overall execution."""

    session_id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: datetime | None = None

    # High-level counts
    total_files: int = 0
    total_issues: int = 0
    successful_fixes: int = 0
    failed_fixes: int = 0

    # Timing data
    api_response_times: list[float] = Field(default_factory=list)
    processing_times: list[float] = Field(default_factory=list)
    confidence_scores: list[float] = Field(default_factory=list)

    # Resource tracking
    peak_memory_usage: float = 0.0  # MB
    cpu_usage_samples: list[float] = Field(default_factory=list)

    # API usage
    api_calls: int = 0
    total_tokens: int = 0


class MetricsCollector:
    """Collects and aggregates performance metrics during AI linting operations."""

    def __init__(self):
        self.session_metrics = SessionMetrics()
        self.operation_start_times: dict[str, float] = {}
        self.file_metrics: list[dict[str, Any]] = []

    def start_session(self) -> None:
        """Start a new metrics collection session."""
        self.session_metrics = SessionMetrics()
        self.session_metrics.start_time = datetime.now()

    def end_session(self) -> None:
        """End the current metrics collection session."""
        self.session_metrics.end_time = datetime.now()

    def start_operation(self, operation_name: str) -> None:
        """Start timing an operation."""
        self.operation_start_times[operation_name] = time.time()

    def end_operation(self, operation_name: str) -> float:
        """End timing an operation and return duration."""
        if operation_name not in self.operation_start_times:
            return 0.0

        duration = time.time() - self.operation_start_times[operation_name]
        del self.operation_start_times[operation_name]
        return duration

    def record_api_call(self, response_time: float, tokens_used: int = 0) -> None:
        """Record API call metrics."""
        self.session_metrics.api_calls += 1
        self.session_metrics.total_tokens += tokens_used
        self.session_metrics.api_response_times.append(response_time)

    def record_fix_attempt(
        self, success: bool, confidence: float | None = None, processing_time: float = 0.0
    ) -> None:
        """Record a fix attempt."""
        if success:
            self.session_metrics.successful_fixes += 1
        else:
            self.session_metrics.failed_fixes += 1

        if confidence is not None:
            self.session_metrics.confidence_scores.append(confidence)

        if processing_time > 0:
            self.session_metrics.processing_times.append(processing_time)

    def record_file_metrics(
        self,
        file_path: str,
        issues_found: int,
        issues_fixed: int,
        file_size: int,
        processing_time: float,
        complexity_score: float,
    ) -> None:
        """Record file-level metrics."""
        self.file_metrics.append(
            {
                "file_path": file_path,
                "issues_found": issues_found,
                "issues_fixed": issues_fixed,
                "file_size": file_size,
                "processing_time": processing_time,
                "complexity_score": complexity_score,
                "timestamp": datetime.now(),
            }
        )

    def sample_resource_usage(self) -> None:
        """Sample current resource usage."""
        try:
            # Memory usage
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.session_metrics.peak_memory_usage = max(
                self.session_metrics.peak_memory_usage, memory_mb
            )

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            self.session_metrics.cpu_usage_samples.append(cpu_percent)

        except Exception as e:
            logger.debug(f"Failed to sample resource usage: {e}")

    def calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics from collected data."""

        # Calculate durations
        total_duration = 0.0
        if self.session_metrics.end_time and self.session_metrics.start_time:
            total_duration = (
                self.session_metrics.end_time - self.session_metrics.start_time
            ).total_seconds()

        # Calculate averages
        avg_api_response = (
            sum(self.session_metrics.api_response_times)
            / len(self.session_metrics.api_response_times)
            if self.session_metrics.api_response_times
            else 0.0
        )

        avg_confidence = (
            sum(self.session_metrics.confidence_scores)
            / len(self.session_metrics.confidence_scores)
            if self.session_metrics.confidence_scores
            else 0.0
        )

        # Calculate rates
        success_rate = (
            self.session_metrics.successful_fixes
            / (self.session_metrics.successful_fixes + self.session_metrics.failed_fixes)
            if (self.session_metrics.successful_fixes + self.session_metrics.failed_fixes) > 0
            else 0.0
        )

        return PerformanceMetrics(
            total_duration=total_duration,
            flake8_duration=0.0,  # TODO: Track separately
            ai_processing_duration=0.0,  # TODO: Track separately
            file_io_duration=0.0,  # TODO: Track separately
            files_per_second=(
                self.session_metrics.total_files / total_duration if total_duration > 0 else 0.0
            ),
            issues_per_second=(
                self.session_metrics.total_issues / total_duration if total_duration > 0 else 0.0
            ),
            tokens_per_second=(
                self.session_metrics.total_tokens / total_duration if total_duration > 0 else 0.0
            ),
            total_files_processed=self.session_metrics.total_files,
            total_issues_found=self.session_metrics.total_issues,
            total_issues_fixed=self.session_metrics.successful_fixes,
            total_tokens_used=self.session_metrics.total_tokens,
            average_file_size=0.0,  # TODO: Calculate from file_metrics
            success_rate=success_rate,
            average_confidence_score=avg_confidence,
            fix_acceptance_rate=1.0,  # TODO: Track user acceptance
            api_calls_made=self.session_metrics.api_calls,
            average_api_response_time=avg_api_response,
            api_error_rate=0.0,  # TODO: Track API errors
            workers_used=1,  # TODO: Track actual workers
            parallel_efficiency=1.0,  # TODO: Calculate from parallel ops
            queue_wait_time=0.0,  # TODO: Track queue wait times
        )

    def get_session_metrics(self) -> dict[str, Any]:
        """Get current session metrics as a dictionary."""
        # End session if not already ended
        if not self.session_metrics.end_time:
            self.end_session()

        # Calculate total duration
        total_duration = 0.0
        if self.session_metrics.end_time and self.session_metrics.start_time:
            total_duration = (
                self.session_metrics.end_time - self.session_metrics.start_time
            ).total_seconds()

        return {
            "session_id": self.session_metrics.session_id,
            "total_duration": total_duration,
            "total_files": self.session_metrics.total_files,
            "total_issues": self.session_metrics.total_issues,
            "successful_fixes": self.session_metrics.successful_fixes,
            "failed_fixes": self.session_metrics.failed_fixes,
            "api_calls": self.session_metrics.api_calls,
            "total_tokens": self.session_metrics.total_tokens,
            "peak_memory_usage": self.session_metrics.peak_memory_usage,
            "average_api_response_time": (
                sum(self.session_metrics.api_response_times)
                / len(self.session_metrics.api_response_times)
                if self.session_metrics.api_response_times
                else 0.0
            ),
            "average_confidence_score": (
                sum(self.session_metrics.confidence_scores)
                / len(self.session_metrics.confidence_scores)
                if self.session_metrics.confidence_scores
                else 0.0
            ),
        }

    def get_session_summary(self) -> dict[str, Any]:
        """Get a summary of the current session."""
        duration = 0.0
        if self.session_metrics.end_time and self.session_metrics.start_time:
            duration = (
                self.session_metrics.end_time - self.session_metrics.start_time
            ).total_seconds()

        return {
            "session_id": self.session_metrics.session_id,
            "duration": duration,
            "files_processed": len(self.file_metrics),
            "total_issues": self.session_metrics.total_issues,
            "successful_fixes": self.session_metrics.successful_fixes,
            "failed_fixes": self.session_metrics.failed_fixes,
            "api_calls": self.session_metrics.api_calls,
            "total_tokens": self.session_metrics.total_tokens,
            "peak_memory_mb": self.session_metrics.peak_memory_usage,
            "average_cpu_usage": (
                sum(self.session_metrics.cpu_usage_samples)
                / len(self.session_metrics.cpu_usage_samples)
                if self.session_metrics.cpu_usage_samples
                else 0.0
            ),
        }


class MetricsAggregator:
    """Aggregates metrics across multiple sessions for analysis."""

    def __init__(self):
        self.historical_sessions: list[SessionMetrics] = []
        self.performance_trends: dict[str, list[float]] = {}

    def add_session(self, session_metrics: SessionMetrics) -> None:
        """Add a completed session for analysis."""
        self.historical_sessions.append(session_metrics)
        self._update_trends(session_metrics)

    def _update_trends(self, session: SessionMetrics) -> None:
        """Update performance trend tracking."""
        if "success_rate" not in self.performance_trends:
            self.performance_trends["success_rate"] = []

        success_rate = (
            session.successful_fixes / (session.successful_fixes + session.failed_fixes)
            if (session.successful_fixes + session.failed_fixes) > 0
            else 0.0
        )
        self.performance_trends["success_rate"].append(success_rate)

        # Add more trend tracking as needed
        if session.api_response_times:
            if "avg_api_response" not in self.performance_trends:
                self.performance_trends["avg_api_response"] = []
            avg_response = sum(session.api_response_times) / len(session.api_response_times)
            self.performance_trends["avg_api_response"].append(avg_response)

    def get_performance_trends(self, metric: str, window: int = 10) -> list[float]:
        """Get recent performance trends for a specific metric."""
        if metric not in self.performance_trends:
            return []
        return self.performance_trends[metric][-window:]

    def get_performance_summary(self) -> dict[str, Any]:
        """Get overall performance summary across all sessions."""
        if not self.historical_sessions:
            return {}

        total_files = sum(
            len(getattr(session, "file_metrics", [])) for session in self.historical_sessions
        )
        total_fixes = sum(session.successful_fixes for session in self.historical_sessions)
        total_failures = sum(session.failed_fixes for session in self.historical_sessions)

        return {
            "total_sessions": len(self.historical_sessions),
            "total_files_processed": total_files,
            "total_successful_fixes": total_fixes,
            "total_failed_fixes": total_failures,
            "overall_success_rate": (
                total_fixes / (total_fixes + total_failures)
                if (total_fixes + total_failures) > 0
                else 0.0
            ),
            "average_session_duration": sum(
                (session.end_time - session.start_time).total_seconds()
                for session in self.historical_sessions
                if session.end_time
            )
            / len(self.historical_sessions),
            "performance_trends": {
                metric: self.get_performance_trends(metric, 5) for metric in self.performance_trends
            },
        }


class PerformanceProfiler:
    """Advanced performance profiling for AI linting operations."""

    def __init__(self):
        self.profiling_data: dict[str, list[float]] = {}
        self.active_profiles: dict[str, float] = {}

    def start_profile(self, operation: str) -> None:
        """Start profiling an operation."""
        self.active_profiles[operation] = time.time()

    def end_profile(self, operation: str) -> float:
        """End profiling and record the duration."""
        if operation not in self.active_profiles:
            return 0.0

        duration = time.time() - self.active_profiles[operation]
        del self.active_profiles[operation]

        if operation not in self.profiling_data:
            self.profiling_data[operation] = []
        self.profiling_data[operation].append(duration)

        return duration

    def get_profile_stats(self, operation: str) -> dict[str, float]:
        """Get statistical summary for a profiled operation."""
        if operation not in self.profiling_data or not self.profiling_data[operation]:
            return {}

        durations = self.profiling_data[operation]
        return {
            "count": len(durations),
            "total": sum(durations),
            "average": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations),
            "median": sorted(durations)[len(durations) // 2],
        }

    def get_all_profiles(self) -> dict[str, dict[str, float]]:
        """Get profile statistics for all operations."""
        return {op: self.get_profile_stats(op) for op in self.profiling_data}


# Global metrics instances for convenience
metrics_collector = MetricsCollector()
metrics_aggregator = MetricsAggregator()
performance_profiler = PerformanceProfiler()
