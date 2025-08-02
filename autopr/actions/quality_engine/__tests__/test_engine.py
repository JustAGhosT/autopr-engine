"""
Tests for Quality Engine core functionality.
"""

from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autopr.actions.quality_engine.engine import QualityEngine
from autopr.actions.quality_engine.models import QualityMode, QualityOutputs


class TestQualityEngine:
    """Test Quality Engine core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = QualityEngine()
        self.test_files = ["test1.py", "test2.py"]

    @pytest.mark.asyncio()
    async def test_execute_fast_mode(self):
        """Test Quality Engine execution in fast mode."""
        with patch.object(self.engine, "_run_tools") as mock_run_tools:
            mock_result = QualityOutputs(
                success=True,
                total_issues_found=2,
                total_issues_fixed=0,
                files_modified=[],
                issues_by_tool={"ruff": [{"issue": "test"}]},
                files_by_tool={"ruff": ["test.py"]},
                summary="Test summary",
            )
            mock_run_tools.return_value = mock_result

            result = await self.engine.execute(files=self.test_files, mode=QualityMode.FAST)

            assert result.success is True
            assert result.total_issues == 2
            mock_run_tools.assert_called_once()

    @pytest.mark.asyncio()
    async def test_execute_comprehensive_mode(self):
        """Test Quality Engine execution in comprehensive mode."""
        with patch.object(self.engine, "_run_tools") as mock_run_tools:
            mock_result = QualityOutputs(
                success=True,
                total_issues_found=5,
                total_issues_fixed=0,
                files_modified=[],
                issues_by_tool={"ruff": [{"issue": "test"}], "bandit": [{"issue": "test"}]},
                files_by_tool={"ruff": ["test.py"], "bandit": ["test.py"]},
                summary="Test summary",
            )
            mock_run_tools.return_value = mock_result

            result = await self.engine.execute(
                files=self.test_files, mode=QualityMode.COMPREHENSIVE
            )

            assert result.success is True
            assert result.total_issues == 5
            assert len(result.issues_by_tool) == 2
            mock_run_tools.assert_called_once()

    @pytest.mark.asyncio()
    async def test_execute_ai_enhanced_mode(self):
        """Test Quality Engine execution in AI-enhanced mode."""
        with patch.object(self.engine, "_run_tools") as mock_run_tools:
            with patch.object(self.engine, "_run_ai_analysis") as mock_ai_analysis:
                mock_result = QualityOutputs(
                    success=True,
                    total_issues_found=3,
                    total_issues_fixed=0,
                    files_modified=[],
                    issues_by_tool={"ruff": [{"issue": "test"}]},
                    files_by_tool={"ruff": ["test.py"]},
                    summary="Test summary",
                )
                mock_run_tools.return_value = mock_result
                mock_ai_analysis.return_value = {"ai_suggestions": ["suggestion1"]}

                result = await self.engine.execute(
                    files=self.test_files, mode=QualityMode.AI_ENHANCED
                )

                assert result.success is True
                assert result.total_issues == 3
                mock_run_tools.assert_called_once()
                mock_ai_analysis.assert_called_once()

    @pytest.mark.asyncio()
    async def test_execute_smart_mode(self):
        """Test Quality Engine execution in smart mode."""
        with patch.object(self.engine, "_select_tools_for_context") as mock_select:
            with patch.object(self.engine, "_run_tools") as mock_run_tools:
                mock_select.return_value = ["ruff", "bandit"]
                mock_result = QualityOutputs(
                    success=True,
                    total_issues_found=1,
                    total_issues_fixed=0,
                    files_modified=[],
                    issues_by_tool={"ruff": [{"issue": "test"}]},
                    files_by_tool={"ruff": ["test.py"]},
                    summary="Test summary",
                )
                mock_run_tools.return_value = mock_result

                result = await self.engine.execute(files=self.test_files, mode=QualityMode.SMART)

                assert result.success is True
                mock_select.assert_called_once_with(self.test_files)
                mock_run_tools.assert_called_once()

    @pytest.mark.asyncio()
    async def test_execute_empty_file_list(self):
        """Test Quality Engine execution with empty file list."""
        result = await self.engine.execute(files=[], mode=QualityMode.FAST)

        assert result.success is True
        assert result.total_issues_found == 0
        assert len(result.files_modified) == 0

    @pytest.mark.asyncio()
    async def test_execute_disabled_tools(self):
        """Test Quality Engine execution with disabled tools."""
        with patch.object(self.engine, "_run_tools") as mock_run_tools:
            mock_result = QualityOutputs(
                success=True,
                total_issues_found=0,
                total_issues_fixed=0,
                files_modified=[],
                issues_by_tool={},
                files_by_tool={},
                summary="Test summary",
            )
            mock_run_tools.return_value = mock_result

            result = await self.engine.execute(
                files=self.test_files, mode=QualityMode.FAST, disabled_tools=["ruff"]
            )

            assert result.success is True
            mock_run_tools.assert_called_once()

    @pytest.mark.asyncio()
    async def test_execute_tool_failure(self):
        """Test Quality Engine execution when tools fail."""
        with patch.object(self.engine, "_run_tools") as mock_run_tools:
            mock_run_tools.side_effect = Exception("Tool execution failed")

            result = await self.engine.execute(files=self.test_files, mode=QualityMode.FAST)

            assert result.success is False
            assert "Tool execution failed" in result.error_message

    def test_select_tools_for_context(self):
        """Test smart tool selection based on context."""
        # Test Python files
        python_files = ["test.py", "module.py"]
        tools = self.engine._select_tools_for_context(python_files)
        assert "ruff" in tools
        assert "mypy" in tools

        # Test JavaScript files
        js_files = ["test.js", "component.tsx"]
        tools = self.engine._select_tools_for_context(js_files)
        assert "eslint" in tools

        # Test mixed files
        mixed_files = ["test.py", "test.js"]
        tools = self.engine._select_tools_for_context(mixed_files)
        assert "ruff" in tools
        assert "eslint" in tools

    def test_validate_configuration(self):
        """Test configuration validation."""
        # Test valid configuration
        valid_config = {"tools": {"ruff": {"enabled": True}, "bandit": {"enabled": True}}}
        assert self.engine._validate_configuration(valid_config) is True

        # Test invalid configuration (missing required fields)
        invalid_config = {"tools": {"ruff": {"enabled": True}}}
        # This should not raise an exception but return False
        assert self.engine._validate_configuration(invalid_config) is False

    @pytest.mark.asyncio()
    async def test_run_ai_analysis(self):
        """Test AI analysis execution."""
        with patch.object(self.engine, "_get_ai_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.analyze = AsyncMock(return_value={"suggestions": ["test"]})
            mock_get_provider.return_value = mock_provider

            result = await self.engine._run_ai_analysis(self.test_files)

            assert result["suggestions"] == ["test"]
            mock_provider.analyze.assert_called_once_with(self.test_files)

    def test_get_available_tools(self):
        """Test getting available tools for a mode."""
        fast_tools = self.engine._get_available_tools(QualityMode.FAST)
        assert "ruff" in fast_tools

        comprehensive_tools = self.engine._get_available_tools(QualityMode.COMPREHENSIVE)
        assert "ruff" in comprehensive_tools
        assert "bandit" in comprehensive_tools
        assert "mypy" in comprehensive_tools

    def test_filter_disabled_tools(self):
        """Test filtering disabled tools."""
        all_tools = ["ruff", "bandit", "mypy"]
        disabled_tools = ["bandit"]

        filtered_tools = self.engine._filter_disabled_tools(all_tools, disabled_tools)

        assert "ruff" in filtered_tools
        assert "mypy" in filtered_tools
        assert "bandit" not in filtered_tools

    @pytest.mark.asyncio()
    async def test_execute_with_custom_config(self):
        """Test Quality Engine execution with custom configuration."""
        custom_config = {
            "tools": {
                "ruff": {"enabled": True, "max_line_length": 100},
                "bandit": {"enabled": False},
            }
        }

        with patch.object(self.engine, "_run_tools") as mock_run_tools:
            mock_result = QualityResult(
                success=True, total_issues=1, files_with_issues=1, issues_by_tool={"ruff": 1}
            )
            mock_run_tools.return_value = mock_result

            result = await self.engine.execute(
                files=self.test_files, mode=QualityMode.FAST, config=custom_config
            )

            assert result.success is True
            assert result.total_issues == 1
            mock_run_tools.assert_called_once()

    def test_detect_file_types(self):
        """Test file type detection."""
        files = ["test.py", "test.js", "test.ts", "test.pyx", "test.c", "test.cpp"]

        file_types = self.engine._detect_file_types(files)

        assert "python" in file_types
        assert "javascript" in file_types
        assert "typescript" in file_types

    @pytest.mark.asyncio()
    async def test_execute_with_verbose_logging(self):
        """Test Quality Engine execution with verbose logging."""
        with patch.object(self.engine, "_run_tools") as mock_run_tools:
            with patch("logging.getLogger") as mock_logger:
                mock_log = MagicMock()
                mock_logger.return_value = mock_log

                mock_result = QualityResult(
                    success=True, total_issues=0, files_with_issues=0, issues_by_tool={}
                )
                mock_run_tools.return_value = mock_result

                result = await self.engine.execute(
                    files=self.test_files, mode=QualityMode.FAST, verbose=True
                )

                assert result.success is True
                mock_log.info.assert_called()

    def test_merge_results(self):
        """Test merging multiple tool results."""
        result1 = QualityResult(
            success=True, total_issues=2, files_with_issues=1, issues_by_tool={"ruff": 2}
        )

        result2 = QualityResult(
            success=True, total_issues=3, files_with_issues=2, issues_by_tool={"bandit": 3}
        )

        merged = self.engine._merge_results([result1, result2])

        assert merged.success is True
        assert merged.total_issues == 5
        assert merged.files_with_issues == 2
        assert merged.issues_by_tool["ruff"] == 2
        assert merged.issues_by_tool["bandit"] == 3


class TestQualityEngineIntegration:
    """Integration tests for Quality Engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = QualityEngine()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_file(self, filename, content):
        """Create a test file with given content."""
        file_path = Path(self.temp_dir) / filename
        file_path.write_text(content)
        return str(file_path)

    @pytest.mark.asyncio()
    async def test_end_to_end_fast_mode(self):
        """Test end-to-end Quality Engine execution in fast mode."""
        # Create test files
        test_file1 = self.create_test_file("test1.py", "def test_function():\n    pass\n")
        test_file2 = self.create_test_file("test2.py", "import os\nprint('hello')\n")

        with patch.object(self.engine, "_run_tools") as mock_run_tools:
            mock_result = QualityResult(
                success=True, total_issues=1, files_with_issues=1, issues_by_tool={"ruff": 1}
            )
            mock_run_tools.return_value = mock_result

            result = await self.engine.execute(
                files=[test_file1, test_file2], mode=QualityMode.FAST
            )

            assert result.success is True
            assert result.total_issues == 1
            mock_run_tools.assert_called_once()

    @pytest.mark.asyncio()
    async def test_end_to_end_comprehensive_mode(self):
        """Test end-to-end Quality Engine execution in comprehensive mode."""
        # Create test files with various issues
        test_file = self.create_test_file(
            "test.py",
            """
def complex_function():
    x = 1
    y = 2
    z = 3
    if x > 0:
        if y > 0:
            if z > 0:
                print("nested")
    return x + y + z
""",
        )

        with patch.object(self.engine, "_run_tools") as mock_run_tools:
            mock_result = QualityResult(
                success=True,
                total_issues=3,
                files_with_issues=1,
                issues_by_tool={"ruff": 1, "bandit": 1, "radon": 1},
            )
            mock_run_tools.return_value = mock_result

            result = await self.engine.execute(files=[test_file], mode=QualityMode.COMPREHENSIVE)

            assert result.success is True
            assert result.total_issues == 3
            assert len(result.issues_by_tool) == 3
            mock_run_tools.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
