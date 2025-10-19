#!/usr/bin/env python3
"""
Comprehensive tests for AI fix applier module.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest


# Import the modules we're testing
try:
    from autopr.actions.ai_linting_fixer.ai_fix_applier import (
        AIFixApplier,
        FixAnalyzer,
        FixApplier,
        FixConfig,
        FixGenerator,
        FixReporter,
        FixValidator,
    )
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestFixConfig:
    """Test FixConfig class."""

    def test_fix_config_initialization(self):
        """Test FixConfig initialization."""
        config = FixConfig(
            model_name="gpt-4",
            max_tokens=1000,
            temperature=0.1,
            max_fixes_per_file=5,
            auto_apply=False,
            validate_fixes=True
        )

        assert config.model_name == "gpt-4"
        assert config.max_tokens == 1000
        assert config.temperature == 0.1
        assert config.max_fixes_per_file == 5
        assert config.auto_apply is False
        assert config.validate_fixes is True

    def test_fix_config_defaults(self):
        """Test FixConfig with default values."""
        config = FixConfig()

        assert config.model_name == "gpt-3.5-turbo"
        assert config.max_tokens == 500
        assert config.temperature == 0.0
        assert config.max_fixes_per_file == 3
        assert config.auto_apply is False
        assert config.validate_fixes is True

    def test_fix_config_to_dict(self):
        """Test FixConfig to_dict method."""
        config = FixConfig(model_name="claude-3", max_tokens=2000)

        result = config.to_dict()
        assert result["model_name"] == "claude-3"
        assert result["max_tokens"] == 2000

    def test_fix_config_from_dict(self):
        """Test FixConfig from_dict method."""
        data = {
            "model_name": "llama-2",
            "max_tokens": 1500,
            "temperature": 0.15,
            "auto_apply": True
        }

        config = FixConfig.from_dict(data)
        assert config.model_name == "llama-2"
        assert config.max_tokens == 1500
        assert config.temperature == 0.15
        assert config.auto_apply is True

    def test_fix_config_validation(self):
        """Test FixConfig validation."""
        valid_config = FixConfig(model_name="gpt-4", max_tokens=1000)
        assert valid_config.is_valid() is True

        invalid_config = FixConfig(model_name="", max_tokens=0)
        assert invalid_config.is_valid() is False


class TestFixGenerator:
    """Test FixGenerator class."""

    @pytest.fixture
    def fix_generator(self):
        """Create a FixGenerator instance for testing."""
        config = FixConfig(model_name="test-model")
        return FixGenerator(config)

    def test_fix_generator_initialization(self, fix_generator):
        """Test FixGenerator initialization."""
        assert fix_generator.config is not None
        assert fix_generator.llm_client is not None

    def test_generate_fix_for_issue(self, fix_generator):
        """Test generating a fix for a specific issue."""
        issue = {
            "type": "syntax_error",
            "message": "Missing colon after function definition",
            "line": 5
        }

        code_content = "def test_function()\n    return True"

        with patch.object(fix_generator.llm_client, 'generate') as mock_generate:
            mock_generate.return_value = "def test_function():\n    return True"

            result = fix_generator.generate_fix_for_issue(issue, code_content)

            assert result is not None
            assert "def test_function():" in result

    def test_generate_fixes_for_file(self, fix_generator):
        """Test generating fixes for an entire file."""
        issues = [
            {"type": "syntax_error", "message": "Missing colon", "line": 1},
            {"type": "style_issue", "message": "Line too long", "line": 2}
        ]

        code_content = "def test_function()\n    return True"

        with patch.object(fix_generator.llm_client, 'generate') as mock_generate:
            mock_generate.return_value = "def test_function():\n    return True"

            results = fix_generator.generate_fixes_for_file(issues, code_content)

            assert len(results) == 2
            assert all(result is not None for result in results)


class TestFixValidator:
    """Test FixValidator class."""

    @pytest.fixture
    def fix_validator(self):
        """Create a FixValidator instance for testing."""
        return FixValidator()

    def test_fix_validator_initialization(self, fix_validator):
        """Test FixValidator initialization."""
        assert fix_validator.validation_rules == []
        assert fix_validator.error_messages == []

    def test_validate_fix_syntax(self, fix_validator):
        """Test validating fix syntax."""
        valid_fix = "def test_function():\n    return True"
        result = fix_validator.validate_fix_syntax(valid_fix, "python")
        assert result.is_valid is True

        invalid_fix = "def test_function()\n    return True"
        result = fix_validator.validate_fix_syntax(invalid_fix, "python")
        assert result.is_valid is False

    def test_validate_fix_semantics(self, fix_validator):
        """Test validating fix semantics."""
        original_code = "x = 5\ny = 10\nresult = x + y"
        fix_code = "x = 5\ny = 10\nresult = x + y"

        result = fix_validator.validate_fix_semantics(original_code, fix_code)
        assert result.is_valid is True

    def test_validate_fix_completeness(self, fix_validator):
        """Test validating fix completeness."""
        issue = {"type": "syntax_error", "message": "Missing colon", "line": 1}
        original_code = "def test_function()\n    return True"
        fix_code = "def test_function():\n    return True"

        result = fix_validator.validate_fix_completeness(issue, original_code, fix_code)
        assert result.is_valid is True


class TestFixApplier:
    """Test FixApplier class."""

    @pytest.fixture
    def fix_applier(self):
        """Create a FixApplier instance for testing."""
        config = FixConfig(backup_files=True)
        return FixApplier(config)

    def test_fix_applier_initialization(self, fix_applier):
        """Test FixApplier initialization."""
        assert fix_applier.config is not None
        assert fix_applier.validator is not None

    def test_apply_fix_to_file(self, fix_applier):
        """Test applying a fix to a file."""
        original_content = "def test_function()\n    return True"
        fix_content = "def test_function():\n    return True"

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write(original_content)
            temp_file = f.name

        try:
            result = fix_applier.apply_fix_to_file(temp_file, fix_content)
            assert result is True

            with open(temp_file) as f:
                applied_content = f.read()
            assert applied_content == fix_content

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_apply_fix_with_backup(self, fix_applier):
        """Test applying a fix with backup."""
        original_content = "def test_function()\n    return True"
        fix_content = "def test_function():\n    return True"

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write(original_content)
            temp_file = f.name

        try:
            result = fix_applier.apply_fix_with_backup(temp_file, fix_content)
            assert result is True

            backup_files = [f for f in os.listdir(os.path.dirname(temp_file))
                          if f.startswith(os.path.basename(temp_file) + ".backup")]
            assert len(backup_files) > 0

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestFixAnalyzer:
    """Test FixAnalyzer class."""

    @pytest.fixture
    def fix_analyzer(self):
        """Create a FixAnalyzer instance for testing."""
        return FixAnalyzer()

    def test_fix_analyzer_initialization(self, fix_analyzer):
        """Test FixAnalyzer initialization."""
        assert fix_analyzer.analysis_cache == {}
        assert fix_analyzer.analysis_rules == []

    def test_analyze_fix_quality(self, fix_analyzer):
        """Test analyzing fix quality."""
        original_code = "def test_function()\n    return True"
        fix_code = "def test_function():\n    return True"

        result = fix_analyzer.analyze_fix_quality(original_code, fix_code)

        assert "quality_score" in result
        assert "improvements" in result
        assert result["quality_score"] > 0

    def test_analyze_fix_impact(self, fix_analyzer):
        """Test analyzing fix impact."""
        original_code = "def test_function()\n    return True"
        fix_code = "def test_function():\n    return True"

        result = fix_analyzer.analyze_fix_impact(original_code, fix_code)

        assert "impact_score" in result
        assert "changes" in result
        assert "risks" in result


class TestFixReporter:
    """Test FixReporter class."""

    @pytest.fixture
    def fix_reporter(self):
        """Create a FixReporter instance for testing."""
        return FixReporter()

    def test_fix_reporter_initialization(self, fix_reporter):
        """Test FixReporter initialization."""
        assert fix_reporter.report_formats == {}
        assert fix_reporter.default_format == "json"

    def test_generate_fix_report(self, fix_reporter):
        """Test generating a fix report."""
        fix_data = {
            "file": "test.py",
            "original_code": "def test_function()\n    return True",
            "fixed_code": "def test_function():\n    return True",
            "issues_fixed": ["syntax_error"],
            "quality_score": 0.9
        }

        report = fix_reporter.generate_fix_report(fix_data)

        assert "file" in report
        assert "issues_fixed" in report
        assert "quality_score" in report

    def test_generate_fix_summary(self, fix_reporter):
        """Test generating a fix summary."""
        fixes = [
            {"file": "file1.py", "issues_fixed": ["syntax_error"], "quality_score": 0.9},
            {"file": "file2.py", "issues_fixed": ["style_issue"], "quality_score": 0.8}
        ]

        summary = fix_reporter.generate_fix_summary(fixes)

        assert "total_fixes" in summary
        assert "average_quality_score" in summary
        assert summary["total_fixes"] == 2


class TestAIFixApplier:
    """Test AIFixApplier class."""

    @pytest.fixture
    def ai_fix_applier(self):
        """Create an AIFixApplier instance for testing."""
        config = FixConfig(model_name="test-model")
        return AIFixApplier(config)

    def test_ai_fix_applier_initialization(self, ai_fix_applier):
        """Test AIFixApplier initialization."""
        assert ai_fix_applier.config is not None
        assert ai_fix_applier.generator is not None
        assert ai_fix_applier.validator is not None
        assert ai_fix_applier.applier is not None
        assert ai_fix_applier.analyzer is not None
        assert ai_fix_applier.reporter is not None

    def test_apply_fix_to_file(self, ai_fix_applier):
        """Test applying AI fix to a file."""
        file_content = "def test_function()\n    return True"
        issues = [{"type": "syntax_error", "message": "Missing colon", "line": 1}]

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write(file_content)
            temp_file = f.name

        try:
            with patch.object(ai_fix_applier.generator, 'generate_fix_for_issue') as mock_generate:
                mock_generate.return_value = "def test_function():\n    return True"

                result = ai_fix_applier.apply_fix_to_file(temp_file, issues)

                assert result.success is True
                assert result.fixes_applied == 1

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_validate_and_apply_fix(self, ai_fix_applier):
        """Test validating and applying a fix."""
        original_code = "def test_function()\n    return True"
        fix_code = "def test_function():\n    return True"

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write(original_code)
            temp_file = f.name

        try:
            with patch.object(ai_fix_applier.validator, 'validate_fix_comprehensive') as mock_validate:
                mock_validate.return_value = Mock(is_valid=True, checks={})

                result = ai_fix_applier.validate_and_apply_fix(temp_file, fix_code)

                assert result.success is True
                assert result.validated is True

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_get_fix_statistics(self, ai_fix_applier):
        """Test getting fix statistics."""
        stats = ai_fix_applier.get_fix_statistics()

        assert "total_fixes_applied" in stats
        assert "successful_fixes" in stats
        assert "failed_fixes" in stats
        assert "average_quality_score" in stats

    def test_generate_fix_report(self, ai_fix_applier):
        """Test generating a comprehensive fix report."""
        report = ai_fix_applier.generate_fix_report()

        assert "summary" in report
        assert "details" in report
        assert "statistics" in report
        assert "recommendations" in report
