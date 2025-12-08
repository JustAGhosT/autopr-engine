"""Unit tests for AI Comment Analyzer.

Tests for:
- AICommentAnalyzer action
- analyze_comment_with_ai function with file reading
- fallback_analysis function
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codeflow_engine.actions.ai_comment_analyzer import (
    AICommentAnalysisInputs,
    AICommentAnalysisOutputs,
    AICommentAnalyzer,
    analyze_comment_with_ai,
    fallback_analysis,
)


class TestAICommentAnalysisInputs:
    """Tests for AICommentAnalysisInputs model."""

    def test_create_inputs_with_required_fields(self):
        """Test creating inputs with just required fields."""
        inputs = AICommentAnalysisInputs(comment_body="Fix the typo")
        assert inputs.comment_body == "Fix the typo"
        assert inputs.file_path is None
        assert inputs.file_content is None
        assert inputs.surrounding_context is None
        assert inputs.pr_diff is None

    def test_create_inputs_with_all_fields(self):
        """Test creating inputs with all fields."""
        inputs = AICommentAnalysisInputs(
            comment_body="Fix the typo",
            file_path="/path/to/file.py",
            file_content="def foo(): pass",
            surrounding_context="function definition",
            pr_diff="+def foo(): pass",
        )
        assert inputs.comment_body == "Fix the typo"
        assert inputs.file_path == "/path/to/file.py"
        assert inputs.file_content == "def foo(): pass"
        assert inputs.surrounding_context == "function definition"
        assert inputs.pr_diff == "+def foo(): pass"


class TestFallbackAnalysis:
    """Tests for fallback_analysis function."""

    def test_fix_request_intent(self):
        """Test that fix-related keywords are detected."""
        inputs = AICommentAnalysisInputs(comment_body="Please fix this issue")
        result = fallback_analysis(inputs)
        assert result.intent == "fix_request"
        assert result.auto_fixable is True

    def test_question_intent(self):
        """Test that question keywords are detected."""
        inputs = AICommentAnalysisInputs(comment_body="Why is this implemented this way?")
        result = fallback_analysis(inputs)
        assert result.intent == "question"
        assert result.auto_fixable is False

    def test_suggestion_intent_default(self):
        """Test that suggestion is the default intent."""
        inputs = AICommentAnalysisInputs(comment_body="Great work on this PR!")
        result = fallback_analysis(inputs)
        assert result.intent == "suggestion"
        assert result.auto_fixable is False

    def test_update_keyword_detected(self):
        """Test that 'update' keyword triggers fix_request."""
        inputs = AICommentAnalysisInputs(comment_body="Please update the documentation")
        result = fallback_analysis(inputs)
        assert result.intent == "fix_request"

    def test_change_keyword_detected(self):
        """Test that 'change' keyword triggers fix_request."""
        inputs = AICommentAnalysisInputs(comment_body="We should change this variable name")
        result = fallback_analysis(inputs)
        assert result.intent == "fix_request"

    def test_remove_keyword_detected(self):
        """Test that 'remove' keyword triggers fix_request."""
        inputs = AICommentAnalysisInputs(comment_body="Remove this unused import")
        result = fallback_analysis(inputs)
        assert result.intent == "fix_request"

    def test_question_mark_detected(self):
        """Test that ? character triggers question intent."""
        inputs = AICommentAnalysisInputs(comment_body="Is this correct?")
        result = fallback_analysis(inputs)
        assert result.intent == "question"

    def test_how_keyword_detected(self):
        """Test that 'how' keyword triggers question intent."""
        inputs = AICommentAnalysisInputs(comment_body="How does this work")
        result = fallback_analysis(inputs)
        assert result.intent == "question"

    def test_what_keyword_detected(self):
        """Test that 'what' keyword triggers question intent."""
        inputs = AICommentAnalysisInputs(comment_body="What does this function do")
        result = fallback_analysis(inputs)
        assert result.intent == "question"

    def test_result_structure(self):
        """Test that fallback returns correct structure."""
        inputs = AICommentAnalysisInputs(comment_body="Test comment")
        result = fallback_analysis(inputs)
        
        assert isinstance(result, AICommentAnalysisOutputs)
        assert result.confidence == 0.6
        assert result.suggested_actions == ["create_issue"]
        assert result.response_template == "Thanks for the feedback! I'll look into this."
        assert result.issue_priority == "medium"
        assert result.tags == ["needs-review"]


class TestAnalyzeCommentWithAI:
    """Tests for analyze_comment_with_ai function."""

    def test_reads_file_content_when_file_exists(self, tmp_path):
        """Test that file content is read when file_path points to existing file."""
        # Create a temporary file with content using pytest's tmp_path fixture
        temp_file = tmp_path / "test_file.py"
        temp_file.write_text("def example_function():\n    return 42\n")
        temp_file_path = str(temp_file)

        inputs = AICommentAnalysisInputs(
            comment_body="Fix the return value",
            file_path=temp_file_path,
        )
        
        # Mock OpenAI to return a valid response and avoid actual API call
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "intent": "fix_request",
            "confidence": 0.9,
            "suggested_actions": ["modify_code"],
            "auto_fixable": True,
            "search_block": "return 42",
            "replace_block": "return 0",
            "response_template": "Fixed the return value",
            "issue_priority": "medium",
            "tags": ["fix"],
        })
        
        with patch("codeflow_engine.actions.ai_comment_analyzer.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response
            
            result = analyze_comment_with_ai(inputs)
            
            # Verify OpenAI was called
            mock_client.chat.completions.create.assert_called_once()
            
            # Check that the user prompt included file content
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs['messages']
            user_message = next(m for m in messages if m['role'] == 'user')
            assert "def example_function()" in user_message['content']
            assert "return 42" in user_message['content']

    def test_handles_nonexistent_file_path(self):
        """Test that nonexistent file path doesn't cause error."""
        inputs = AICommentAnalysisInputs(
            comment_body="Fix this issue",
            file_path="/nonexistent/path/file.py",
        )
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "intent": "fix_request",
            "confidence": 0.8,
            "suggested_actions": [],
            "auto_fixable": False,
            "search_block": None,
            "replace_block": None,
            "response_template": "Looking into it",
            "issue_priority": "medium",
            "tags": [],
        })
        
        with patch("codeflow_engine.actions.ai_comment_analyzer.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response
            
            result = analyze_comment_with_ai(inputs)
            
            # Should not raise an error
            assert result.intent == "fix_request"

    def test_handles_none_file_path(self):
        """Test that None file_path is handled gracefully."""
        inputs = AICommentAnalysisInputs(
            comment_body="Great work!",
            file_path=None,
        )
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "intent": "praise",
            "confidence": 0.95,
            "suggested_actions": [],
            "auto_fixable": False,
            "search_block": None,
            "replace_block": None,
            "response_template": "Thank you!",
            "issue_priority": "low",
            "tags": ["praise"],
        })
        
        with patch("codeflow_engine.actions.ai_comment_analyzer.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response
            
            result = analyze_comment_with_ai(inputs)
            assert result.intent == "praise"

    def test_fallback_on_api_error(self):
        """Test that fallback is used when OpenAI API fails."""
        inputs = AICommentAnalysisInputs(comment_body="Please fix this bug")
        
        with patch("codeflow_engine.actions.ai_comment_analyzer.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            result = analyze_comment_with_ai(inputs)
            
            # Should use fallback analysis
            assert result.intent == "fix_request"
            assert result.confidence == 0.6

    def test_fallback_on_none_content(self):
        """Test that fallback is used when response content is None."""
        inputs = AICommentAnalysisInputs(comment_body="Why is this?")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        
        with patch("codeflow_engine.actions.ai_comment_analyzer.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response
            
            result = analyze_comment_with_ai(inputs)
            
            # Should use fallback analysis
            assert result.intent == "question"
            assert result.confidence == 0.6

    def test_fallback_on_invalid_json(self):
        """Test that fallback is used when JSON parsing fails."""
        inputs = AICommentAnalysisInputs(comment_body="Update the readme")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is not valid JSON"
        
        with patch("codeflow_engine.actions.ai_comment_analyzer.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response
            
            result = analyze_comment_with_ai(inputs)
            
            # Should use fallback analysis
            assert result.intent == "fix_request"
            assert result.confidence == 0.6


class TestAICommentAnalyzer:
    """Tests for AICommentAnalyzer action class."""

    def test_initialization(self):
        """Test AICommentAnalyzer initialization."""
        analyzer = AICommentAnalyzer()
        assert analyzer.name == "ai_comment_analyzer"
        assert "LLM" in analyzer.description
        assert analyzer.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_execute_calls_analyze_function(self):
        """Test that execute calls analyze_comment_with_ai."""
        analyzer = AICommentAnalyzer()
        inputs = AICommentAnalysisInputs(comment_body="Please remove this line")
        
        with patch("codeflow_engine.actions.ai_comment_analyzer.analyze_comment_with_ai") as mock_analyze:
            mock_analyze.return_value = AICommentAnalysisOutputs(
                intent="fix_request",
                confidence=0.8,
                suggested_actions=["delete_line"],
                auto_fixable=True,
                response_template="Removed the line",
                issue_priority="medium",
                tags=["cleanup"],
            )
            
            result = await analyzer.execute(inputs, {})
            
            mock_analyze.assert_called_once_with(inputs)
            assert result.intent == "fix_request"

    @pytest.mark.asyncio
    async def test_execute_with_context(self):
        """Test that execute passes through context correctly."""
        analyzer = AICommentAnalyzer()
        inputs = AICommentAnalysisInputs(
            comment_body="What does this do?",
            file_path="test.py",
        )
        context = {"pr_number": 42, "repo": "test-repo"}
        
        with patch("codeflow_engine.actions.ai_comment_analyzer.analyze_comment_with_ai") as mock_analyze:
            mock_analyze.return_value = AICommentAnalysisOutputs(
                intent="question",
                confidence=0.9,
                suggested_actions=[],
                auto_fixable=False,
                response_template="This function...",
                issue_priority="low",
                tags=["question"],
            )
            
            result = await analyzer.execute(inputs, context)
            
            # Context is passed but not used by the underlying function
            assert result.intent == "question"
