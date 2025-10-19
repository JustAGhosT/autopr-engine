#!/usr/bin/env python3
"""
Comprehensive tests for exception specialist module.
"""

import json
import os
import tempfile
from unittest.mock import Mock

import pytest


# Import the modules we're testing
try:
    from autopr.actions.exception_specialist import (
        ExceptionAnalyzer,
        ExceptionConfig,
        ExceptionHandler,
        ExceptionPattern,
        ExceptionReporter,
        ExceptionSpecialist,
    )
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestExceptionConfig:
    """Test ExceptionConfig class."""

    def test_exception_config_initialization(self):
        """Test ExceptionConfig initialization."""
        config = ExceptionConfig(
            enable_analysis=True,
            enable_handling=True,
            enable_reporting=True,
            log_exceptions=True,
            max_exception_history=100,
            auto_retry=True,
            retry_attempts=3
        )

        assert config.enable_analysis is True
        assert config.enable_handling is True
        assert config.enable_reporting is True
        assert config.log_exceptions is True
        assert config.max_exception_history == 100
        assert config.auto_retry is True
        assert config.retry_attempts == 3

    def test_exception_config_defaults(self):
        """Test ExceptionConfig with default values."""
        config = ExceptionConfig()

        assert config.enable_analysis is True
        assert config.enable_handling is True
        assert config.enable_reporting is True
        assert config.log_exceptions is True
        assert config.max_exception_history == 50
        assert config.auto_retry is False
        assert config.retry_attempts == 1

    def test_exception_config_to_dict(self):
        """Test ExceptionConfig to_dict method."""
        config = ExceptionConfig(
            enable_analysis=False,
            auto_retry=True,
            retry_attempts=5
        )

        result = config.to_dict()
        assert result["enable_analysis"] is False
        assert result["auto_retry"] is True
        assert result["retry_attempts"] == 5

    def test_exception_config_from_dict(self):
        """Test ExceptionConfig from_dict method."""
        data = {
            "enable_analysis": True,
            "enable_handling": False,
            "enable_reporting": True,
            "log_exceptions": False,
            "max_exception_history": 200,
            "auto_retry": True,
            "retry_attempts": 4
        }

        config = ExceptionConfig.from_dict(data)
        assert config.enable_analysis is True
        assert config.enable_handling is False
        assert config.enable_reporting is True
        assert config.log_exceptions is False
        assert config.max_exception_history == 200
        assert config.auto_retry is True
        assert config.retry_attempts == 4

    def test_exception_config_validation(self):
        """Test ExceptionConfig validation."""
        valid_config = ExceptionConfig(max_exception_history=100, retry_attempts=3)
        assert valid_config.is_valid() is True

        invalid_config = ExceptionConfig(max_exception_history=0, retry_attempts=0)
        assert invalid_config.is_valid() is False


class TestExceptionPattern:
    """Test ExceptionPattern class."""

    def test_exception_pattern_initialization(self):
        """Test ExceptionPattern initialization."""
        pattern = ExceptionPattern(
            name="connection_error",
            pattern=".*Connection.*failed.*",
            severity="high",
            category="network",
            suggested_fix="Check network connectivity"
        )

        assert pattern.name == "connection_error"
        assert pattern.pattern == ".*Connection.*failed.*"
        assert pattern.severity == "high"
        assert pattern.category == "network"
        assert pattern.suggested_fix == "Check network connectivity"

    def test_exception_pattern_defaults(self):
        """Test ExceptionPattern with default values."""
        pattern = ExceptionPattern(name="test_pattern", pattern=".*test.*")

        assert pattern.name == "test_pattern"
        assert pattern.pattern == ".*test.*"
        assert pattern.severity == "medium"
        assert pattern.category == "general"
        assert pattern.suggested_fix == ""

    def test_exception_pattern_match(self):
        """Test ExceptionPattern match method."""
        pattern = ExceptionPattern(
            name="timeout_error",
            pattern=".*timeout.*",
            severity="high"
        )

        # Matching exception
        matching_exception = "Connection timeout after 30 seconds"
        assert pattern.matches(matching_exception) is True

        # Non-matching exception
        non_matching_exception = "File not found"
        assert pattern.matches(non_matching_exception) is False

    def test_exception_pattern_to_dict(self):
        """Test ExceptionPattern to_dict method."""
        pattern = ExceptionPattern(
            name="validation_error",
            pattern=".*validation.*failed.*",
            severity="medium",
            category="input",
            suggested_fix="Validate input data"
        )

        result = pattern.to_dict()
        assert result["name"] == "validation_error"
        assert result["pattern"] == ".*validation.*failed.*"
        assert result["severity"] == "medium"
        assert result["category"] == "input"
        assert result["suggested_fix"] == "Validate input data"

    def test_exception_pattern_from_dict(self):
        """Test ExceptionPattern from_dict method."""
        data = {
            "name": "permission_error",
            "pattern": ".*permission.*denied.*",
            "severity": "high",
            "category": "security",
            "suggested_fix": "Check file permissions"
        }

        pattern = ExceptionPattern.from_dict(data)
        assert pattern.name == "permission_error"
        assert pattern.pattern == ".*permission.*denied.*"
        assert pattern.severity == "high"
        assert pattern.category == "security"
        assert pattern.suggested_fix == "Check file permissions"


class TestExceptionAnalyzer:
    """Test ExceptionAnalyzer class."""

    @pytest.fixture
    def exception_analyzer(self):
        """Create an ExceptionAnalyzer instance for testing."""
        return ExceptionAnalyzer()

    def test_exception_analyzer_initialization(self, exception_analyzer):
        """Test ExceptionAnalyzer initialization."""
        assert exception_analyzer.patterns == []
        assert exception_analyzer.analysis_cache == {}

    def test_add_pattern(self, exception_analyzer):
        """Test adding an exception pattern."""
        pattern = ExceptionPattern(
            name="test_pattern",
            pattern=".*test.*",
            severity="medium"
        )

        exception_analyzer.add_pattern(pattern)
        assert len(exception_analyzer.patterns) == 1
        assert exception_analyzer.patterns[0] == pattern

    def test_analyze_exception(self, exception_analyzer):
        """Test analyzing an exception."""
        # Add a pattern
        pattern = ExceptionPattern(
            name="connection_error",
            pattern=".*Connection.*failed.*",
            severity="high",
            category="network"
        )
        exception_analyzer.add_pattern(pattern)

        # Analyze matching exception
        exception_message = "Connection failed to database"
        result = exception_analyzer.analyze_exception(exception_message)

        assert result.matched_patterns == [pattern]
        assert result.severity == "high"
        assert result.category == "network"
        assert len(result.suggestions) > 0

    def test_analyze_exception_no_match(self, exception_analyzer):
        """Test analyzing an exception with no matching patterns."""
        exception_message = "Unknown error occurred"
        result = exception_analyzer.analyze_exception(exception_message)

        assert result.matched_patterns == []
        assert result.severity == "unknown"
        assert result.category == "unknown"

    def test_analyze_exception_stack_trace(self, exception_analyzer):
        """Test analyzing an exception with stack trace."""
        stack_trace = """
        Traceback (most recent call last):
          File "test.py", line 10, in <module>
            result = divide(10, 0)
          File "math.py", line 5, in divide
            return a / b
        ZeroDivisionError: division by zero
        """

        result = exception_analyzer.analyze_exception_stack_trace(stack_trace)

        assert result.exception_type == "ZeroDivisionError"
        assert result.exception_message == "division by zero"
        assert result.file_name == "math.py"
        assert result.line_number == 5

    def test_get_exception_statistics(self, exception_analyzer):
        """Test getting exception statistics."""
        # Add some patterns and analyze exceptions
        pattern1 = ExceptionPattern(name="error1", pattern=".*error1.*", severity="high")
        pattern2 = ExceptionPattern(name="error2", pattern=".*error2.*", severity="medium")

        exception_analyzer.add_pattern(pattern1)
        exception_analyzer.add_pattern(pattern2)

        exception_analyzer.analyze_exception("This is error1 message")
        exception_analyzer.analyze_exception("This is error2 message")
        exception_analyzer.analyze_exception("This is error1 again")

        stats = exception_analyzer.get_exception_statistics()

        assert stats["total_exceptions"] == 3
        assert stats["high_severity"] == 2
        assert stats["medium_severity"] == 1
        assert "error1" in stats["pattern_counts"]
        assert "error2" in stats["pattern_counts"]


class TestExceptionHandler:
    """Test ExceptionHandler class."""

    @pytest.fixture
    def exception_handler(self):
        """Create an ExceptionHandler instance for testing."""
        config = ExceptionConfig(auto_retry=True, retry_attempts=3)
        return ExceptionHandler(config)

    def test_exception_handler_initialization(self, exception_handler):
        """Test ExceptionHandler initialization."""
        assert exception_handler.config is not None
        assert exception_handler.handlers == {}

    def test_register_handler(self, exception_handler):
        """Test registering an exception handler."""
        def connection_handler(exception):
            return "Retry connection"

        exception_handler.register_handler("ConnectionError", connection_handler)
        assert "ConnectionError" in exception_handler.handlers

    def test_handle_exception(self, exception_handler):
        """Test handling an exception."""
        def test_handler(exception):
            return f"Handled: {exception}"

        exception_handler.register_handler("TestError", test_handler)

        exception = Exception("Test error message")
        exception.__class__.__name__ = "TestError"

        result = exception_handler.handle_exception(exception)
        assert result == "Handled: Test error message"

    def test_handle_exception_no_handler(self, exception_handler):
        """Test handling an exception with no registered handler."""
        exception = Exception("Unknown error")
        exception.__class__.__name__ = "UnknownError"

        result = exception_handler.handle_exception(exception)
        assert result is None

    def test_retry_with_exception(self, exception_handler):
        """Test retrying a function that raises an exception."""
        def failing_function():
            raise ValueError("Test error")

        def success_function():
            return "Success"

        # Test failing function
        result = exception_handler.retry_with_exception(failing_function)
        assert result is None  # Should fail after retries

        # Test successful function
        result = exception_handler.retry_with_exception(success_function)
        assert result == "Success"

    def test_handle_exception_with_context(self, exception_handler):
        """Test handling an exception with additional context."""
        def context_handler(exception, context):
            return f"Handled {exception} with context: {context}"

        exception_handler.register_handler("ContextError", context_handler)

        exception = Exception("Context error")
        exception.__class__.__name__ = "ContextError"

        context = {"user_id": 123, "operation": "save"}
        result = exception_handler.handle_exception_with_context(exception, context)

        assert "Context error" in result
        assert "user_id" in result
        assert "save" in result


class TestExceptionReporter:
    """Test ExceptionReporter class."""

    @pytest.fixture
    def exception_reporter(self):
        """Create an ExceptionReporter instance for testing."""
        return ExceptionReporter()

    def test_exception_reporter_initialization(self, exception_reporter):
        """Test ExceptionReporter initialization."""
        assert exception_reporter.reports == []
        assert exception_reporter.report_formats == {}

    def test_add_exception_report(self, exception_reporter):
        """Test adding an exception report."""
        exception = Exception("Test error")
        analysis_result = Mock(
            matched_patterns=[],
            severity="medium",
            category="test",
            suggestions=["Fix the issue"]
        )

        exception_reporter.add_exception_report(exception, analysis_result)
        assert len(exception_reporter.reports) == 1

    def test_generate_exception_report(self, exception_reporter):
        """Test generating an exception report."""
        # Add some exception reports
        for i in range(3):
            exception = Exception(f"Error {i}")
            analysis_result = Mock(
                matched_patterns=[],
                severity="medium",
                category="test",
                suggestions=[f"Fix {i}"]
            )
            exception_reporter.add_exception_report(exception, analysis_result)

        report = exception_reporter.generate_exception_report()

        assert "total_exceptions" in report
        assert "severity_breakdown" in report
        assert "category_breakdown" in report
        assert report["total_exceptions"] == 3

    def test_generate_exception_summary(self, exception_reporter):
        """Test generating an exception summary."""
        # Add exception reports with different severities
        for severity in ["high", "medium", "low"]:
            exception = Exception(f"{severity} error")
            analysis_result = Mock(
                matched_patterns=[],
                severity=severity,
                category="test",
                suggestions=["Fix it"]
            )
            exception_reporter.add_exception_report(exception, analysis_result)

        summary = exception_reporter.generate_exception_summary()

        assert summary["total_exceptions"] == 3
        assert summary["high_severity"] == 1
        assert summary["medium_severity"] == 1
        assert summary["low_severity"] == 1

    def test_export_exception_report(self, exception_reporter):
        """Test exporting an exception report."""
        # Add a test report
        exception = Exception("Export test error")
        analysis_result = Mock(
            matched_patterns=[],
            severity="high",
            category="export",
            suggestions=["Fix export"]
        )
        exception_reporter.add_exception_report(exception, analysis_result)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name

        try:
            result = exception_reporter.export_exception_report(temp_file, "json")
            assert result is True
            assert os.path.exists(temp_file)

            with open(temp_file) as f:
                content = f.read()
                report_data = json.loads(content)
                assert "total_exceptions" in report_data
                assert report_data["total_exceptions"] == 1

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_clear_exception_reports(self, exception_reporter):
        """Test clearing exception reports."""
        # Add some reports
        for i in range(3):
            exception = Exception(f"Error {i}")
            analysis_result = Mock(
                matched_patterns=[],
                severity="medium",
                category="test",
                suggestions=["Fix it"]
            )
            exception_reporter.add_exception_report(exception, analysis_result)

        assert len(exception_reporter.reports) == 3

        exception_reporter.clear_exception_reports()
        assert len(exception_reporter.reports) == 0


class TestExceptionSpecialist:
    """Test ExceptionSpecialist class."""

    @pytest.fixture
    def exception_specialist(self):
        """Create an ExceptionSpecialist instance for testing."""
        config = ExceptionConfig(enable_analysis=True, enable_handling=True)
        return ExceptionSpecialist(config)

    def test_exception_specialist_initialization(self, exception_specialist):
        """Test ExceptionSpecialist initialization."""
        assert exception_specialist.config is not None
        assert exception_specialist.analyzer is not None
        assert exception_specialist.handler is not None
        assert exception_specialist.reporter is not None

    def test_handle_exception_comprehensive(self, exception_specialist):
        """Test comprehensive exception handling."""
        exception = Exception("Comprehensive test error")

        result = exception_specialist.handle_exception_comprehensive(exception)

        assert result.analyzed is True
        assert result.handled is True
        assert result.reported is True

    def test_add_exception_pattern(self, exception_specialist):
        """Test adding an exception pattern."""
        pattern = ExceptionPattern(
            name="test_pattern",
            pattern=".*test.*",
            severity="medium"
        )

        exception_specialist.add_exception_pattern(pattern)
        assert len(exception_specialist.analyzer.patterns) == 1

    def test_register_exception_handler(self, exception_specialist):
        """Test registering an exception handler."""
        def test_handler(exception):
            return "Handled test exception"

        exception_specialist.register_exception_handler("TestError", test_handler)
        assert "TestError" in exception_specialist.handler.handlers

    def test_analyze_and_handle_exception(self, exception_specialist):
        """Test analyzing and handling an exception."""
        exception = Exception("Analyze and handle test")

        result = exception_specialist.analyze_and_handle_exception(exception)

        assert result.analysis is not None
        assert result.handling_result is not None

    def test_get_exception_statistics(self, exception_specialist):
        """Test getting exception statistics."""
        # Handle some exceptions first
        for i in range(3):
            exception = Exception(f"Error {i}")
            exception_specialist.handle_exception_comprehensive(exception)

        stats = exception_specialist.get_exception_statistics()

        assert "total_exceptions" in stats
        assert "analysis_stats" in stats
        assert "handling_stats" in stats
        assert "reporting_stats" in stats

    def test_generate_exception_report(self, exception_specialist):
        """Test generating a comprehensive exception report."""
        # Handle some exceptions first
        for i in range(2):
            exception = Exception(f"Report error {i}")
            exception_specialist.handle_exception_comprehensive(exception)

        report = exception_specialist.generate_exception_report()

        assert "summary" in report
        assert "details" in report
        assert "recommendations" in report
        assert "statistics" in report

    def test_clear_exception_data(self, exception_specialist):
        """Test clearing all exception data."""
        # Add some data first
        exception = Exception("Test error")
        exception_specialist.handle_exception_comprehensive(exception)

        # Clear data
        exception_specialist.clear_exception_data()

        # Verify data is cleared
        stats = exception_specialist.get_exception_statistics()
        assert stats["total_exceptions"] == 0
