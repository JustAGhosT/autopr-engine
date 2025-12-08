#!/usr/bin/env python3
"""
Comprehensive tests for performance tracker module.
"""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the modules we're testing
try:
    from codeflow_engine.actions.performance_tracker import (PerformanceAnalyzer,
                                                    PerformanceConfig,
                                                    PerformanceMetrics,
                                                    PerformanceMonitor,
                                                    PerformanceReporter,
                                                    PerformanceTracker)
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestPerformanceMetrics:
    """Test PerformanceMetrics class."""

    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics(
            operation_name="test_operation",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=1),
            duration=1.0,
            memory_usage=1024,
            cpu_usage=50.0,
            success=True,
            error_message=None
        )
        
        assert metrics.operation_name == "test_operation"
        assert metrics.duration == 1.0
        assert metrics.memory_usage == 1024
        assert metrics.cpu_usage == 50.0
        assert metrics.success is True
        assert metrics.error_message is None

    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics with default values."""
        start_time = datetime.now()
        metrics = PerformanceMetrics(
            operation_name="test_operation",
            start_time=start_time,
            end_time=start_time + timedelta(seconds=0.5)
        )
        
        assert metrics.operation_name == "test_operation"
        assert metrics.duration == 0.5
        assert metrics.memory_usage == 0
        assert metrics.cpu_usage == 0.0
        assert metrics.success is True
        assert metrics.error_message is None

    def test_performance_metrics_with_error(self):
        """Test PerformanceMetrics with error."""
        start_time = datetime.now()
        metrics = PerformanceMetrics(
            operation_name="test_operation",
            start_time=start_time,
            end_time=start_time + timedelta(seconds=1),
            success=False,
            error_message="Test error occurred"
        )
        
        assert metrics.success is False
        assert metrics.error_message == "Test error occurred"

    def test_performance_metrics_to_dict(self):
        """Test PerformanceMetrics to_dict method."""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=1.5)
        
        metrics = PerformanceMetrics(
            operation_name="test_operation",
            start_time=start_time,
            end_time=end_time,
            duration=1.5,
            memory_usage=2048,
            cpu_usage=75.0,
            success=True
        )
        
        result = metrics.to_dict()
        assert result["operation_name"] == "test_operation"
        assert result["duration"] == 1.5
        assert result["memory_usage"] == 2048
        assert result["cpu_usage"] == 75.0
        assert result["success"] is True

    def test_performance_metrics_from_dict(self):
        """Test PerformanceMetrics from_dict method."""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=2.0)
        
        data = {
            "operation_name": "test_operation",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": 2.0,
            "memory_usage": 3072,
            "cpu_usage": 25.0,
            "success": True,
            "error_message": None
        }
        
        metrics = PerformanceMetrics.from_dict(data)
        assert metrics.operation_name == "test_operation"
        assert metrics.duration == 2.0
        assert metrics.memory_usage == 3072
        assert metrics.cpu_usage == 25.0
        assert metrics.success is True

    def test_performance_metrics_calculate_duration(self):
        """Test automatic duration calculation."""
        start_time = datetime.now()
        time.sleep(0.1)  # Small delay
        end_time = datetime.now()
        
        metrics = PerformanceMetrics(
            operation_name="test_operation",
            start_time=start_time,
            end_time=end_time
        )
        
        assert metrics.duration > 0
        assert metrics.duration < 1.0  # Should be small


class TestPerformanceConfig:
    """Test PerformanceConfig class."""

    def test_performance_config_initialization(self):
        """Test PerformanceConfig initialization."""
        config = PerformanceConfig(
            enabled=True,
            track_memory=True,
            track_cpu=True,
            track_disk=True,
            track_network=True,
            sampling_interval=0.1,
            max_history_size=1000,
            save_to_file=True,
            file_path="performance.log"
        )
        
        assert config.enabled is True
        assert config.track_memory is True
        assert config.track_cpu is True
        assert config.track_disk is True
        assert config.track_network is True
        assert config.sampling_interval == 0.1
        assert config.max_history_size == 1000
        assert config.save_to_file is True
        assert config.file_path == "performance.log"

    def test_performance_config_defaults(self):
        """Test PerformanceConfig with default values."""
        config = PerformanceConfig()
        
        assert config.enabled is True
        assert config.track_memory is True
        assert config.track_cpu is True
        assert config.track_disk is False
        assert config.track_network is False
        assert config.sampling_interval == 0.5
        assert config.max_history_size == 100
        assert config.save_to_file is False
        assert config.file_path == "performance_metrics.json"

    def test_performance_config_to_dict(self):
        """Test PerformanceConfig to_dict method."""
        config = PerformanceConfig(
            enabled=True,
            track_memory=True,
            track_cpu=False,
            sampling_interval=0.2,
            max_history_size=500
        )
        
        result = config.to_dict()
        assert result["enabled"] is True
        assert result["track_memory"] is True
        assert result["track_cpu"] is False
        assert result["sampling_interval"] == 0.2
        assert result["max_history_size"] == 500

    def test_performance_config_from_dict(self):
        """Test PerformanceConfig from_dict method."""
        data = {
            "enabled": False,
            "track_memory": True,
            "track_cpu": True,
            "track_disk": False,
            "track_network": True,
            "sampling_interval": 0.3,
            "max_history_size": 200,
            "save_to_file": True,
            "file_path": "custom_performance.log"
        }
        
        config = PerformanceConfig.from_dict(data)
        assert config.enabled is False
        assert config.track_memory is True
        assert config.track_cpu is True
        assert config.track_disk is False
        assert config.track_network is True
        assert config.sampling_interval == 0.3
        assert config.max_history_size == 200
        assert config.save_to_file is True
        assert config.file_path == "custom_performance.log"


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""

    @pytest.fixture
    def performance_monitor(self):
        """Create a PerformanceMonitor instance for testing."""
        config = PerformanceConfig(enabled=True, track_memory=True, track_cpu=True)
        return PerformanceMonitor(config)

    def test_performance_monitor_initialization(self, performance_monitor):
        """Test PerformanceMonitor initialization."""
        assert performance_monitor.config is not None
        assert performance_monitor.metrics_history == []
        assert performance_monitor.is_monitoring is False

    def test_start_monitoring(self, performance_monitor):
        """Test starting performance monitoring."""
        performance_monitor.start_monitoring()
        assert performance_monitor.is_monitoring is True
        assert performance_monitor.start_time is not None

    def test_stop_monitoring(self, performance_monitor):
        """Test stopping performance monitoring."""
        performance_monitor.start_monitoring()
        time.sleep(0.1)  # Small delay
        performance_monitor.stop_monitoring()
        
        assert performance_monitor.is_monitoring is False
        assert len(performance_monitor.metrics_history) > 0

    def test_record_metric(self, performance_monitor):
        """Test recording a performance metric."""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=1)
        
        metric = PerformanceMetrics(
            operation_name="test_operation",
            start_time=start_time,
            end_time=end_time,
            duration=1.0,
            memory_usage=1024,
            cpu_usage=50.0,
            success=True
        )
        
        performance_monitor.record_metric(metric)
        assert len(performance_monitor.metrics_history) == 1
        assert performance_monitor.metrics_history[0] == metric

    def test_get_current_metrics(self, performance_monitor):
        """Test getting current system metrics."""
        metrics = performance_monitor.get_current_metrics()
        
        assert "memory_usage" in metrics
        assert "cpu_usage" in metrics
        assert "timestamp" in metrics
        assert metrics["memory_usage"] >= 0
        assert metrics["cpu_usage"] >= 0

    def test_get_metrics_summary(self, performance_monitor):
        """Test getting metrics summary."""
        # Add some test metrics
        for i in range(5):
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=i + 1)
            
            metric = PerformanceMetrics(
                operation_name=f"operation_{i}",
                start_time=start_time,
                end_time=end_time,
                duration=i + 1,
                memory_usage=1024 * (i + 1),
                cpu_usage=10.0 * (i + 1),
                success=True
            )
            performance_monitor.record_metric(metric)
        
        summary = performance_monitor.get_metrics_summary()
        
        assert "total_operations" in summary
        assert "average_duration" in summary
        assert "total_memory_usage" in summary
        assert "average_cpu_usage" in summary
        assert summary["total_operations"] == 5

    def test_clear_history(self, performance_monitor):
        """Test clearing metrics history."""
        # Add some test metrics
        for i in range(3):
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=1)
            
            metric = PerformanceMetrics(
                operation_name=f"operation_{i}",
                start_time=start_time,
                end_time=end_time,
                duration=1.0,
                success=True
            )
            performance_monitor.record_metric(metric)
        
        assert len(performance_monitor.metrics_history) == 3
        
        performance_monitor.clear_history()
        assert len(performance_monitor.metrics_history) == 0


class TestPerformanceAnalyzer:
    """Test PerformanceAnalyzer class."""

    @pytest.fixture
    def performance_analyzer(self):
        """Create a PerformanceAnalyzer instance for testing."""
        return PerformanceAnalyzer()

    def test_performance_analyzer_initialization(self, performance_analyzer):
        """Test PerformanceAnalyzer initialization."""
        assert performance_analyzer.analysis_cache == {}
        assert performance_analyzer.analysis_rules == []

    def test_analyze_metrics(self, performance_analyzer):
        """Test analyzing performance metrics."""
        # Create test metrics
        metrics = []
        for i in range(10):
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=i + 1)
            
            metric = PerformanceMetrics(
                operation_name=f"operation_{i}",
                start_time=start_time,
                end_time=end_time,
                duration=i + 1,
                memory_usage=1024 * (i + 1),
                cpu_usage=10.0 * (i + 1),
                success=i < 8  # 8 successful, 2 failed
            )
            metrics.append(metric)
        
        analysis = performance_analyzer.analyze_metrics(metrics)
        
        assert "total_operations" in analysis
        assert "success_rate" in analysis
        assert "average_duration" in analysis
        assert "max_duration" in analysis
        assert "min_duration" in analysis
        assert "total_memory_usage" in analysis
        assert "average_cpu_usage" in analysis
        
        assert analysis["total_operations"] == 10
        assert analysis["success_rate"] == 0.8
        assert analysis["max_duration"] == 10.0
        assert analysis["min_duration"] == 1.0

    def test_detect_performance_issues(self, performance_analyzer):
        """Test detecting performance issues."""
        # Create metrics with potential issues
        metrics = []
        
        # Slow operation
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=10)
        slow_metric = PerformanceMetrics(
            operation_name="slow_operation",
            start_time=start_time,
            end_time=end_time,
            duration=10.0,
            memory_usage=10240,
            cpu_usage=90.0,
            success=True
        )
        metrics.append(slow_metric)
        
        # High memory usage
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=1)
        high_memory_metric = PerformanceMetrics(
            operation_name="high_memory_operation",
            start_time=start_time,
            end_time=end_time,
            duration=1.0,
            memory_usage=51200,  # 50MB
            cpu_usage=20.0,
            success=True
        )
        metrics.append(high_memory_metric)
        
        # Failed operation
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=1)
        failed_metric = PerformanceMetrics(
            operation_name="failed_operation",
            start_time=start_time,
            end_time=end_time,
            duration=1.0,
            memory_usage=1024,
            cpu_usage=10.0,
            success=False,
            error_message="Test error"
        )
        metrics.append(failed_metric)
        
        issues = performance_analyzer.detect_performance_issues(metrics)
        
        assert len(issues) > 0
        assert any("slow" in issue.lower() for issue in issues)
        assert any("memory" in issue.lower() for issue in issues)
        assert any("failed" in issue.lower() for issue in issues)

    def test_generate_recommendations(self, performance_analyzer):
        """Test generating performance recommendations."""
        # Create metrics with issues
        metrics = []
        for i in range(5):
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=5)  # All slow
            
            metric = PerformanceMetrics(
                operation_name=f"slow_operation_{i}",
                start_time=start_time,
                end_time=end_time,
                duration=5.0,
                memory_usage=2048,
                cpu_usage=80.0,
                success=True
            )
            metrics.append(metric)
        
        recommendations = performance_analyzer.generate_recommendations(metrics)
        
        assert len(recommendations) > 0
        assert any("optimize" in rec.lower() for rec in recommendations)
        assert any("performance" in rec.lower() for rec in recommendations)

    def test_calculate_performance_score(self, performance_analyzer):
        """Test calculating performance score."""
        # Create good metrics
        good_metrics = []
        for i in range(5):
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=0.1)  # Fast operations
            
            metric = PerformanceMetrics(
                operation_name=f"fast_operation_{i}",
                start_time=start_time,
                end_time=end_time,
                duration=0.1,
                memory_usage=512,
                cpu_usage=10.0,
                success=True
            )
            good_metrics.append(metric)
        
        score = performance_analyzer.calculate_performance_score(good_metrics)
        assert score >= 0.0
        assert score <= 1.0
        assert score > 0.7  # Should be high for good metrics

    def test_compare_performance(self, performance_analyzer):
        """Test comparing performance between different sets."""
        # Create baseline metrics
        baseline_metrics = []
        for i in range(3):
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=1)
            
            metric = PerformanceMetrics(
                operation_name=f"baseline_operation_{i}",
                start_time=start_time,
                end_time=end_time,
                duration=1.0,
                memory_usage=1024,
                cpu_usage=20.0,
                success=True
            )
            baseline_metrics.append(metric)
        
        # Create improved metrics
        improved_metrics = []
        for i in range(3):
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=0.5)  # Faster
            
            metric = PerformanceMetrics(
                operation_name=f"improved_operation_{i}",
                start_time=start_time,
                end_time=end_time,
                duration=0.5,
                memory_usage=512,  # Less memory
                cpu_usage=10.0,    # Less CPU
                success=True
            )
            improved_metrics.append(metric)
        
        comparison = performance_analyzer.compare_performance(
            baseline_metrics, improved_metrics
        )
        
        assert "duration_improvement" in comparison
        assert "memory_improvement" in comparison
        assert "cpu_improvement" in comparison
        assert comparison["duration_improvement"] > 0  # Should be positive (improvement)


class TestPerformanceReporter:
    """Test PerformanceReporter class."""

    @pytest.fixture
    def performance_reporter(self):
        """Create a PerformanceReporter instance for testing."""
        return PerformanceReporter()

    def test_performance_reporter_initialization(self, performance_reporter):
        """Test PerformanceReporter initialization."""
        assert performance_reporter.report_formats == {}
        assert performance_reporter.default_format == "json"

    def test_add_report_format(self, performance_reporter):
        """Test adding a custom report format."""
        def custom_format(metrics):
            return f"Custom report with {len(metrics)} metrics"
        
        performance_reporter.add_report_format("custom", custom_format)
        assert "custom" in performance_reporter.report_formats

    def test_generate_json_report(self, performance_reporter):
        """Test generating JSON report."""
        # Create test metrics
        metrics = []
        for i in range(3):
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=i + 1)
            
            metric = PerformanceMetrics(
                operation_name=f"operation_{i}",
                start_time=start_time,
                end_time=end_time,
                duration=i + 1,
                memory_usage=1024 * (i + 1),
                cpu_usage=10.0 * (i + 1),
                success=True
            )
            metrics.append(metric)
        
        report = performance_reporter.generate_report(metrics, "json")
        
        # Parse JSON to verify structure
        report_data = json.loads(report)
        assert "summary" in report_data
        assert "metrics" in report_data
        assert len(report_data["metrics"]) == 3

    def test_generate_text_report(self, performance_reporter):
        """Test generating text report."""
        # Create test metrics
        metrics = []
        for i in range(2):
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=i + 1)
            
            metric = PerformanceMetrics(
                operation_name=f"operation_{i}",
                start_time=start_time,
                end_time=end_time,
                duration=i + 1,
                memory_usage=1024 * (i + 1),
                cpu_usage=10.0 * (i + 1),
                success=True
            )
            metrics.append(metric)
        
        report = performance_reporter.generate_report(metrics, "text")
        
        assert isinstance(report, str)
        assert "Performance Report" in report
        assert "operation_0" in report
        assert "operation_1" in report

    def test_generate_html_report(self, performance_reporter):
        """Test generating HTML report."""
        # Create test metrics
        metrics = []
        for i in range(2):
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=i + 1)
            
            metric = PerformanceMetrics(
                operation_name=f"operation_{i}",
                start_time=start_time,
                end_time=end_time,
                duration=i + 1,
                memory_usage=1024 * (i + 1),
                cpu_usage=10.0 * (i + 1),
                success=True
            )
            metrics.append(metric)
        
        report = performance_reporter.generate_report(metrics, "html")
        
        assert isinstance(report, str)
        assert "<html>" in report
        assert "<head>" in report
        assert "<body>" in report
        assert "Performance Report" in report

    def test_save_report_to_file(self, performance_reporter):
        """Test saving report to file."""
        # Create test metrics
        metrics = []
        for i in range(2):
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=i + 1)
            
            metric = PerformanceMetrics(
                operation_name=f"operation_{i}",
                start_time=start_time,
                end_time=end_time,
                duration=i + 1,
                memory_usage=1024 * (i + 1),
                cpu_usage=10.0 * (i + 1),
                success=True
            )
            metrics.append(metric)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            result = performance_reporter.save_report_to_file(
                metrics, temp_file, "json"
            )
            assert result is True
            assert os.path.exists(temp_file)
            
            # Verify file content
            with open(temp_file, 'r') as f:
                content = f.read()
                report_data = json.loads(content)
                assert "summary" in report_data
                assert "metrics" in report_data
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_generate_summary_report(self, performance_reporter):
        """Test generating summary report."""
        # Create test metrics
        metrics = []
        for i in range(5):
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=i + 1)
            
            metric = PerformanceMetrics(
                operation_name=f"operation_{i}",
                start_time=start_time,
                end_time=end_time,
                duration=i + 1,
                memory_usage=1024 * (i + 1),
                cpu_usage=10.0 * (i + 1),
                success=i < 4  # 4 successful, 1 failed
            )
            metrics.append(metric)
        
        summary = performance_reporter.generate_summary_report(metrics)
        
        assert "total_operations" in summary
        assert "successful_operations" in summary
        assert "failed_operations" in summary
        assert "success_rate" in summary
        assert "average_duration" in summary
        assert "total_memory_usage" in summary
        assert "average_cpu_usage" in summary
        
        assert summary["total_operations"] == 5
        assert summary["successful_operations"] == 4
        assert summary["failed_operations"] == 1
        assert summary["success_rate"] == 0.8


class TestPerformanceTracker:
    """Test PerformanceTracker class."""

    @pytest.fixture
    def performance_tracker(self):
        """Create a PerformanceTracker instance for testing."""
        config = PerformanceConfig(enabled=True, track_memory=True, track_cpu=True)
        return PerformanceTracker(config)

    def test_performance_tracker_initialization(self, performance_tracker):
        """Test PerformanceTracker initialization."""
        assert performance_tracker.config is not None
        assert performance_tracker.monitor is not None
        assert performance_tracker.analyzer is not None
        assert performance_tracker.reporter is not None

    def test_start_tracking(self, performance_tracker):
        """Test starting performance tracking."""
        performance_tracker.start_tracking("test_operation")
        assert performance_tracker.monitor.is_monitoring is True
        assert performance_tracker.current_operation == "test_operation"

    def test_stop_tracking(self, performance_tracker):
        """Test stopping performance tracking."""
        performance_tracker.start_tracking("test_operation")
        time.sleep(0.1)  # Small delay
        
        metric = performance_tracker.stop_tracking()
        
        assert performance_tracker.monitor.is_monitoring is False
        assert metric.operation_name == "test_operation"
        assert metric.duration > 0
        assert metric.success is True

    def test_track_operation_decorator(self, performance_tracker):
        """Test tracking operation with decorator."""
        @performance_tracker.track_operation
        def test_function():
            time.sleep(0.1)
            return "success"
        
        result = test_function()
        
        assert result == "success"
        assert len(performance_tracker.monitor.metrics_history) == 1
        
        metric = performance_tracker.monitor.metrics_history[0]
        assert metric.operation_name == "test_function"
        assert metric.duration > 0
        assert metric.success is True

    def test_track_operation_context_manager(self, performance_tracker):
        """Test tracking operation with context manager."""
        with performance_tracker.track_operation("context_test"):
            time.sleep(0.1)
        
        assert len(performance_tracker.monitor.metrics_history) == 1
        
        metric = performance_tracker.monitor.metrics_history[0]
        assert metric.operation_name == "context_test"
        assert metric.duration > 0
        assert metric.success is True

    def test_track_operation_with_error(self, performance_tracker):
        """Test tracking operation that raises an error."""
        @performance_tracker.track_operation
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        assert len(performance_tracker.monitor.metrics_history) == 1
        
        metric = performance_tracker.monitor.metrics_history[0]
        assert metric.operation_name == "failing_function"
        assert metric.success is False
        assert "Test error" in metric.error_message

    def test_get_performance_summary(self, performance_tracker):
        """Test getting performance summary."""
        # Track some operations
        for i in range(3):
            with performance_tracker.track_operation(f"operation_{i}"):
                time.sleep(0.1)
        
        summary = performance_tracker.get_performance_summary()
        
        assert "total_operations" in summary
        assert "average_duration" in summary
        assert "success_rate" in summary
        assert summary["total_operations"] == 3
        assert summary["success_rate"] == 1.0

    def test_generate_performance_report(self, performance_tracker):
        """Test generating performance report."""
        # Track some operations
        for i in range(2):
            with performance_tracker.track_operation(f"operation_{i}"):
                time.sleep(0.1)
        
        report = performance_tracker.generate_performance_report("json")
        
        # Parse JSON to verify structure
        report_data = json.loads(report)
        assert "summary" in report_data
        assert "metrics" in report_data
        assert len(report_data["metrics"]) == 2

    def test_save_performance_report(self, performance_tracker):
        """Test saving performance report to file."""
        # Track some operations
        for i in range(2):
            with performance_tracker.track_operation(f"operation_{i}"):
                time.sleep(0.1)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            result = performance_tracker.save_performance_report(temp_file, "json")
            assert result is True
            assert os.path.exists(temp_file)
            
            # Verify file content
            with open(temp_file, 'r') as f:
                content = f.read()
                report_data = json.loads(content)
                assert "summary" in report_data
                assert "metrics" in report_data
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_detect_performance_issues(self, performance_tracker):
        """Test detecting performance issues."""
        # Track operations with potential issues
        with performance_tracker.track_operation("slow_operation"):
            time.sleep(0.5)  # Slow operation
        
        with performance_tracker.track_operation("fast_operation"):
            time.sleep(0.01)  # Fast operation
        
        issues = performance_tracker.detect_performance_issues()
        
        assert len(issues) > 0
        assert any("slow" in issue.lower() for issue in issues)

    def test_get_recommendations(self, performance_tracker):
        """Test getting performance recommendations."""
        # Track some operations
        for i in range(3):
            with performance_tracker.track_operation(f"operation_{i}"):
                time.sleep(0.2)  # Moderate operations
        
        recommendations = performance_tracker.get_recommendations()
        
        assert len(recommendations) > 0
        assert any("performance" in rec.lower() for rec in recommendations)

    def test_clear_performance_data(self, performance_tracker):
        """Test clearing performance data."""
        # Track some operations
        for i in range(3):
            with performance_tracker.track_operation(f"operation_{i}"):
                time.sleep(0.1)
        
        assert len(performance_tracker.monitor.metrics_history) == 3
        
        performance_tracker.clear_performance_data()
        assert len(performance_tracker.monitor.metrics_history) == 0
