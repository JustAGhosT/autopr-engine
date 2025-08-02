"""
Tests for enhanced tool base class features.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from autopr.actions.quality_engine.tools.semgrep_tool import SemgrepTool
from autopr.actions.quality_engine.tools.tool_base import Tool
from autopr.actions.quality_engine.tools.windows_security_tool import WindowsSecurityTool


class TestTool:
    """Test the enhanced base tool class."""

    def test_tool_initialization(self):
        """Test tool initialization with default values."""
        tool = SemgrepTool()

        assert tool.name == "semgrep"
        assert tool.category == "security"
        assert tool.timeout == 120.0
        assert tool.max_files == 200
        assert (
            tool.description
            == "Cross-platform static analysis for security vulnerabilities and code quality issues"
        )

    def test_tool_display_name(self):
        """Test tool display name generation."""
        tool = SemgrepTool()
        assert tool.get_display_name() == "Semgrep"

        # Test with underscore in name
        class TestTool(Tool):
            @property
            def name(self) -> str:
                return "test_tool_name"

            @property
            def description(self) -> str:
                return "Test description"

            async def run(self, files, config):
                return []

        test_tool = TestTool()
        assert test_tool.get_display_name() == "Test Tool Name"

    def test_tool_string_representation(self):
        """Test tool string representation."""
        tool = SemgrepTool()
        assert str(tool) == "Semgrep (security)"
        assert repr(tool) == "SemgrepTool(name='semgrep', category='security')"

    def test_config_schema(self):
        """Test configuration schema generation."""
        tool = SemgrepTool()
        schema = tool.get_config_schema()

        assert "timeout" in schema
        assert "max_files" in schema
        assert "verbose" in schema
        assert schema["timeout"]["default"] == 120.0
        assert schema["max_files"]["default"] == 200

    def test_config_validation(self):
        """Test configuration validation."""
        tool = SemgrepTool()

        # Valid config
        errors = tool.validate_config({})
        assert len(errors) == 0

        # Invalid timeout
        errors = tool.validate_config({"timeout": -1})
        assert len(errors) == 1
        assert "positive number" in errors[0]

        # Invalid max_files
        errors = tool.validate_config({"max_files": 0})
        assert len(errors) == 1
        assert "positive integer" in errors[0]

        # Invalid config type
        errors = tool.validate_config("not a dict")
        assert len(errors) == 1
        assert "dictionary" in errors[0]

    def test_performance_metrics(self):
        """Test performance metrics generation."""
        tool = SemgrepTool()
        metrics = tool.get_performance_metrics()

        assert metrics["recommended_timeout"] == 120.0
        assert metrics["recommended_max_files"] == 200
        assert metrics["category"] == "security"
        assert "static analysis" in metrics["description"]


class TestToolExecution:
    """Test tool execution with timeout handling."""

    @pytest.mark.asyncio()
    async def test_successful_execution(self):
        """Test successful tool execution."""
        tool = SemgrepTool()

        with patch.object(tool, "run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = [{"issue": "test"}]

            result = await tool.run_with_timeout(["test.py"], {})

            assert result["success"] is True
            assert len(result["issues"]) == 1
            assert result["execution_time"] > 0
            assert result["error_message"] is None
            assert result["warnings"] == []
            assert "1 issue found" in result["output_summary"]

    @pytest.mark.asyncio()
    async def test_timeout_handling(self):
        """Test timeout handling."""
        tool = SemgrepTool()
        tool.default_timeout = 0.1  # Very short timeout for testing

        async def slow_run(files, config):
            await asyncio.sleep(1)  # Sleep longer than timeout
            return []

        with patch.object(tool, "run", side_effect=slow_run):
            result = await tool.run_with_timeout(["test.py"], {})

            assert result["success"] is False
            assert "timed out" in result["error_message"]
            assert result["execution_time"] >= 0.1

    @pytest.mark.asyncio()
    async def test_error_handling(self):
        """Test error handling."""
        tool = SemgrepTool()

        async def failing_run(files, config):
            raise Exception("Test error")

        with patch.object(tool, "run", side_effect=failing_run):
            result = await tool.run_with_timeout(["test.py"], {})

            assert result["success"] is False
            assert "Test error" in result["error_message"]
            assert result["issues"] == []

    @pytest.mark.asyncio()
    async def test_file_limit_warning(self):
        """Test file limit warning."""
        tool = SemgrepTool()
        tool.max_files_per_run = 5

        with patch.object(tool, "run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = []

            # Test with more files than limit
            result = await tool.run_with_timeout(
                ["1.py", "2.py", "3.py", "4.py", "5.py", "6.py"], {}
            )

            assert result["success"] is True
            assert len(result["warnings"]) == 1
            assert "Limited to first 5 files" in result["warnings"][0]

    @pytest.mark.asyncio()
    async def test_output_summary_generation(self):
        """Test output summary generation."""
        tool = SemgrepTool()

        # Test no issues
        result = await tool.run_with_timeout([], {})
        assert "No issues found" in result["output_summary"]

        # Test with issues
        with patch.object(tool, "run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = [{"issue": "1"}, {"issue": "2"}]
            result = await tool.run_with_timeout(["test.py"], {})
            assert "2 issues found" in result["output_summary"]

        # Test with error
        with patch.object(tool, "run", side_effect=Exception("Test error")):
            result = await tool.run_with_timeout(["test.py"], {})
            assert "Test error" in result["output_summary"]


class TestSemgrepTool:
    """Test Semgrep tool specifically."""

    def test_semgrep_tool_properties(self):
        """Test Semgrep tool properties."""
        tool = SemgrepTool()

        assert tool.name == "semgrep"
        assert tool.category == "security"
        assert tool.timeout == 120.0
        assert tool.max_files == 200

    def test_semgrep_default_config(self):
        """Test Semgrep default configuration."""
        tool = SemgrepTool()
        config = tool.get_default_config()

        assert config["rules"] == "auto"
        assert config["severity"] == "INFO,WARNING,ERROR"
        assert config["strict"] is False
        assert config["verbose"] is False
        assert "security" in config["categories"]

    def test_semgrep_supported_languages(self):
        """Test Semgrep supported languages."""
        tool = SemgrepTool()
        languages = tool.get_supported_languages()

        assert "python" in languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert "java" in languages
        assert "go" in languages

    def test_semgrep_rule_categories(self):
        """Test Semgrep rule categories."""
        tool = SemgrepTool()
        categories = tool.get_rule_categories()

        assert "security" in categories
        assert "performance" in categories
        assert "maintainability" in categories
        assert "bug" in categories

    def test_category_determination(self):
        """Test issue category determination."""
        tool = SemgrepTool()

        # Test security category
        category = tool._determine_category("security.vulnerability.xss", {})
        assert category == "security"

        # Test performance category
        category = tool._determine_category("performance.memory.leak", {})
        assert category == "performance"

        # Test maintainability category
        category = tool._determine_category("maintainability.style.convention", {})
        assert category == "maintainability"

        # Test bug category
        category = tool._determine_category("bug.null.pointer", {})
        assert category == "bug"

        # Test default category
        category = tool._determine_category("unknown.rule", {})
        assert category == "general"


class TestWindowsSecurityTool:
    """Test Windows Security tool specifically."""

    def test_windows_security_tool_properties(self):
        """Test Windows Security tool properties."""
        tool = WindowsSecurityTool()

        assert tool.name == "windows_security"
        assert tool.category == "security"
        assert tool.timeout == 45.0
        assert tool.max_files == 50

    @pytest.mark.asyncio()
    async def test_windows_security_empty_files(self):
        """Test Windows Security tool with empty file list."""
        tool = WindowsSecurityTool()
        result = await tool.run([], {})
        assert result == []

    @pytest.mark.asyncio()
    async def test_windows_security_python_security_patterns(self):
        """Test Python security pattern detection."""
        tool = WindowsSecurityTool()

        # Test with content containing security issues
        test_content = """
        password = "secret123"
        eval("dangerous_code")
        subprocess.run("command", shell=True)
        """

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = test_content

            issues = await tool._check_python_security_patterns("test.py", {})

            # Should find hardcoded secret, eval usage, and shell injection
            assert len(issues) == 3

            # Check for hardcoded secret
            secret_issues = [i for i in issues if i["code"] == "HARDCODED_SECRET"]
            assert len(secret_issues) == 1

            # Check for eval usage
            eval_issues = [i for i in issues if i["code"] == "EVAL_USAGE"]
            assert len(eval_issues) == 1

            # Check for shell injection
            shell_issues = [i for i in issues if i["code"] == "SHELL_INJECTION"]
            assert len(shell_issues) == 1
