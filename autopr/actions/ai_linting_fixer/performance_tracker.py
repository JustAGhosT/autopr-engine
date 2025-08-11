"""
Performance Tracker Module

This module tracks performance metrics and analytics for AI linting operations.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """Tracks performance metrics and analytics."""

    def __init__(self, metrics_file: str | None = None, display=None):
        """Initialize the performance tracker."""
        self.metrics_file = metrics_file or "./logs/performance_metrics.json"
        self.display = display
        self.session_start_time = time.time()
        self.metrics = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "total_duration": 0.0,
            # File processing metrics
            "files_processed": 0,
            "files_successful": 0,
            "files_failed": 0,
            # Issue processing metrics
            "issues_found": 0,
            "issues_fixed": 0,
            "issues_failed": 0,
            # AI/LLM metrics
            "api_calls_made": 0,
            "total_tokens_used": 0,
            "average_api_response_time": 0.0,
            "api_response_times": [],
            # Performance metrics
            "processing_times": [],
            "memory_usage_samples": [],
            "cpu_usage_samples": [],
            # Error metrics
            "errors_encountered": 0,
            "error_types": {},
            # Quality metrics
            "syntax_validation_passed": 0,
            "syntax_validation_failed": 0,
            "confidence_scores": [],
            # Resource metrics
            "peak_memory_usage": 0.0,
            "average_memory_usage": 0.0,
            "peak_cpu_usage": 0.0,
            "average_cpu_usage": 0.0,
        }

        # Ensure metrics directory exists
        self._ensure_metrics_directory()

    def _ensure_metrics_directory(self) -> None:
        """Ensure the metrics directory exists."""
        try:
            metrics_path = Path(self.metrics_file)
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            if self.display:
                self.display.error.show_warning(f"⚠️ Failed to create metrics directory: {e}")
            else:
                logger.warning(f"Failed to create metrics directory: {e}")

    def start_session(self) -> None:
        """Start a new performance tracking session."""
        self.session_start_time = time.time()
        self.metrics["start_time"] = datetime.now().isoformat()
        self.metrics["session_id"] = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.display:
            self.display.error.show_info("📊 Performance tracking session started")
        else:
            logger.info("Performance tracking session started")

    def end_session(self) -> None:
        """End the current performance tracking session."""
        end_time = time.time()
        self.metrics["end_time"] = datetime.now().isoformat()
        self.metrics["total_duration"] = end_time - self.session_start_time

        # Calculate averages
        self._calculate_averages()

        if self.display:
            self.display.error.show_info(
                f"📊 Performance tracking session ended. Duration: {self.metrics['total_duration']:.2f}s"
            )
        else:
            logger.info(
                f"Performance tracking session ended. Duration: {self.metrics['total_duration']:.2f}s"
            )

    def log_metric(self, metric_name: str, value: Any) -> None:
        """Log a single metric."""
        if metric_name in self.metrics:
            if isinstance(self.metrics[metric_name], list):
                self.metrics[metric_name].append(value)
            elif isinstance(self.metrics[metric_name], (int, float)):
                self.metrics[metric_name] += value
            else:
                self.metrics[metric_name] = value
        else:
            # Add new metric
            self.metrics[metric_name] = value

    def log_file_processing(
        self,
        file_path: str,
        success: bool,
        processing_time: float,
        issues_found: int,
        issues_fixed: int,
    ) -> None:
        """Log file processing metrics."""
        self.metrics["files_processed"] += 1

        if success:
            self.metrics["files_successful"] += 1
        else:
            self.metrics["files_failed"] += 1

        self.metrics["processing_times"].append(processing_time)
        self.metrics["issues_found"] += issues_found
        self.metrics["issues_fixed"] += issues_fixed
        self.metrics["issues_failed"] += issues_found - issues_fixed

        logger.debug(
            f"Logged file processing: {file_path}, success: {success}, time: {processing_time:.2f}s"
        )

    def log_api_call(self, response_time: float, tokens_used: int, success: bool) -> None:
        """Log API call metrics."""
        self.metrics["api_calls_made"] += 1
        self.metrics["api_response_times"].append(response_time)
        self.metrics["total_tokens_used"] += tokens_used

        if not success:
            self.metrics["errors_encountered"] += 1

        logger.debug(f"Logged API call: response_time={response_time:.2f}s, tokens={tokens_used}")

    def log_syntax_validation(self, passed: bool) -> None:
        """Log syntax validation results."""
        if passed:
            self.metrics["syntax_validation_passed"] += 1
        else:
            self.metrics["syntax_validation_failed"] += 1

    def log_confidence_score(self, confidence: float) -> None:
        """Log confidence score."""
        self.metrics["confidence_scores"].append(confidence)

    def log_error(self, error_type: str, error_message: str) -> None:
        """Log error metrics."""
        self.metrics["errors_encountered"] += 1

        if error_type not in self.metrics["error_types"]:
            self.metrics["error_types"][error_type] = 0
        self.metrics["error_types"][error_type] += 1

    def log_resource_usage(self, memory_mb: float, cpu_percent: float) -> None:
        """Log resource usage metrics."""
        self.metrics["memory_usage_samples"].append(memory_mb)
        self.metrics["cpu_usage_samples"].append(cpu_percent)

        # Update peak values
        self.metrics["peak_memory_usage"] = max(self.metrics["peak_memory_usage"], memory_mb)

        self.metrics["peak_cpu_usage"] = max(self.metrics["peak_cpu_usage"], cpu_percent)

    def get_session_metrics(self) -> dict[str, Any]:
        """Get current session metrics."""
        # Calculate current duration
        current_duration = time.time() - self.session_start_time
        metrics_copy = self.metrics.copy()
        metrics_copy["current_duration"] = current_duration

        return metrics_copy

    def get_performance_summary(self) -> dict[str, Any]:
        """Get a summary of performance metrics."""
        try:
            # Calculate averages
            avg_processing_time = (
                sum(self.metrics["processing_times"]) / len(self.metrics["processing_times"])
                if self.metrics["processing_times"]
                else 0.0
            )

            avg_api_response_time = (
                sum(self.metrics["api_response_times"]) / len(self.metrics["api_response_times"])
                if self.metrics["api_response_times"]
                else 0.0
            )

            # Calculate confidence statistics
            confidence_scores = self.metrics["confidence_scores"]
            avg_confidence = 0.0
            if confidence_scores:
                avg_confidence = sum(confidence_scores) / len(confidence_scores)

            success_rate = (
                (self.metrics["files_successful"] / self.metrics["files_processed"]) * 100
                if self.metrics["files_processed"] > 0
                else 0.0
            )

            fix_rate = (
                (self.metrics["issues_fixed"] / self.metrics["issues_found"]) * 100
                if self.metrics["issues_found"] > 0
                else 0.0
            )

            return {
                "session_duration": self.metrics["total_duration"],
                "files_processed": self.metrics["files_processed"],
                "success_rate": success_rate,
                "fix_rate": fix_rate,
                "total_api_calls": self.metrics["api_calls_made"],
                "total_tokens_used": self.metrics["total_tokens_used"],
                "average_processing_time": avg_processing_time,
                "average_api_response_time": avg_api_response_time,
                "average_confidence": avg_confidence,
                "confidence_scores_count": len(confidence_scores),
                "errors_encountered": self.metrics["errors_encountered"],
                "peak_memory_usage": self.metrics["peak_memory_usage"],
                "peak_cpu_usage": self.metrics["peak_cpu_usage"],
            }
        except Exception as e:
            logger.exception(f"Error generating performance summary: {e}")
            return {"message": "Error generating performance summary"}

    def export_metrics(self, file_path: str | None = None) -> bool:
        """Export metrics to a file."""
        try:
            export_path = file_path or self.metrics_file

            # Ensure directory exists
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)

            # End session if not already ended
            if not self.metrics["end_time"]:
                self.end_session()

            # Calculate final averages
            self._calculate_averages()

            # Export to JSON
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, indent=2, default=str)

            if self.display:
                self.display.error.show_info(f"📊 Performance metrics exported to: {export_path}")
            else:
                logger.info(f"Performance metrics exported to: {export_path}")
            return True

        except Exception as e:
            if self.display:
                self.display.error.show_warning(f"⚠️ Failed to export metrics: {e}")
            else:
                logger.exception(f"Failed to export metrics: {e}")
            return False

    def load_metrics(self, file_path: str) -> bool:
        """Load metrics from a file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                loaded_metrics = json.load(f)

            # Update current metrics with loaded data
            self.metrics.update(loaded_metrics)

            logger.info(f"Performance metrics loaded from: {file_path}")
            return True

        except Exception as e:
            logger.exception(f"Failed to load metrics from {file_path}: {e}")
            return False

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "total_duration": 0.0,
            "files_processed": 0,
            "files_successful": 0,
            "files_failed": 0,
            "issues_found": 0,
            "issues_fixed": 0,
            "issues_failed": 0,
            "api_calls_made": 0,
            "total_tokens_used": 0,
            "average_api_response_time": 0.0,
            "api_response_times": [],
            "processing_times": [],
            "memory_usage_samples": [],
            "cpu_usage_samples": [],
            "errors_encountered": 0,
            "error_types": {},
            "syntax_validation_passed": 0,
            "syntax_validation_failed": 0,
            "confidence_scores": [],
            "peak_memory_usage": 0.0,
            "average_memory_usage": 0.0,
            "peak_cpu_usage": 0.0,
            "average_cpu_usage": 0.0,
        }

        self.session_start_time = time.time()
        logger.info("Performance metrics reset")

    def _calculate_averages(self) -> None:
        """Calculate average values from collected samples."""
        try:
            # Calculate average API response time
            if self.metrics["api_response_times"]:
                self.metrics["average_api_response_time"] = sum(
                    self.metrics["api_response_times"]
                ) / len(self.metrics["api_response_times"])

            # Calculate average memory usage
            if self.metrics["memory_usage_samples"]:
                self.metrics["average_memory_usage"] = sum(
                    self.metrics["memory_usage_samples"]
                ) / len(self.metrics["memory_usage_samples"])

            # Calculate average CPU usage
            if self.metrics["cpu_usage_samples"]:
                self.metrics["average_cpu_usage"] = sum(self.metrics["cpu_usage_samples"]) / len(
                    self.metrics["cpu_usage_samples"]
                )

        except Exception as e:
            logger.debug(f"Error calculating averages: {e}")

    def get_metrics_history(self, days: int = 7) -> list[dict[str, Any]]:
        """Get metrics history from saved files."""
        try:
            metrics_dir = Path(self.metrics_file).parent
            if not metrics_dir.exists():
                return []

            history = []
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

            for metrics_file in metrics_dir.glob("*.json"):
                try:
                    if metrics_file.stat().st_mtime > cutoff_time:
                        with open(metrics_file, encoding="utf-8") as f:
                            metrics_data = json.load(f)
                            history.append(metrics_data)
                except Exception as e:
                    logger.debug(f"Failed to load metrics file {metrics_file}: {e}")

            # Sort by start time (newest first)
            history.sort(key=lambda x: x.get("start_time", ""), reverse=True)
            return history

        except Exception as e:
            logger.exception(f"Failed to get metrics history: {e}")
            return []

    def generate_performance_report(self) -> str:
        """Generate a human-readable performance report."""
        summary = self.get_performance_summary()

        if "message" in summary:
            return summary["message"]

        report = f"""
Performance Report
==================

Session Duration: {summary['session_duration']:.2f} seconds
Files Processed: {summary['files_processed']}
Success Rate: {summary['success_rate']:.1f}%
Fix Rate: {summary['fix_rate']:.1f}%

Performance Metrics:
- Average Processing Time: {summary['average_processing_time']:.2f}s per file
- Average API Response Time: {summary['average_api_response_time']:.2f}s
- Total API Calls: {summary['total_api_calls']}
- Total Tokens Used: {summary['total_tokens_used']}

Quality Metrics:
"""
        # Quality metrics
        if summary.get("average_confidence", 0) > 0:
            report += f"- Average Confidence: {summary['average_confidence']:.3f}\n"
            report += f"- Confidence Scores Count: {summary['confidence_scores_count']}\n"

            # Add confidence distribution if available
            confidence_scores = self.metrics["confidence_scores"]
            if confidence_scores:
                high_confidence = len([c for c in confidence_scores if c > 0.8])
                medium_confidence = len([c for c in confidence_scores if 0.5 <= c <= 0.8])
                low_confidence = len([c for c in confidence_scores if c < 0.5])
                total = len(confidence_scores)

                report += f"- High Confidence (>0.8): {high_confidence}/{total} ({high_confidence / total * 100:.1f}%)\n"
                report += f"- Medium Confidence (0.5-0.8): {medium_confidence}/{total} ({medium_confidence / total * 100:.1f}%)\n"
                report += f"- Low Confidence (<0.5): {low_confidence}/{total} ({low_confidence / total * 100:.1f}%)\n"

        report += f"- Errors Encountered: {summary['errors_encountered']}\n"

        report += "Resource Usage:\n"
        report += f"- Peak Memory Usage: {summary['peak_memory_usage']:.1f} MB\n"
        report += f"- Peak CPU Usage: {summary['peak_cpu_usage']:.1f}%\n"

        return report
