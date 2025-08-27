"""
Comprehensive tests for Metrics Collector module.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add the parent directory to sys.path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from autopr.actions.ai_linting_fixer.metrics import (EvaluationMetrics,
                                                         MetricPoint,
                                                         MetricsCollector,
                                                         PerformanceMetrics)
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestMetricPoint:
    """Comprehensive tests for MetricPoint class."""

    def test_metric_point_initialization(self):
        """Test MetricPoint initialization."""
        timestamp = datetime.now()
        metric_point = MetricPoint(
            name="test_metric",
            value=100.0,
            timestamp=timestamp,
            metadata={"source": "test"}
        )
        
        assert metric_point.name == "test_metric"
        assert metric_point.value == 100.0
        assert metric_point.timestamp == timestamp
        assert metric_point.metadata == {"source": "test"}

    def test_metric_point_default_metadata(self):
        """Test MetricPoint initialization with default metadata."""
        metric_point = MetricPoint(
            name="test_metric",
            value=100.0,
            timestamp=datetime.now()
        )
        
        assert metric_point.metadata == {}

    def test_metric_point_equality(self):
        """Test MetricPoint equality."""
        timestamp = datetime.now()
        point1 = MetricPoint("test", 100.0, timestamp)
        point2 = MetricPoint("test", 100.0, timestamp)
        point3 = MetricPoint("test", 200.0, timestamp)
        
        assert point1 == point2
        assert point1 != point3


class TestEvaluationMetrics:
    """Comprehensive tests for EvaluationMetrics class."""

    def test_evaluation_metrics_initialization(self):
        """Test EvaluationMetrics initialization."""
        metrics = EvaluationMetrics(
            fix_success_rate=0.85,
            classification_accuracy=0.92,
            false_positive_rate=0.08,
            user_satisfaction=4.5,
            avg_response_time=1.2,
            avg_resolution_time=5.0,
            api_cost=0.15,
            coverage_rate=0.78,
            code_quality_score=8.5,
            test_pass_rate=0.95,
            security_score=9.0,
            maintainability_index=7.8,
            uptime=99.9,
            error_rate=0.01,
            throughput=150.0,
            resource_utilization=0.75,
            health_score=8.8
        )
        
        assert metrics.fix_success_rate == 0.85
        assert metrics.classification_accuracy == 0.92
        assert metrics.false_positive_rate == 0.08
        assert metrics.user_satisfaction == 4.5
        assert metrics.avg_response_time == 1.2
        assert metrics.avg_resolution_time == 5.0
        assert metrics.api_cost == 0.15
        assert metrics.coverage_rate == 0.78
        assert metrics.code_quality_score == 8.5
        assert metrics.test_pass_rate == 0.95
        assert metrics.security_score == 9.0
        assert metrics.maintainability_index == 7.8
        assert metrics.uptime == 99.9
        assert metrics.error_rate == 0.01
        assert metrics.throughput == 150.0
        assert metrics.resource_utilization == 0.75
        assert metrics.health_score == 8.8


class TestPerformanceMetrics:
    """Comprehensive tests for PerformanceMetrics class."""

    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics(
            total_duration=120.5,
            flake8_duration=10.2,
            ai_processing_duration=45.8,
            file_io_duration=5.1,
            files_per_second=2.5,
            issues_per_second=1.8,
            tokens_per_second=50.0,
            total_files_processed=100,
            total_issues_found=180,
            total_issues_fixed=150,
            total_tokens_used=6000,
            average_file_size=2.5,
            success_rate=0.83,
            average_confidence_score=0.78,
            fix_acceptance_rate=0.92,
            api_calls_made=200,
            average_api_response_time=1.5,
            api_error_rate=0.02,
            workers_used=4,
            parallel_efficiency=0.85,
            queue_wait_time=0.5
        )
        
        assert metrics.total_duration == 120.5
        assert metrics.flake8_duration == 10.2
        assert metrics.ai_processing_duration == 45.8
        assert metrics.file_io_duration == 5.1
        assert metrics.files_per_second == 2.5
        assert metrics.issues_per_second == 1.8
        assert metrics.tokens_per_second == 50.0
        assert metrics.total_files_processed == 100
        assert metrics.total_issues_found == 180
        assert metrics.total_issues_fixed == 150
        assert metrics.total_tokens_used == 6000
        assert metrics.average_file_size == 2.5
        assert metrics.success_rate == 0.83
        assert metrics.average_confidence_score == 0.78
        assert metrics.fix_acceptance_rate == 0.92
        assert metrics.api_calls_made == 200
        assert metrics.average_api_response_time == 1.5
        assert metrics.api_error_rate == 0.02
        assert metrics.workers_used == 4
        assert metrics.parallel_efficiency == 0.85
        assert metrics.queue_wait_time == 0.5


class TestMetricsCollector:
    """Comprehensive tests for MetricsCollector class."""

    @pytest.fixture
    def metrics_collector(self):
        """Create a MetricsCollector instance for testing."""
        return MetricsCollector()

    def test_initialization(self, metrics_collector):
        """Test MetricsCollector initialization."""
        assert metrics_collector.session_metrics is not None
        assert metrics_collector.file_metrics is not None
        assert metrics_collector.agent_metrics is not None
        assert metrics_collector.performance_metrics is not None

    def test_record_metric(self, metrics_collector):
        """Test record_metric method."""
        metrics_collector.record_metric("test_metric", 100.0, {"source": "test"})
        
        # Check that metric was recorded
        assert len(metrics_collector.session_metrics.metrics) == 1
        metric = metrics_collector.session_metrics.metrics[0]
        assert metric.name == "test_metric"
        assert metric.value == 100.0
        assert metric.metadata == {"source": "test"}

    def test_record_event(self, metrics_collector):
        """Test record_event method."""
        metrics_collector.record_event("test_event", {"details": "test"})
        
        # Check that event was recorded
        assert len(metrics_collector.session_metrics.events) == 1
        event = metrics_collector.session_metrics.events[0]
        assert event.name == "test_event"
        assert event.metadata == {"details": "test"}

    def test_record_user_feedback(self, metrics_collector):
        """Test record_user_feedback method."""
        metrics_collector.record_user_feedback("test_feedback", 5, "Great job!")
        
        # Check that feedback was recorded
        assert len(metrics_collector.session_metrics.user_feedback) == 1
        feedback = metrics_collector.session_metrics.user_feedback[0]
        assert feedback.feedback_type == "test_feedback"
        assert feedback.rating == 5
        assert feedback.comment == "Great job!"

    def test_record_benchmark(self, metrics_collector):
        """Test record_benchmark method."""
        metrics_collector.record_benchmark("test_benchmark", 1.5, {"baseline": 2.0})
        
        # Check that benchmark was recorded
        assert len(metrics_collector.session_metrics.benchmarks) == 1
        benchmark = metrics_collector.session_metrics.benchmarks[0]
        assert benchmark.name == "test_benchmark"
        assert benchmark.value == 1.5
        assert benchmark.metadata == {"baseline": 2.0}

    def test_get_metrics_summary(self, metrics_collector):
        """Test get_metrics_summary method."""
        # Add some test data
        metrics_collector.record_metric("test_metric", 100.0)
        metrics_collector.record_metric("test_metric", 200.0)
        
        summary = metrics_collector.get_metrics_summary()
        
        assert "test_metric" in summary
        assert summary["test_metric"]["count"] == 2
        assert summary["test_metric"]["average"] == 150.0

    def test_get_benchmark_results(self, metrics_collector):
        """Test get_benchmark_results method."""
        # Add some test benchmarks
        metrics_collector.record_benchmark("test_benchmark", 1.5, {"baseline": 2.0})
        metrics_collector.record_benchmark("test_benchmark", 1.8, {"baseline": 2.0})
        
        results = metrics_collector.get_benchmark_results()
        
        assert "test_benchmark" in results
        assert results["test_benchmark"]["count"] == 2
        assert results["test_benchmark"]["average"] == 1.65

    def test_get_trend_analysis(self, metrics_collector):
        """Test get_trend_analysis method."""
        # Add metrics over time
        base_time = datetime.now()
        metrics_collector.record_metric("test_metric", 100.0, {"timestamp": base_time})
        metrics_collector.record_metric("test_metric", 110.0, {"timestamp": base_time + timedelta(hours=1)})
        metrics_collector.record_metric("test_metric", 120.0, {"timestamp": base_time + timedelta(hours=2)})
        
        trends = metrics_collector.get_trend_analysis()
        
        assert "test_metric" in trends
        assert trends["test_metric"]["trend"] == "increasing"

    def test_generate_report(self, metrics_collector):
        """Test generate_report method."""
        # Add some test data
        metrics_collector.record_metric("test_metric", 100.0)
        metrics_collector.record_event("test_event", {"details": "test"})
        
        report = metrics_collector.generate_report()
        
        assert "metrics_summary" in report
        assert "performance_metrics" in report
        assert "trends" in report
        assert "recommendations" in report

    def test_calculate_performance_metrics(self, metrics_collector):
        """Test calculate_performance_metrics method."""
        # Add some test data
        metrics_collector.session_metrics.total_files = 100
        metrics_collector.session_metrics.total_issues = 180
        metrics_collector.session_metrics.successful_fixes = 150
        metrics_collector.session_metrics.total_tokens = 6000
        metrics_collector.session_metrics.api_calls = 200
        
        performance_metrics = metrics_collector.calculate_performance_metrics()
        
        assert performance_metrics.total_files_processed == 100
        assert performance_metrics.total_issues_found == 180
        assert performance_metrics.total_issues_fixed == 150
        assert performance_metrics.total_tokens_used == 6000
        assert performance_metrics.api_calls_made == 200

    def test_reset_metrics(self, metrics_collector):
        """Test reset_metrics method."""
        # Add some test data
        metrics_collector.record_metric("test_metric", 100.0)
        metrics_collector.record_event("test_event", {"details": "test"})
        
        # Reset metrics
        metrics_collector.reset_metrics()
        
        # Check that metrics were reset
        assert len(metrics_collector.session_metrics.metrics) == 0
        assert len(metrics_collector.session_metrics.events) == 0


if __name__ == "__main__":
    pytest.main([__file__])
