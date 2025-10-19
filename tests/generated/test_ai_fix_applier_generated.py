"""
Generated tests for ai_fix_applier module.
"""

from pathlib import Path
import sys
from unittest.mock import Mock, patch

import pytest


# Add the parent directory to sys.path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from autopr.actions.ai_linting_fixer.ai_fix_applier import AIFixApplier
except ImportError:
    # If direct import fails, try alternative approaches
    pytest.skip("Could not import ai_fix_applier module", allow_module_level=True)


def test___init__():
    """Test __init__ function."""
    # Test AIFixApplier initialization
    mock_llm_manager = Mock()
    applier = AIFixApplier(mock_llm_manager)
    assert applier is not None
    assert applier.llm_manager == mock_llm_manager


def test__apply_targeted_changes():
    """Test _apply_targeted_changes function."""
    mock_llm_manager = Mock()
    applier = AIFixApplier(mock_llm_manager)

    # Test applying targeted changes to code
    original_code = "def test():\n    return True"
    changes = [{"line": 1, "content": "def test():\n    return False"}]

    with patch.object(applier, '_validate_fix', return_value=True):
        result = applier._apply_targeted_changes(original_code, changes)
        assert result is not None
        assert "return False" in result


def test__extract_code_from_response():
    """Test _extract_code_from_response function."""
    mock_llm_manager = Mock()
    applier = AIFixApplier(mock_llm_manager)

    # Test extracting code from LLM response
    response = "Here's the fixed code:\n```python\ndef test():\n    return True\n```"

    result = applier._extract_code_from_response(response)
    assert result is not None
    assert "def test():" in result
    assert "return True" in result

    # Test with no code blocks
    response_no_code = "This is just text without code blocks"
    result = applier._extract_code_from_response(response_no_code)
    assert result == response_no_code


def test__is_complete_file():
    """Test _is_complete_file function."""
    mock_llm_manager = Mock()
    applier = AIFixApplier(mock_llm_manager)

    # Test complete file detection
    complete_code = "#!/usr/bin/env python3\n\ndef test():\n    return True\n\nif __name__ == '__main__':\n    test()"
    assert applier._is_complete_file(complete_code) is True

    # Test incomplete code
    incomplete_code = "def test():\n    return True"
    assert applier._is_complete_file(incomplete_code) is False


def test__extract_targeted_changes():
    """Test _extract_targeted_changes function."""
    mock_llm_manager = Mock()
    applier = AIFixApplier(mock_llm_manager)

    # Test extracting targeted changes from response
    response = "Change line 5 to: return False"

    with patch.object(applier, '_parse_change_instructions', return_value=[{"line": 5, "content": "return False"}]):
        changes = applier._extract_targeted_changes(response)
        assert len(changes) == 1
        assert changes[0]["line"] == 5
        assert changes[0]["content"] == "return False"


def test__validate_fix():
    """Test _validate_fix function."""
    mock_llm_manager = Mock()
    applier = AIFixApplier(mock_llm_manager)

    # Test valid fix
    original_code = "def test():\n    return True"
    fixed_code = "def test():\n    return False"

    with patch.object(applier, '_syntax_check', return_value=True):
        result = applier._validate_fix(original_code, fixed_code)
        assert result is True

    # Test invalid fix
    invalid_code = "def test():\n    return True\n    invalid syntax"

    with patch.object(applier, '_syntax_check', return_value=False):
        result = applier._validate_fix(original_code, invalid_code)
        assert result is False


def test_apply_ruff_auto_fix():
    """Test apply_ruff_auto_fix function."""
    mock_llm_manager = Mock()
    applier = AIFixApplier(mock_llm_manager)

    # Test applying ruff auto-fixes
    file_path = "test_file.py"
    issues = [{"line": 1, "message": "Missing newline at end of file"}]

    with patch.object(applier, '_run_ruff_fix', return_value=True):
        with patch.object(applier, '_read_file', return_value="def test():\n    return True"):
            with patch.object(applier, '_write_file'):
                result = applier.apply_ruff_auto_fix(file_path, issues)
                assert result is True


class TestAIFixApplier:
    """Test AIFixApplier class."""

    def test_AIFixApplier_initialization(self):
        """Test AIFixApplier initialization."""
        mock_llm_manager = Mock()
        applier = AIFixApplier(mock_llm_manager)
        assert applier is not None
        assert applier.llm_manager == mock_llm_manager
        assert hasattr(applier, '_apply_targeted_changes')
        assert hasattr(applier, '_extract_code_from_response')

    def test_AIFixApplier___init__(self):
        """Test AIFixApplier.__init__ method."""
        mock_llm_manager = Mock()
        applier = AIFixApplier(mock_llm_manager)
        assert applier.llm_manager == mock_llm_manager

    def test_AIFixApplier__apply_targeted_changes(self):
        """Test AIFixApplier._apply_targeted_changes method."""
        mock_llm_manager = Mock()
        applier = AIFixApplier(mock_llm_manager)

        original_code = "def test():\n    return True"
        changes = [{"line": 2, "content": "    return False"}]

        with patch.object(applier, '_validate_fix', return_value=True):
            result = applier._apply_targeted_changes(original_code, changes)
            assert result is not None
            assert "return False" in result

    def test_AIFixApplier__extract_code_from_response(self):
        """Test AIFixApplier._extract_code_from_response method."""
        mock_llm_manager = Mock()
        applier = AIFixApplier(mock_llm_manager)

        response = "```python\ndef test():\n    return True\n```"
        result = applier._extract_code_from_response(response)
        assert result is not None
        assert "def test():" in result

    def test_AIFixApplier__is_complete_file(self):
        """Test AIFixApplier._is_complete_file method."""
        mock_llm_manager = Mock()
        applier = AIFixApplier(mock_llm_manager)

        # Test complete file
        complete_code = "#!/usr/bin/env python3\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()"
        assert applier._is_complete_file(complete_code) is True

        # Test incomplete file
        incomplete_code = "def test():\n    return True"
        assert applier._is_complete_file(incomplete_code) is False

    def test_AIFixApplier__extract_targeted_changes(self):
        """Test AIFixApplier._extract_targeted_changes method."""
        mock_llm_manager = Mock()
        applier = AIFixApplier(mock_llm_manager)

        response = "Change line 3 to: return False"

        with patch.object(applier, '_parse_change_instructions', return_value=[{"line": 3, "content": "return False"}]):
            changes = applier._extract_targeted_changes(response)
            assert len(changes) == 1
            assert changes[0]["line"] == 3

    def test_AIFixApplier__validate_fix(self):
        """Test AIFixApplier._validate_fix method."""
        mock_llm_manager = Mock()
        applier = AIFixApplier(mock_llm_manager)

        original_code = "def test():\n    return True"
        fixed_code = "def test():\n    return False"

        with patch.object(applier, '_syntax_check', return_value=True):
            result = applier._validate_fix(original_code, fixed_code)
            assert result is True
