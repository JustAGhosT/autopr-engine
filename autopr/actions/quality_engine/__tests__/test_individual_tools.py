"""
Tests for individual quality tools integration.
"""

from unittest.mock import patch

import pytest

from autopr.actions.quality_engine.tools.bandit_tool import BanditTool
from autopr.actions.quality_engine.tools.dependency_scanner_tool import DependencyScannerTool
from autopr.actions.quality_engine.tools.eslint_tool import ESLintTool
from autopr.actions.quality_engine.tools.interrogate_tool import InterrogateTool
from autopr.actions.quality_engine.tools.mypy_tool import MyPyTool
from autopr.actions.quality_engine.tools.performance_analyzer_tool import PerformanceAnalyzerTool
from autopr.actions.quality_engine.tools.pytest_tool import PyTestTool
from autopr.actions.quality_engine.tools.radon_tool import RadonTool
from autopr.actions.quality_engine.tools.ruff_tool import RuffTool
from autopr.actions.quality_engine.tools.semgrep_tool import SemgrepTool


class TestRuffTool:
    """Test Ruff tool integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = RuffTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio()
    async def test_ruff_execution_success(self):
        """Test successful Ruff execution."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (0, "Found 2 issues", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.tool_name == "ruff"
            assert result.issues_found == 2
            mock_run.assert_called_once()

    @pytest.mark.asyncio()
    async def test_ruff_execution_failure(self):
        """Test Ruff execution failure."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (1, "", "Error: ruff not found")

            result = await self.tool.execute(self.test_files)

            assert result.success is False
            assert "ruff not found" in result.error_message

    @pytest.mark.asyncio()
    async def test_ruff_with_custom_config(self):
        """Test Ruff with custom configuration."""
        config = {"max_line_length": 100, "select": ["E", "W"]}
        self.tool = RuffTool(config=config)

        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (0, "Found 0 issues", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            # Verify config was used in command
            call_args = mock_run.call_args[0][0]
            assert "--line-length=100" in call_args


class TestMyPyTool:
    """Test MyPy tool integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = MyPyTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio()
    async def test_mypy_execution_success(self):
        """Test successful MyPy execution."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (0, "Success: no issues found", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.tool_name == "mypy"
            assert result.issues_found == 0

    @pytest.mark.asyncio()
    async def test_mypy_with_type_errors(self):
        """Test MyPy with type errors."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (1, "test.py:5: error: Incompatible types", "")

            result = await self.tool.execute(self.test_files)

            assert (
                result.success is True
            )  # MyPy returns 1 for errors but we consider it successful execution
            assert result.issues_found > 0


class TestBanditTool:
    """Test Bandit tool integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = BanditTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio()
    async def test_bandit_execution_success(self):
        """Test successful Bandit execution."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (0, "No issues identified.", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.tool_name == "bandit"
            assert result.issues_found == 0

    @pytest.mark.asyncio()
    async def test_bandit_with_security_issues(self):
        """Test Bandit with security issues."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (1, ">> Issue: [B101:assert_used] Use of assert detected.", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.issues_found > 0


class TestSemgrepTool:
    """Test Semgrep tool integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = SemgrepTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio()
    async def test_semgrep_execution_success(self):
        """Test successful Semgrep execution."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (0, "No findings.", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.tool_name == "semgrep"
            assert result.issues_found == 0

    @pytest.mark.asyncio()
    async def test_semgrep_with_findings(self):
        """Test Semgrep with security findings."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (
                1,
                "test.py:5: python.lang.security.audit.unsafe-deserialization.unsafe-deserialization",
                "",
            )

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.issues_found > 0


class TestInterrogateTool:
    """Test Interrogate tool integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = InterrogateTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio()
    async def test_interrogate_execution_success(self):
        """Test successful Interrogate execution."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (0, "Coverage: 100%", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.tool_name == "interrogate"
            assert result.issues_found == 0

    @pytest.mark.asyncio()
    async def test_interrogate_with_coverage_issues(self):
        """Test Interrogate with coverage issues."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (1, "Coverage: 75%", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.issues_found > 0


class TestRadonTool:
    """Test Radon tool integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = RadonTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio()
    async def test_radon_execution_success(self):
        """Test successful Radon execution."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (0, "test.py - A (1.0)", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.tool_name == "radon"
            assert result.issues_found == 0

    @pytest.mark.asyncio()
    async def test_radon_with_complexity_issues(self):
        """Test Radon with complexity issues."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (0, "test.py - F (15.0)", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.issues_found > 0


class TestPyTestTool:
    """Test PyTest tool integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = PyTestTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio()
    async def test_pytest_execution_success(self):
        """Test successful PyTest execution."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (0, "1 passed", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.tool_name == "pytest"
            assert result.issues_found == 0

    @pytest.mark.asyncio()
    async def test_pytest_with_failures(self):
        """Test PyTest with test failures."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (1, "1 failed", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.issues_found > 0


class TestESLintTool:
    """Test ESLint tool integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = ESLintTool()
        self.test_files = ["test.js"]

    @pytest.mark.asyncio()
    async def test_eslint_execution_success(self):
        """Test successful ESLint execution."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (0, "", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.tool_name == "eslint"
            assert result.issues_found == 0

    @pytest.mark.asyncio()
    async def test_eslint_with_linting_errors(self):
        """Test ESLint with linting errors."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (1, "test.js:5:10 error 'x' is defined but never used", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.issues_found > 0


class TestDependencyScannerTool:
    """Test Dependency Scanner tool integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = DependencyScannerTool()
        self.test_files = ["requirements.txt"]

    @pytest.mark.asyncio()
    async def test_dependency_scanner_execution_success(self):
        """Test successful Dependency Scanner execution."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (0, "No vulnerabilities found", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.tool_name == "dependency_scanner"
            assert result.issues_found == 0

    @pytest.mark.asyncio()
    async def test_dependency_scanner_with_vulnerabilities(self):
        """Test Dependency Scanner with vulnerabilities."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (1, "Vulnerability found in package: CVE-2023-1234", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.issues_found > 0


class TestPerformanceAnalyzerTool:
    """Test Performance Analyzer tool integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = PerformanceAnalyzerTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio()
    async def test_performance_analyzer_execution_success(self):
        """Test successful Performance Analyzer execution."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (0, "Performance analysis complete", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.tool_name == "performance_analyzer"
            assert result.issues_found == 0

    @pytest.mark.asyncio()
    async def test_performance_analyzer_with_issues(self):
        """Test Performance Analyzer with performance issues."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (1, "Performance issue detected: slow loop", "")

            result = await self.tool.execute(self.test_files)

            assert result.success is True
            assert result.issues_found > 0


class TestToolBase:
    """Test base tool functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = RuffTool()  # Use Ruff as example

    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "ruff"
        assert self.tool.description is not None
        assert self.tool.supported_extensions == [".py"]

    def test_tool_supports_file(self):
        """Test file support detection."""
        assert self.tool.supports_file("test.py") is True
        assert self.tool.supports_file("test.js") is False

    def test_tool_config_validation(self):
        """Test tool configuration validation."""
        valid_config = {"max_line_length": 100}
        assert self.tool.validate_config(valid_config) is True

        invalid_config = {"invalid_option": "value"}
        assert self.tool.validate_config(invalid_config) is False

    @pytest.mark.asyncio()
    async def test_tool_execution_with_timeout(self):
        """Test tool execution with timeout."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.side_effect = TimeoutError()

            result = await self.tool.execute(["test.py"])

            assert result.success is False
            assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio()
    async def test_tool_execution_with_missing_tool(self):
        """Test tool execution when tool is not installed."""
        with patch.object(self.tool, "_run_command") as mock_run:
            mock_run.return_value = (127, "", "command not found")

            result = await self.tool.execute(["test.py"])

            assert result.success is False
            assert "not found" in result.error_message.lower()


if __name__ == "__main__":
    pytest.main([__file__])
