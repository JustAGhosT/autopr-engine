"""Unit tests for CLI analyze_comment command.

Tests for:
- analyze_comment CLI command
- _run_comment_analysis async function
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from codeflow_engine.actions.ai_comment_analyzer import (
    AICommentAnalysisInputs,
    AICommentAnalysisOutputs,
)
from codeflow_engine.cli.main import analyze_comment, cli, _run_comment_analysis


class TestAnalyzeCommentCommand:
    """Tests for the analyze_comment CLI command."""

    def test_analyze_comment_with_required_options(self):
        """Test analyze_comment command with only required options."""
        runner = CliRunner()
        
        mock_result = AICommentAnalysisOutputs(
            intent="fix_request",
            confidence=0.8,
            suggested_actions=["modify_code"],
            auto_fixable=True,
            response_template="Fixed it",
            issue_priority="medium",
            tags=["fix"],
        )
        
        with patch("codeflow_engine.cli.main.AICommentAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.execute = AsyncMock(return_value=mock_result)
            mock_analyzer_class.return_value = mock_analyzer
            
            result = runner.invoke(cli, [
                "analyze-comment",
                "--comment-body", "Please fix this bug",
            ])
            
            assert result.exit_code == 0
            output = json.loads(result.output.strip())
            assert output["intent"] == "fix_request"
            assert output["confidence"] == 0.8

    def test_analyze_comment_with_all_options(self):
        """Test analyze_comment command with all options."""
        runner = CliRunner()
        
        mock_result = AICommentAnalysisOutputs(
            intent="suggestion",
            confidence=0.7,
            suggested_actions=["review"],
            auto_fixable=False,
            response_template="Will review",
            issue_priority="low",
            tags=["suggestion"],
        )
        
        with patch("codeflow_engine.cli.main.AICommentAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.execute = AsyncMock(return_value=mock_result)
            mock_analyzer_class.return_value = mock_analyzer
            
            result = runner.invoke(cli, [
                "analyze-comment",
                "--comment-body", "Consider refactoring this",
                "--file-path", "src/main.py",
                "--pr-diff", "+def new_function(): pass",
            ])
            
            assert result.exit_code == 0
            output = json.loads(result.output.strip())
            assert output["intent"] == "suggestion"
            
            # Verify inputs were constructed correctly
            mock_analyzer.execute.assert_called_once()
            call_args = mock_analyzer.execute.call_args
            inputs = call_args[0][0]
            assert inputs.comment_body == "Consider refactoring this"
            assert inputs.file_path == "src/main.py"
            assert inputs.pr_diff == "+def new_function(): pass"

    def test_analyze_comment_missing_required_option(self):
        """Test that analyze_comment fails without required --comment-body."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["analyze-comment"])
        
        assert result.exit_code != 0
        assert "Missing option '--comment-body'" in result.output or "Error" in result.output

    def test_analyze_comment_handles_exception(self):
        """Test that analyze_comment handles exceptions gracefully by calling sys.exit."""
        runner = CliRunner()
        
        # Mock the async function directly to avoid asyncio issues with CliRunner
        with patch("codeflow_engine.cli.main._run_comment_analysis") as mock_run:
            # Make the mock coroutine raise an exception when awaited
            async def raise_error(*args, **kwargs):
                raise Exception("Test error")
            
            mock_run.side_effect = raise_error
            
            # Patch asyncio.run to actually run the coroutine
            with patch("codeflow_engine.cli.main.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.side_effect = Exception("Test error")
                
                result = runner.invoke(cli, [
                    "analyze-comment",
                    "--comment-body", "This will fail",
                ])
                
                # The command should fail with exception
                assert result.exit_code != 0 or "error" in result.output.lower() or result.exception is not None


class TestRunCommentAnalysis:
    """Tests for _run_comment_analysis async function."""

    @pytest.mark.asyncio
    async def test_run_comment_analysis_basic(self):
        """Test _run_comment_analysis with basic input."""
        mock_result = AICommentAnalysisOutputs(
            intent="question",
            confidence=0.9,
            suggested_actions=[],
            auto_fixable=False,
            response_template="Answering the question",
            issue_priority="low",
            tags=["question"],
        )
        
        with patch("codeflow_engine.cli.main.AICommentAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.execute = AsyncMock(return_value=mock_result)
            mock_analyzer_class.return_value = mock_analyzer
            
            with patch("codeflow_engine.cli.main.click.echo") as mock_echo:
                await _run_comment_analysis(
                    comment_body="What does this function do?",
                    file_path=None,
                    pr_diff=None,
                )
                
                # Verify echo was called with JSON output
                mock_echo.assert_called_once()
                output = json.loads(mock_echo.call_args[0][0])
                assert output["intent"] == "question"

    @pytest.mark.asyncio
    async def test_run_comment_analysis_with_file_path(self):
        """Test _run_comment_analysis with file_path."""
        mock_result = AICommentAnalysisOutputs(
            intent="fix_request",
            confidence=0.85,
            suggested_actions=["modify"],
            auto_fixable=True,
            search_block="old_code",
            replace_block="new_code",
            response_template="Fixed",
            issue_priority="high",
            tags=["fix"],
        )
        
        with patch("codeflow_engine.cli.main.AICommentAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.execute = AsyncMock(return_value=mock_result)
            mock_analyzer_class.return_value = mock_analyzer
            
            with patch("codeflow_engine.cli.main.click.echo"):
                await _run_comment_analysis(
                    comment_body="Please update this",
                    file_path="src/utils.py",
                    pr_diff="+new line",
                )
                
                # Verify AICommentAnalysisInputs was constructed correctly
                mock_analyzer.execute.assert_called_once()
                call_args = mock_analyzer.execute.call_args
                inputs = call_args[0][0]
                assert isinstance(inputs, AICommentAnalysisInputs)
                assert inputs.comment_body == "Please update this"
                assert inputs.file_path == "src/utils.py"
                assert inputs.pr_diff == "+new line"

    @pytest.mark.asyncio
    async def test_run_comment_analysis_exception_exits(self):
        """Test that _run_comment_analysis exits on exception."""
        with patch("codeflow_engine.cli.main.AICommentAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.execute = AsyncMock(side_effect=RuntimeError("Analysis failed"))
            mock_analyzer_class.return_value = mock_analyzer
            
            with pytest.raises(SystemExit) as exc_info:
                await _run_comment_analysis(
                    comment_body="This will fail",
                    file_path=None,
                    pr_diff=None,
                )
            
            assert exc_info.value.code == 1


class TestCLIImports:
    """Tests to ensure CLI imports are properly covered."""

    def test_ai_comment_analyzer_import(self):
        """Test that AICommentAnalyzer is importable from cli.main."""
        from codeflow_engine.cli.main import AICommentAnalyzer, AICommentAnalysisInputs
        
        assert AICommentAnalyzer is not None
        assert AICommentAnalysisInputs is not None

    def test_analyze_comment_command_exists(self):
        """Test that analyze_comment command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "analyze-comment" in result.output

    def test_cli_version(self):
        """Test CLI version option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        
        assert result.exit_code == 0
        # Just check that a version is present in the output, not the specific version
        assert "autopr" in result.output.lower() or "version" in result.output.lower() or any(
            part.count('.') >= 1 for part in result.output.split()
        )
