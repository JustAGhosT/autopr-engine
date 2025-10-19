#!/usr/bin/env python3
"""
Comprehensive tests for metrics collector module.
"""

from datetime import datetime, timedelta
import json
import os
import tempfile

import pytest


# Import the modules we're testing
try:
    from autopr.quality.metrics_collector import (
        EvaluationMetrics,
        MetricPoint,
        MetricsCollector,
        PerformanceMetrics,
    )
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestMetricPoint:
    """Test MetricPoint class."""

    def test_metric_point_initialization(self):
        """Test MetricPoint initialization."""
        timestamp = datetime.now()
        metric_point = MetricPoint(
            name="test_metric",
            value=42.5,
            timestamp=timestamp,
            tags={"tag1": "value1", "tag2": "value2"}
        )

        assert metric_point.name == "test_metric"
        assert metric_point.value == 42.5
        assert metric_point.timestamp == timestamp
        assert metric_point.tags == {"tag1": "value1", "tag2": "value2"}

    def test_metric_point_to_dict(self):
        """Test MetricPoint to_dict method."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        metric_point = MetricPoint(
            name="test_metric",
            value=100.0,
            timestamp=timestamp,
            tags={"environment": "test"}
        )

        result = metric_point.to_dict()
        expected = {
            "name": "test_metric",
            "value": 100.0,
            "timestamp": timestamp.isoformat(),
            "tags": {"environment": "test"}
        }
        assert result == expected

    def test_metric_point_from_dict(self):
        """Test MetricPoint from_dict method."""
        data = {
            "name": "test_metric",
            "value": 75.5,
            "timestamp": "2023-01-01T12:00:00",
            "tags": {"service": "api"}
        }

        metric_point = MetricPoint.from_dict(data)
        assert metric_point.name == "test_metric"
        assert metric_point.value == 75.5
        assert metric_point.timestamp == datetime.fromisoformat("2023-01-01T12:00:00")
        assert metric_point.tags == {"service": "api"}


class TestEvaluationMetrics:
    """Test EvaluationMetrics class."""

    def test_evaluation_metrics_initialization(self):
        """Test EvaluationMetrics initialization."""
        metrics = EvaluationMetrics()

        assert metrics.success_rate == 0.0
        assert metrics.total_fixes == 0
        assert metrics.successful_fixes == 0
        assert metrics.failed_fixes == 0
        assert metrics.average_fix_time == 0.0
        assert metrics.fix_times == []

    def test_evaluation_metrics_record_fix(self):
        """Test recording a fix."""
        metrics = EvaluationMetrics()

        # Record successful fix
        metrics.record_fix(success=True, fix_time=1.5)
        assert metrics.total_fixes == 1
        assert metrics.successful_fixes == 1
        assert metrics.failed_fixes == 0
        assert metrics.success_rate == 1.0
        assert metrics.average_fix_time == 1.5
        assert metrics.fix_times == [1.5]

        # Record failed fix
        metrics.record_fix(success=False, fix_time=2.0)
        assert metrics.total_fixes == 2
        assert metrics.successful_fixes == 1
        assert metrics.failed_fixes == 1
        assert metrics.success_rate == 0.5
        assert metrics.average_fix_time == 1.75
        assert metrics.fix_times == [1.5, 2.0]

    def test_evaluation_metrics_calculate_success_rate(self):
        """Test success rate calculation."""
        metrics = EvaluationMetrics()

        # No fixes
        assert metrics.calculate_success_rate() == 0.0

        # All successful
        metrics.record_fix(success=True, fix_time=1.0)
        metrics.record_fix(success=True, fix_time=1.0)
        assert metrics.calculate_success_rate() == 1.0

        # Mixed results
        metrics.record_fix(success=False, fix_time=1.0)
        assert metrics.calculate_success_rate() == 2/3

    def test_evaluation_metrics_to_dict(self):
        """Test EvaluationMetrics to_dict method."""
        metrics = EvaluationMetrics()
        metrics.record_fix(success=True, fix_time=1.0)
        metrics.record_fix(success=False, fix_time=2.0)

        result = metrics.to_dict()
        expected = {
            "success_rate": 0.5,
            "total_fixes": 2,
            "successful_fixes": 1,
            "failed_fixes": 1,
            "average_fix_time": 1.5,
            "fix_times": [1.0, 2.0]
        }
        assert result == expected


class TestPerformanceMetrics:
    """Test PerformanceMetrics class."""

    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics()

        assert metrics.total_processing_time == 0.0
        assert metrics.average_response_time == 0.0
        assert metrics.response_times == []
        assert metrics.memory_usage == 0.0
        assert metrics.cpu_usage == 0.0

    def test_performance_metrics_record_response_time(self):
        """Test recording response time."""
        metrics = PerformanceMetrics()

        metrics.record_response_time(1.5)
        assert metrics.response_times == [1.5]
        assert metrics.average_response_time == 1.5

        metrics.record_response_time(2.5)
        assert metrics.response_times == [1.5, 2.5]
        assert metrics.average_response_time == 2.0

    def test_performance_metrics_update_system_metrics(self):
        """Test updating system metrics."""
        metrics = PerformanceMetrics()

        metrics.update_system_metrics(memory_usage=512.0, cpu_usage=25.5)
        assert metrics.memory_usage == 512.0
        assert metrics.cpu_usage == 25.5

    def test_performance_metrics_to_dict(self):
        """Test PerformanceMetrics to_dict method."""
        metrics = PerformanceMetrics()
        metrics.record_response_time(1.0)
        metrics.record_response_time(2.0)
        metrics.update_system_metrics(memory_usage=256.0, cpu_usage=15.0)

        result = metrics.to_dict()
        expected = {
            "total_processing_time": 0.0,
            "average_response_time": 1.5,
            "response_times": [1.0, 2.0],
            "memory_usage": 256.0,
            "cpu_usage": 15.0
        }
        assert result == expected


class TestMetricsCollector:
    """Test MetricsCollector class."""

    @pytest.fixture
    def metrics_collector(self):
        """Create a MetricsCollector instance for testing."""
        return MetricsCollector()

    def test_metrics_collector_initialization(self, metrics_collector):
        """Test MetricsCollector initialization."""
        assert metrics_collector.evaluation_metrics is not None
        assert metrics_collector.performance_metrics is not None
        assert metrics_collector.events == []
        assert metrics_collector.feedback == []
        assert metrics_collector.benchmarks == []

    def test_record_metric(self, metrics_collector):
        """Test recording a metric."""
        timestamp = datetime.now()
        metrics_collector.record_metric(
            name="test_metric",
            value=42.0,
            timestamp=timestamp,
            tags={"test": "value"}
        )

        assert len(metrics_collector.events) == 1
        event = metrics_collector.events[0]
        assert event.name == "test_metric"
        assert event.value == 42.0
        assert event.timestamp == timestamp
        assert event.tags == {"test": "value"}

    def test_record_event(self, metrics_collector):
        """Test recording an event."""
        metrics_collector.record_event("test_event", {"data": "value"})

        assert len(metrics_collector.events) == 1
        event = metrics_collector.events[0]
        assert event.name == "test_event"
        assert event.tags == {"data": "value"}

    def test_record_feedback(self, metrics_collector):
        """Test recording feedback."""
        feedback_data = {
            "rating": 5,
            "comment": "Great fix!",
            "user_id": "user123"
        }
        metrics_collector.record_feedback(feedback_data)

        assert len(metrics_collector.feedback) == 1
        assert metrics_collector.feedback[0] == feedback_data

    def test_record_benchmark(self, metrics_collector):
        """Test recording a benchmark."""
        benchmark_data = {
            "name": "performance_test",
            "duration": 1.5,
            "memory_usage": 256.0
        }
        metrics_collector.record_benchmark(benchmark_data)

        assert len(metrics_collector.benchmarks) == 1
        assert metrics_collector.benchmarks[0] == benchmark_data

    def test_generate_summary(self, metrics_collector):
        """Test generating a summary."""
        # Add some test data
        metrics_collector.evaluation_metrics.record_fix(success=True, fix_time=1.0)
        metrics_collector.evaluation_metrics.record_fix(success=False, fix_time=2.0)
        metrics_collector.performance_metrics.record_response_time(1.5)
        metrics_collector.record_event("test_event", {"data": "value"})

        summary = metrics_collector.generate_summary()

        assert "evaluation_metrics" in summary
        assert "performance_metrics" in summary
        assert "total_events" in summary
        assert "total_feedback" in summary
        assert "total_benchmarks" in summary
        assert summary["total_events"] == 1
        assert summary["total_feedback"] == 0
        assert summary["total_benchmarks"] == 0

    def test_generate_report(self, metrics_collector):
        """Test generating a detailed report."""
        # Add test data
        metrics_collector.evaluation_metrics.record_fix(success=True, fix_time=1.0)
        metrics_collector.performance_metrics.record_response_time(1.5)
        metrics_collector.record_event("test_event", {"data": "value"})

        report = metrics_collector.generate_report()

        assert "summary" in report
        assert "events" in report
        assert "feedback" in report
        assert "benchmarks" in report
        assert "timestamp" in report

    def test_save_metrics_to_file(self, metrics_collector):
        """Test saving metrics to file."""
        # Add test data
        metrics_collector.record_metric("test_metric", 42.0)
        metrics_collector.record_event("test_event", {"data": "value"})

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name

        try:
            metrics_collector.save_metrics_to_file(temp_file)

            # Verify file was created and contains data
            assert os.path.exists(temp_file)
            with open(temp_file) as f:
                data = json.load(f)

            assert "events" in data
            assert "summary" in data
            assert len(data["events"]) == 2  # metric + event

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_load_metrics_from_file(self, metrics_collector):
        """Test loading metrics from file."""
        test_data = {
            "events": [
                {
                    "name": "test_metric",
                    "value": 42.0,
                    "timestamp": datetime.now().isoformat(),
                    "tags": {"test": "value"}
                }
            ],
            "summary": {
                "total_events": 1,
                "total_feedback": 0,
                "total_benchmarks": 0
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(test_data, f)
            temp_file = f.name

        try:
            loaded_collector = MetricsCollector.load_metrics_from_file(temp_file)

            assert len(loaded_collector.events) == 1
            assert loaded_collector.events[0].name == "test_metric"
            assert loaded_collector.events[0].value == 42.0

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_calculate_performance_metrics(self, metrics_collector):
        """Test calculating performance metrics."""
        # Add test data
        metrics_collector.performance_metrics.record_response_time(1.0)
        metrics_collector.performance_metrics.record_response_time(2.0)
        metrics_collector.performance_metrics.record_response_time(3.0)

        performance = metrics_collector.calculate_performance_metrics()

        assert performance["average_response_time"] == 2.0
        assert performance["min_response_time"] == 1.0
        assert performance["max_response_time"] == 3.0
        assert performance["total_responses"] == 3

    def test_get_metrics_by_time_range(self, metrics_collector):
        """Test getting metrics by time range."""
        now = datetime.now()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        # Add metrics with different timestamps
        metrics_collector.record_metric("metric1", 1.0, timestamp=past)
        metrics_collector.record_metric("metric2", 2.0, timestamp=now)
        metrics_collector.record_metric("metric3", 3.0, timestamp=future)

        # Get metrics for the last hour
        recent_metrics = metrics_collector.get_metrics_by_time_range(
            start_time=past, end_time=now
        )

        assert len(recent_metrics) == 2  # metric1 and metric2
        assert any(m.name == "metric1" for m in recent_metrics)
        assert any(m.name == "metric2" for m in recent_metrics)
        assert not any(m.name == "metric3" for m in recent_metrics)
