"""
Comprehensive tests for AI Fix Applier module.
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Add the parent directory to sys.path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from autopr.actions.ai_linting_fixer.ai_fix_applier import AIFixApplier
    from autopr.actions.ai_linting_fixer.backup_manager import BackupManager
    from autopr.actions.ai_linting_fixer.file_splitter import SplitConfig
    from autopr.actions.ai_linting_fixer.models import LintingIssue
    from autopr.actions.ai_linting_fixer.validation_manager import \
        ValidationConfig
    from autopr.actions.llm.manager import ActionLLMProviderManager
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}")


class TestAIFixApplier:
    """Comprehensive tests for AIFixApplier class."""

    @pytest.fixture
    def mock_llm_manager(self):
        """Create a mock LLM manager."""
        manager = Mock(spec=ActionLLMProviderManager)
        manager.default_provider = "azure_openai"
        manager.complete = AsyncMock()
        return manager

    @pytest.fixture
    def mock_backup_manager(self):
        """Create a mock backup manager."""
        manager = Mock(spec=BackupManager)
        manager.sessions = {}
        manager.start_session = Mock()
        manager.backup_file = Mock(return_value="backup_path")
        manager.restore_file = Mock(return_value=True)
        return manager

    @pytest.fixture
    def sample_issues(self):
        """Create sample linting issues."""
        return [
            LintingIssue(
                error_code="E501",
                message="Line too long",
                line_number=10,
                column=80,
                file_path="test_file.py"
            ),
            LintingIssue(
                error_code="F401",
                message="Unused import",
                line_number=5,
                column=1,
                file_path="test_file.py"
            )
        ]

    @pytest.fixture
    def ai_fix_applier(self, mock_llm_manager, mock_backup_manager):
        """Create an AIFixApplier instance for testing."""
        validation_config = ValidationConfig()
        split_config = SplitConfig()
        
        return AIFixApplier(
            llm_manager=mock_llm_manager,
            backup_manager=mock_backup_manager,
            validation_config=validation_config,
            split_config=split_config
        )

    def test_initialization(self, mock_llm_manager):
        """Test AIFixApplier initialization."""
        applier = AIFixApplier(mock_llm_manager)
        
        assert applier.llm_manager == mock_llm_manager
        assert applier.enable_validation is True
        assert applier.enable_backup is True
        assert applier.enable_splitting is True
        assert applier.enable_test_generation is True

    def test_initialization_with_none_llm_manager(self):
        """Test that initialization fails with None LLM manager."""
        with pytest.raises(ValueError, match="llm_manager is required"):
            AIFixApplier(None)

    def test_extract_code_from_response(self, ai_fix_applier):
        """Test _extract_code_from_response method."""
        # Test with code block
        response_with_block = '''
        Here's the fixed code:
        ```python
        def fixed_function():
            return True
        ```
        '''
        result = ai_fix_applier._extract_code_from_response(response_with_block)
        assert "def fixed_function()" in result
        
        # Test with line changes
        response_with_lines = '''
        Line 10: def fixed_function():
        Line 11:     return True
        '''
        result = ai_fix_applier._extract_code_from_response(response_with_lines)
        assert "def fixed_function()" in result
        
        # Test with no code
        result = ai_fix_applier._extract_code_from_response("No code here")
        assert result is None

    def test_is_complete_file(self, ai_fix_applier):
        """Test _is_complete_file method."""
        # Test complete file
        complete_file = '''
        import os
        import sys
        
        def test_function():
            return True
        
        class TestClass:
            def __init__(self):
                pass
        '''
        assert ai_fix_applier._is_complete_file(complete_file) is True
        
        # Test incomplete file
        incomplete_file = "def test_function():"
        assert ai_fix_applier._is_complete_file(incomplete_file) is False

    def test_validate_fix(self, ai_fix_applier, sample_issues):
        """Test _validate_fix method."""
        original = "def test(): pass"
        fixed = "def test():\n    return True"
        
        result = ai_fix_applier._validate_fix(original, fixed, sample_issues)
        assert result["is_valid"] is True
        
        # Test with syntax error
        invalid_fix = "def test(: invalid syntax"
        result = ai_fix_applier._validate_fix(original, invalid_fix, sample_issues)
        assert result["is_valid"] is False

    def test_apply_targeted_changes(self, ai_fix_applier):
        """Test _apply_targeted_changes method."""
        original_content = "line1\\nline2\\nline3"
        ai_response = "Line 2: modified line2"
        issue_lines = [2]
        
        result = ai_fix_applier._apply_targeted_changes(original_content, ai_response, issue_lines)
        assert "modified line2" in result
        
        # Test with no changes
        result = ai_fix_applier._apply_targeted_changes(original_content, "No changes", issue_lines)
        assert result == original_content


class TestAIFixApplierIntegration:
    """Integration tests for AIFixApplier."""

    @pytest.mark.asyncio
    async def test_full_fix_workflow(self, tmp_path):
        """Test the complete fix workflow."""
        # This would test the entire workflow from start to finish
        # Implementation would depend on having a real LLM manager configured
        pass

    def test_backup_and_restore_workflow(self, tmp_path):
        """Test backup and restore functionality."""
        # This would test the backup/restore workflow
        pass


if __name__ == "__main__":
    pytest.main([__file__])
