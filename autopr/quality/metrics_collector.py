"""
AutoPR Evaluation: Metrics Collector
Comprehensive system for tracking performance, accuracy, and user satisfaction metrics.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import sqlite3
import statistics
from typing import Any

from pydantic import BaseModel


@dataclass
class MetricPoint:
    timestamp: datetime
    metric_name: str
    value: float
    metadata: dict[str, Any]


class EvaluationMetrics(BaseModel):
    # Accuracy Metrics
    fix_success_rate: float = 0.0
    classification_accuracy: float = 0.0
    false_positive_rate: float = 0.0
    user_satisfaction_score: float = 0.0

    # Efficiency Metrics
    avg_response_time: float = 0.0
    avg_resolution_time: float = 0.0
    api_cost_per_comment: float = 0.0
    coverage_rate: float = 0.0

    # Quality Metrics
    code_quality_score: float = 0.0
    test_pass_rate: float = 0.0
    security_score: float = 0.0
    maintainability_index: float = 0.0

    # System Metrics
    uptime: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0
    resource_utilization: float = 0.0


class MetricsCollector:
    def __init__(self, db_path: str = "autopr_metrics.db") -> None:
        self.db_path = db_path
        self.init_database()

    def init_database(self) -> None:
        """Initialize metrics database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                metadata TEXT,
                session_id TEXT,
                user_id TEXT,
                comment_id TEXT
            )
        """
        )

        # Create events table for detailed tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                event_data TEXT,
                success BOOLEAN,
                duration_ms INTEGER,
                user_id TEXT,
                comment_id TEXT,
                pr_number INTEGER
            )
        """
        )

        # Create user feedback table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT NOT NULL,
                comment_id TEXT,
                rating INTEGER,  -- 1-5 scale
                feedback_text TEXT,
                category TEXT,  -- "helpful", "accurate", "fast", etc.
                autopr_action TEXT  -- what AutoPR did
            )
        """
        )

        # Create performance benchmarks table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                benchmark_name TEXT NOT NULL,
                test_case TEXT,
                expected_result TEXT,
                actual_result TEXT,
                success BOOLEAN,
                duration_ms INTEGER,
                provider TEXT,
                model TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def record_metric(
        self,
        metric_name: str,
        value: float,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        comment_id: str | None = None,
    ) -> None:
        """Record a single metric point."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO metrics (metric_name, value, metadata, session_id, user_id, comment_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                metric_name,
                value,
                json.dumps(metadata) if metadata else None,
                session_id,
                user_id,
                comment_id,
            ),
        )

        conn.commit()
        conn.close()

    def record_event(
        self,
        event_type: str,
        event_data: dict[str, Any],
        success: bool,
        duration_ms: int | None = None,
        user_id: str | None = None,
        comment_id: str | None = None,
        pr_number: int | None = None,
    ) -> None:
        """Record a detailed event."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO events (event_type, event_data, success, duration_ms, user_id, comment_id, pr_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event_type,
                json.dumps(event_data),
                success,
                duration_ms,
                user_id,
                comment_id,
                pr_number,
            ),
        )

        conn.commit()
        conn.close()

    def record_user_feedback(
        self,
        user_id: str,
        rating: int,
        feedback_text: str | None = None,
        category: str | None = None,
        autopr_action: str | None = None,
        comment_id: str | None = None,
    ) -> None:
        """Record user feedback."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO user_feedback (user_id, rating, feedback_text, category, autopr_action, comment_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                user_id,
                rating,
                feedback_text,
                category,
                autopr_action,
                comment_id,
            ),
        )

        conn.commit()
        conn.close()

    def record_benchmark(
        self,
        benchmark_name: str,
        test_case: str,
        expected_result: str,
        actual_result: str,
        success: bool,
        duration_ms: int | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        """Record benchmark test results."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO benchmarks (benchmark_name, test_case, expected_result, actual_result,
                                  success, duration_ms, provider, model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                benchmark_name,
                test_case,
                expected_result,
                actual_result,
                success,
                duration_ms,
                provider,
                model,
            ),
        )

        conn.commit()
        conn.close()

    def get_metrics_summary(self, timeframe: str = "7d") -> EvaluationMetrics:
        """Get comprehensive metrics summary for a timeframe."""
        start_time = self._get_start_time(timeframe)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate accuracy metrics
        fix_success_rate = self._calculate_fix_success_rate(cursor, start_time)
        classification_accuracy = self._calculate_classification_accuracy(cursor, start_time)
        false_positive_rate = self._calculate_false_positive_rate(cursor, start_time)
        user_satisfaction = self._calculate_user_satisfaction(cursor, start_time)

        # Calculate efficiency metrics
        avg_response_time = self._calculate_avg_response_time(cursor, start_time)
        avg_resolution_time = self._calculate_avg_resolution_time(cursor, start_time)
        api_cost = self._calculate_api_cost(cursor, start_time)
        coverage_rate = self._calculate_coverage_rate(cursor, start_time)

        # Calculate quality metrics
        code_quality_score = self._calculate_code_quality_score(cursor, start_time)
        test_pass_rate = self._calculate_test_pass_rate(cursor, start_time)
        security_score = self._calculate_security_score(cursor, start_time)
        maintainability_index = self._calculate_maintainability_index(cursor, start_time)

        # Calculate system metrics
        uptime = self._calculate_uptime(cursor, start_time)
        error_rate = self._calculate_error_rate(cursor, start_time)
        throughput = self._calculate_throughput(cursor, start_time)
        resource_utilization = self._calculate_resource_utilization(cursor, start_time)

        conn.close()

        return EvaluationMetrics(
            fix_success_rate=fix_success_rate,
            classification_accuracy=classification_accuracy,
            false_positive_rate=false_positive_rate,
            user_satisfaction_score=user_satisfaction,
            avg_response_time=avg_response_time,
            avg_resolution_time=avg_resolution_time,
            api_cost_per_comment=api_cost,
            coverage_rate=coverage_rate,
            code_quality_score=code_quality_score,
            test_pass_rate=test_pass_rate,
            security_score=security_score,
            maintainability_index=maintainability_index,
            uptime=uptime,
            error_rate=error_rate,
            throughput=throughput,
            resource_utilization=resource_utilization,
        )

    def get_benchmark_results(
        self, benchmark_name: str | None = None, timeframe: str = "30d"
    ) -> dict[str, Any]:
        """Get benchmark test results."""
        start_time = self._get_start_time(timeframe)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT benchmark_name, COUNT(*) as total_tests,
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) as passed_tests,
                   AVG(duration_ms) as avg_duration,
                   provider, model
            FROM benchmarks
            WHERE timestamp >= ?
        """
        params: list[Any] = [start_time]

        if benchmark_name:
            query += " AND benchmark_name = ?"
            params.append(benchmark_name)

        query += " GROUP BY benchmark_name, provider, model"

        cursor.execute(query, params)
        results = cursor.fetchall()

        benchmark_data = {}
        for row in results:
            name, total, passed, avg_duration, provider, model = row
            benchmark_data[f"{name}_{provider}_{model}"] = {
                "total_tests": total,
                "passed_tests": passed,
                "success_rate": passed / total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "provider": provider,
                "model": model,
            }

        conn.close()
        return benchmark_data

    def get_trend_analysis(self, metric_name: str, timeframe: str = "30d") -> dict[str, Any]:
        """Get trend analysis for a specific metric."""
        start_time = self._get_start_time(timeframe)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DATE(timestamp) as date, AVG(value) as avg_value
            FROM metrics
            WHERE metric_name = ? AND timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        """,
            (metric_name, start_time),
        )

        results = cursor.fetchall()

        if not results:
            return {"trend": "no_data", "change": 0, "values": []}

        dates = [row[0] for row in results]
        values = [row[1] for row in results]

        # Calculate trend
        if len(values) >= 2:
            recent_avg = statistics.mean(values[-7:]) if len(values) >= 7 else values[-1]
            older_avg = statistics.mean(values[:7]) if len(values) >= 14 else values[0]
            change_percent = ((recent_avg - older_avg) / older_avg * 100) if older_avg != 0 else 0

            if change_percent > 5:
                trend = "improving"
            elif change_percent < -5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
            change_percent = 0

        conn.close()

        return {
            "trend": trend,
            "change_percent": change_percent,
            "values": values,
            "dates": dates,
            "current_value": values[-1] if values else 0,
            "best_value": max(values) if values else 0,
            "worst_value": min(values) if values else 0,
        }

    def generate_report(self, timeframe: str = "7d") -> dict[str, Any]:
        """Generate comprehensive evaluation report."""
        metrics = self.get_metrics_summary(timeframe)
        benchmarks = self.get_benchmark_results(timeframe=timeframe)

        # Get trend analysis for key metrics
        trends = {}
        key_metrics = [
            "fix_success_rate",
            "user_satisfaction_score",
            "avg_response_time",
            "error_rate",
        ]
        for metric in key_metrics:
            trends[metric] = self.get_trend_analysis(metric, timeframe)

        # Calculate overall health score
        health_score = self._calculate_health_score(metrics)

        return {
            "summary": {
                "timeframe": timeframe,
                "health_score": health_score,
                "report_generated": datetime.now().isoformat(),
            },
            "metrics": metrics.dict(),
            "benchmarks": benchmarks,
            "trends": trends,
            "recommendations": self._generate_recommendations(metrics, trends),
        }

    def _get_start_time(self, timeframe: str) -> datetime:
        """Convert timeframe string to datetime."""
        now = datetime.now()
        if timeframe.endswith("d"):
            days = int(timeframe[:-1])
            return now - timedelta(days=days)
        if timeframe.endswith("h"):
            hours = int(timeframe[:-1])
            return now - timedelta(hours=hours)
        if timeframe.endswith("m"):
            minutes = int(timeframe[:-1])
            return now - timedelta(minutes=minutes)
        return now - timedelta(days=7)  # Default to 7 days

    def _calculate_fix_success_rate(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate the rate of successful automated fixes."""
        cursor.execute(
            """
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
            FROM events
            WHERE event_type = 'fix_applied' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        total, successful = result
        return (successful / total) if total > 0 else 0.0

    def _calculate_classification_accuracy(
        self, cursor: sqlite3.Cursor, start_time: datetime
    ) -> float:
        """Calculate comment classification accuracy."""
        cursor.execute(
            """
            SELECT AVG(value) FROM metrics
            WHERE metric_name = 'classification_confidence' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        return result[0] or 0.0

    def _calculate_false_positive_rate(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate false positive rate for automated actions."""
        cursor.execute(
            """
            SELECT COUNT(*) as total_actions,
                   SUM(CASE WHEN JSON_EXTRACT(event_data, '$.user_rejected') = 'true' THEN 1 ELSE 0 END) as rejected
            FROM events
            WHERE event_type IN ('fix_applied', 'issue_created') AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        total, rejected = result
        return (rejected / total) if total > 0 else 0.0

    def _calculate_user_satisfaction(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate average user satisfaction score."""
        cursor.execute(
            """
            SELECT AVG(rating) FROM user_feedback
            WHERE timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        return result[0] or 0.0

    def _calculate_avg_response_time(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate average response time in seconds."""
        cursor.execute(
            """
            SELECT AVG(duration_ms) FROM events
            WHERE event_type = 'comment_processed' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        avg_ms = result[0] or 0
        return avg_ms / 1000.0  # Convert to seconds

    def _calculate_avg_resolution_time(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate average time to resolve issues."""
        cursor.execute(
            """
            SELECT AVG(duration_ms) FROM events
            WHERE event_type = 'issue_resolved' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        avg_ms = result[0] or 0
        return avg_ms / 1000.0  # Convert to seconds

    def _calculate_api_cost(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate average API cost per comment."""
        cursor.execute(
            """
            SELECT AVG(value) FROM metrics
            WHERE metric_name = 'api_cost' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        return result[0] or 0.0

    def _calculate_coverage_rate(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate percentage of comments handled automatically."""
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_comments,
                SUM(CASE WHEN JSON_EXTRACT(event_data, '$.automated') = 'true' THEN 1 ELSE 0 END) as automated
            FROM events
            WHERE event_type = 'comment_received' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        total, automated = result
        return (automated / total) if total > 0 else 0.0

    def _calculate_code_quality_score(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate average code quality score."""
        cursor.execute(
            """
            SELECT AVG(value) FROM metrics
            WHERE metric_name = 'code_quality_score' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        return result[0] or 0.0

    def _calculate_test_pass_rate(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate test pass rate for automated fixes."""
        cursor.execute(
            """
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) as passed
            FROM events
            WHERE event_type = 'tests_run' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        total, passed = result
        return (passed / total) if total > 0 else 0.0

    def _calculate_security_score(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate security score."""
        cursor.execute(
            """
            SELECT AVG(value) FROM metrics
            WHERE metric_name = 'security_score' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        return result[0] or 0.0

    def _calculate_maintainability_index(
        self, cursor: sqlite3.Cursor, start_time: datetime
    ) -> float:
        """Calculate maintainability index."""
        cursor.execute(
            """
            SELECT AVG(value) FROM metrics
            WHERE metric_name = 'maintainability_index' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        return result[0] or 0.0

    def _calculate_uptime(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate system uptime percentage."""
        cursor.execute(
            """
            SELECT COUNT(*) as total_checks,
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_checks
            FROM events
            WHERE event_type = 'health_check' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        total, successful = result
        return (successful / total) if total > 0 else 1.0

    def _calculate_error_rate(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate system error rate."""
        cursor.execute(
            """
            SELECT COUNT(*) as total_events,
                   SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as errors
            FROM events
            WHERE timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        total, errors = result
        return (errors / total) if total > 0 else 0.0

    def _calculate_throughput(self, cursor: sqlite3.Cursor, start_time: datetime) -> float:
        """Calculate comments processed per hour."""
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM events
            WHERE event_type = 'comment_processed' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        total_comments = result[0]

        # Calculate hours elapsed
        hours_elapsed = (datetime.now() - start_time).total_seconds() / 3600
        return total_comments / hours_elapsed if hours_elapsed > 0 else 0.0

    def _calculate_resource_utilization(
        self, cursor: sqlite3.Cursor, start_time: datetime
    ) -> float:
        """Calculate average resource utilization."""
        cursor.execute(
            """
            SELECT AVG(value) FROM metrics
            WHERE metric_name = 'cpu_usage' AND timestamp >= ?
        """,
            (start_time,),
        )

        result = cursor.fetchone()
        return result[0] or 0.0

    def _calculate_health_score(self, metrics: EvaluationMetrics) -> float:
        """Calculate overall system health score (0-100)."""
        # Weight different metrics based on importance
        weights = {
            "fix_success_rate": 0.25,
            "user_satisfaction_score": 0.20,
            "uptime": 0.15,
            "test_pass_rate": 0.15,
            "security_score": 0.10,
            "code_quality_score": 0.10,
            "error_rate": -0.05,  # Negative weight for error rate
        }

        score = 0.0
        for metric, weight in weights.items():
            value = getattr(metrics, metric, 0.0)
            if metric == "user_satisfaction_score":
                value /= 5.0  # Normalize to 0-1 scale
            elif metric == "error_rate":
                value = 1.0 - value  # Invert error rate

            score += value * weight

        return min(max(score * 100, 0), 100)  # Clamp to 0-100

    def _generate_recommendations(
        self, metrics: EvaluationMetrics, trends: dict[str, Any]
    ) -> list[str]:
        """Generate actionable recommendations based on metrics."""
        recommendations = []

        # Fix success rate recommendations
        if metrics.fix_success_rate < 0.8:
            recommendations.append("Consider improving fix success rate by enhancing quality gates")

        # User satisfaction recommendations
        if metrics.user_satisfaction_score < 3.5:
            recommendations.append("User satisfaction is low - review comment handling strategies")

        # Response time recommendations
        if metrics.avg_response_time > 5.0:
            recommendations.append(
                "Response time is high - consider using faster LLM providers or caching"
            )

        # Error rate recommendations
        if metrics.error_rate > 0.1:
            recommendations.append("Error rate is elevated - investigate system stability issues")

        # Trend-based recommendations
        for metric, trend_data in trends.items():
            if trend_data["trend"] == "declining":
                recommendations.append(f"{metric} is declining - requires attention")

        return recommendations


# Convenience function for easy metrics collection
def collect_autopr_metrics() -> "MetricsCollector":
    """Convenient function to get the global metrics collector."""
    return MetricsCollector()
