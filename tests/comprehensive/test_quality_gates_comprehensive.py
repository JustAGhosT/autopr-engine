#!/usr/bin/env python3
"""
Comprehensive tests for quality gates module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the modules we're testing
try:
    from codeflow_engine.actions.quality_gates import (QualityGateChecker,
                                              QualityGateConfig,
                                              QualityGateInputs,
                                              QualityGateOutputs,
                                              QualityGateResult, QualityGates,
                                              QualityGateValidator)
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestQualityGateInputs:
    """Test QualityGateInputs class."""

    def test_quality_gate_inputs_initialization(self):
        """Test QualityGateInputs initialization."""
        inputs = QualityGateInputs(
            file_path="test.py",
            code_content="def test(): pass",
            quality_threshold=0.8,
            checks=["syntax", "style", "complexity"]
        )
        
        assert inputs.file_path == "test.py"
        assert inputs.code_content == "def test(): pass"
        assert inputs.quality_threshold == 0.8
        assert inputs.checks == ["syntax", "style", "complexity"]

    def test_quality_gate_inputs_defaults(self):
        """Test QualityGateInputs with default values."""
        inputs = QualityGateInputs(file_path="test.py")
        
        assert inputs.file_path == "test.py"
        assert inputs.code_content == ""
        assert inputs.quality_threshold == 0.7
        assert inputs.checks == ["syntax", "style"]

    def test_quality_gate_inputs_to_dict(self):
        """Test QualityGateInputs to_dict method."""
        inputs = QualityGateInputs(
            file_path="test.py",
            code_content="def test(): pass",
            quality_threshold=0.9,
            checks=["syntax", "style", "complexity", "security"]
        )
        
        result = inputs.to_dict()
        expected = {
            "file_path": "test.py",
            "code_content": "def test(): pass",
            "quality_threshold": 0.9,
            "checks": ["syntax", "style", "complexity", "security"]
        }
        assert result == expected

    def test_quality_gate_inputs_from_dict(self):
        """Test QualityGateInputs from_dict method."""
        data = {
            "file_path": "test.py",
            "code_content": "def test(): pass",
            "quality_threshold": 0.85,
            "checks": ["syntax", "style"]
        }
        
        inputs = QualityGateInputs.from_dict(data)
        assert inputs.file_path == "test.py"
        assert inputs.code_content == "def test(): pass"
        assert inputs.quality_threshold == 0.85
        assert inputs.checks == ["syntax", "style"]


class TestQualityGateOutputs:
    """Test QualityGateOutputs class."""

    def test_quality_gate_outputs_initialization(self):
        """Test QualityGateOutputs initialization."""
        outputs = QualityGateOutputs(
            passed=True,
            score=0.85,
            issues=["line too long", "missing docstring"],
            recommendations=["add docstring", "shorten line"]
        )
        
        assert outputs.passed is True
        assert outputs.score == 0.85
        assert outputs.issues == ["line too long", "missing docstring"]
        assert outputs.recommendations == ["add docstring", "shorten line"]

    def test_quality_gate_outputs_defaults(self):
        """Test QualityGateOutputs with default values."""
        outputs = QualityGateOutputs()
        
        assert outputs.passed is False
        assert outputs.score == 0.0
        assert outputs.issues == []
        assert outputs.recommendations == []

    def test_quality_gate_outputs_to_dict(self):
        """Test QualityGateOutputs to_dict method."""
        outputs = QualityGateOutputs(
            passed=True,
            score=0.92,
            issues=["minor style issue"],
            recommendations=["consider adding type hints"]
        )
        
        result = outputs.to_dict()
        expected = {
            "passed": True,
            "score": 0.92,
            "issues": ["minor style issue"],
            "recommendations": ["consider adding type hints"]
        }
        assert result == expected

    def test_quality_gate_outputs_from_dict(self):
        """Test QualityGateOutputs from_dict method."""
        data = {
            "passed": False,
            "score": 0.65,
            "issues": ["syntax error", "complexity too high"],
            "recommendations": ["fix syntax", "refactor code"]
        }
        
        outputs = QualityGateOutputs.from_dict(data)
        assert outputs.passed is False
        assert outputs.score == 0.65
        assert outputs.issues == ["syntax error", "complexity too high"]
        assert outputs.recommendations == ["fix syntax", "refactor code"]


class TestQualityGateResult:
    """Test QualityGateResult class."""

    def test_quality_gate_result_initialization(self):
        """Test QualityGateResult initialization."""
        result = QualityGateResult(
            check_name="syntax",
            passed=True,
            score=0.95,
            details="No syntax errors found",
            errors=[]
        )
        
        assert result.check_name == "syntax"
        assert result.passed is True
        assert result.score == 0.95
        assert result.details == "No syntax errors found"
        assert result.errors == []

    def test_quality_gate_result_with_errors(self):
        """Test QualityGateResult with errors."""
        errors = ["SyntaxError: invalid syntax", "IndentationError: unexpected indent"]
        result = QualityGateResult(
            check_name="syntax",
            passed=False,
            score=0.0,
            details="Multiple syntax errors found",
            errors=errors
        )
        
        assert result.check_name == "syntax"
        assert result.passed is False
        assert result.score == 0.0
        assert result.details == "Multiple syntax errors found"
        assert result.errors == errors

    def test_quality_gate_result_to_dict(self):
        """Test QualityGateResult to_dict method."""
        result = QualityGateResult(
            check_name="style",
            passed=True,
            score=0.88,
            details="Style check passed",
            errors=[]
        )
        
        result_dict = result.to_dict()
        expected = {
            "check_name": "style",
            "passed": True,
            "score": 0.88,
            "details": "Style check passed",
            "errors": []
        }
        assert result_dict == expected

    def test_quality_gate_result_from_dict(self):
        """Test QualityGateResult from_dict method."""
        data = {
            "check_name": "complexity",
            "passed": False,
            "score": 0.45,
            "details": "Cyclomatic complexity too high",
            "errors": ["Function has complexity of 15, max allowed is 10"]
        }
        
        result = QualityGateResult.from_dict(data)
        assert result.check_name == "complexity"
        assert result.passed is False
        assert result.score == 0.45
        assert result.details == "Cyclomatic complexity too high"
        assert result.errors == ["Function has complexity of 15, max allowed is 10"]


class TestQualityGateConfig:
    """Test QualityGateConfig class."""

    def test_quality_gate_config_initialization(self):
        """Test QualityGateConfig initialization."""
        config = QualityGateConfig(
            syntax_check=True,
            style_check=True,
            complexity_check=True,
            security_check=False,
            performance_check=False,
            syntax_threshold=1.0,
            style_threshold=0.8,
            complexity_threshold=0.7,
            security_threshold=0.9,
            performance_threshold=0.6
        )
        
        assert config.syntax_check is True
        assert config.style_check is True
        assert config.complexity_check is True
        assert config.security_check is False
        assert config.performance_check is False
        assert config.syntax_threshold == 1.0
        assert config.style_threshold == 0.8
        assert config.complexity_threshold == 0.7
        assert config.security_threshold == 0.9
        assert config.performance_threshold == 0.6

    def test_quality_gate_config_defaults(self):
        """Test QualityGateConfig with default values."""
        config = QualityGateConfig()
        
        assert config.syntax_check is True
        assert config.style_check is True
        assert config.complexity_check is False
        assert config.security_check is False
        assert config.performance_check is False
        assert config.syntax_threshold == 1.0
        assert config.style_threshold == 0.8
        assert config.complexity_threshold == 0.7

    def test_quality_gate_config_to_dict(self):
        """Test QualityGateConfig to_dict method."""
        config = QualityGateConfig(
            syntax_check=True,
            style_check=True,
            complexity_check=True,
            security_check=True,
            performance_check=False
        )
        
        result = config.to_dict()
        expected = {
            "syntax_check": True,
            "style_check": True,
            "complexity_check": True,
            "security_check": True,
            "performance_check": False,
            "syntax_threshold": 1.0,
            "style_threshold": 0.8,
            "complexity_threshold": 0.7,
            "security_threshold": 0.9,
            "performance_threshold": 0.6
        }
        assert result == expected

    def test_quality_gate_config_from_dict(self):
        """Test QualityGateConfig from_dict method."""
        data = {
            "syntax_check": True,
            "style_check": False,
            "complexity_check": True,
            "security_check": False,
            "performance_check": True,
            "syntax_threshold": 1.0,
            "style_threshold": 0.9,
            "complexity_threshold": 0.8,
            "security_threshold": 0.95,
            "performance_threshold": 0.7
        }
        
        config = QualityGateConfig.from_dict(data)
        assert config.syntax_check is True
        assert config.style_check is False
        assert config.complexity_check is True
        assert config.security_check is False
        assert config.performance_check is True
        assert config.syntax_threshold == 1.0
        assert config.style_threshold == 0.9
        assert config.complexity_threshold == 0.8
        assert config.security_threshold == 0.95
        assert config.performance_threshold == 0.7

    def test_quality_gate_config_get_enabled_checks(self):
        """Test getting enabled checks from config."""
        config = QualityGateConfig(
            syntax_check=True,
            style_check=True,
            complexity_check=False,
            security_check=True,
            performance_check=False
        )
        
        enabled_checks = config.get_enabled_checks()
        assert "syntax" in enabled_checks
        assert "style" in enabled_checks
        assert "security" in enabled_checks
        assert "complexity" not in enabled_checks
        assert "performance" not in enabled_checks


class TestQualityGateChecker:
    """Test QualityGateChecker class."""

    @pytest.fixture
    def quality_checker(self):
        """Create a QualityGateChecker instance for testing."""
        return QualityGateChecker()

    def test_quality_checker_initialization(self, quality_checker):
        """Test QualityGateChecker initialization."""
        assert quality_checker.config is not None
        assert quality_checker.checkers == {}

    def test_add_checker(self, quality_checker):
        """Test adding a quality checker."""
        def syntax_checker(code_content):
            return QualityGateResult(
                check_name="syntax",
                passed=True,
                score=1.0,
                details="No syntax errors",
                errors=[]
            )
        
        quality_checker.add_checker("syntax", syntax_checker)
        assert "syntax" in quality_checker.checkers

    def test_check_syntax(self, quality_checker):
        """Test syntax checking."""
        valid_code = "def test_function():\n    return True"
        
        result = quality_checker.check_syntax(valid_code)
        assert result.check_name == "syntax"
        assert result.passed is True
        assert result.score > 0.0

    def test_check_syntax_with_error(self, quality_checker):
        """Test syntax checking with error."""
        invalid_code = "def test_function():\n    return True\n    invalid syntax"
        
        result = quality_checker.check_syntax(invalid_code)
        assert result.check_name == "syntax"
        assert result.passed is False
        assert result.score == 0.0
        assert len(result.errors) > 0

    def test_check_style(self, quality_checker):
        """Test style checking."""
        good_style_code = "def test_function():\n    return True"
        
        result = quality_checker.check_style(good_style_code)
        assert result.check_name == "style"
        assert result.score >= 0.0
        assert result.score <= 1.0

    def test_check_style_with_issues(self, quality_checker):
        """Test style checking with issues."""
        bad_style_code = "def test_function():\nreturn True"  # Missing indentation
        
        result = quality_checker.check_style(bad_style_code)
        assert result.check_name == "style"
        assert result.score < 1.0

    def test_check_complexity(self, quality_checker):
        """Test complexity checking."""
        simple_code = "def simple_function():\n    return 1"
        
        result = quality_checker.check_complexity(simple_code)
        assert result.check_name == "complexity"
        assert result.score >= 0.0
        assert result.score <= 1.0

    def test_check_complexity_high(self, quality_checker):
        """Test complexity checking with high complexity."""
        complex_code = """
def complex_function(x):
    if x > 0:
        if x < 10:
            if x % 2 == 0:
                if x % 3 == 0:
                    if x % 5 == 0:
                        return "divisible by 30"
                    else:
                        return "divisible by 6"
                else:
                    return "divisible by 2"
            else:
                return "odd"
        else:
            return "large"
    else:
        return "non-positive"
"""
        
        result = quality_checker.check_complexity(complex_code)
        assert result.check_name == "complexity"
        assert result.score < 1.0  # Should have lower score due to high complexity

    def test_check_security(self, quality_checker):
        """Test security checking."""
        secure_code = "def secure_function():\n    return 'safe'"
        
        result = quality_checker.check_security(secure_code)
        assert result.check_name == "security"
        assert result.score >= 0.0
        assert result.score <= 1.0

    def test_check_security_vulnerable(self, quality_checker):
        """Test security checking with vulnerable code."""
        vulnerable_code = """
import os
def vulnerable_function(user_input):
    os.system(user_input)  # Dangerous!
"""
        
        result = quality_checker.check_security(vulnerable_code)
        assert result.check_name == "security"
        assert result.score < 1.0  # Should have lower score due to security issues

    def test_check_performance(self, quality_checker):
        """Test performance checking."""
        efficient_code = "def efficient_function():\n    return sum(range(100))"
        
        result = quality_checker.check_performance(efficient_code)
        assert result.check_name == "performance"
        assert result.score >= 0.0
        assert result.score <= 1.0

    def test_check_performance_inefficient(self, quality_checker):
        """Test performance checking with inefficient code."""
        inefficient_code = """
def inefficient_function():
    result = []
    for i in range(1000):
        result.append(i)
    return result
"""
        
        result = quality_checker.check_performance(inefficient_code)
        assert result.check_name == "performance"
        assert result.score < 1.0  # Should have lower score due to inefficiency

    def test_run_all_checks(self, quality_checker):
        """Test running all enabled checks."""
        test_code = "def test_function():\n    return True"
        
        results = quality_checker.run_all_checks(test_code)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        for result in results:
            assert isinstance(result, QualityGateResult)
            assert result.check_name in ["syntax", "style", "complexity", "security", "performance"]

    def test_calculate_overall_score(self, quality_checker):
        """Test calculating overall quality score."""
        results = [
            QualityGateResult("syntax", True, 1.0, "No errors", []),
            QualityGateResult("style", True, 0.8, "Minor issues", []),
            QualityGateResult("complexity", True, 0.9, "Good complexity", [])
        ]
        
        overall_score = quality_checker.calculate_overall_score(results)
        assert overall_score >= 0.0
        assert overall_score <= 1.0
        assert overall_score > 0.8  # Should be high with these good results


class TestQualityGateValidator:
    """Test QualityGateValidator class."""

    @pytest.fixture
    def quality_validator(self):
        """Create a QualityGateValidator instance for testing."""
        return QualityGateValidator()

    def test_quality_validator_initialization(self, quality_validator):
        """Test QualityGateValidator initialization."""
        assert quality_validator.checker is not None
        assert quality_validator.config is not None

    def test_validate_fix(self, quality_validator):
        """Test validating a fix."""
        inputs = QualityGateInputs(
            file_path="test.py",
            code_content="def test_function():\n    return True",
            quality_threshold=0.8,
            checks=["syntax", "style"]
        )
        
        outputs = quality_validator.validate_fix(inputs)
        
        assert isinstance(outputs, QualityGateOutputs)
        assert outputs.score >= 0.0
        assert outputs.score <= 1.0

    def test_validate_fix_below_threshold(self, quality_validator):
        """Test validating a fix that's below threshold."""
        # Create code with style issues
        bad_code = "def bad_function():\nreturn True"  # Missing indentation
        
        inputs = QualityGateInputs(
            file_path="test.py",
            code_content=bad_code,
            quality_threshold=0.9,  # High threshold
            checks=["syntax", "style"]
        )
        
        outputs = quality_validator.validate_fix(inputs)
        
        assert isinstance(outputs, QualityGateOutputs)
        assert outputs.passed is False  # Should fail due to style issues
        assert outputs.score < 0.9

    def test_validate_fix_above_threshold(self, quality_validator):
        """Test validating a fix that's above threshold."""
        good_code = "def good_function():\n    return True"
        
        inputs = QualityGateInputs(
            file_path="test.py",
            code_content=good_code,
            quality_threshold=0.7,  # Lower threshold
            checks=["syntax", "style"]
        )
        
        outputs = quality_validator.validate_fix(inputs)
        
        assert isinstance(outputs, QualityGateOutputs)
        assert outputs.passed is True  # Should pass with good code
        assert outputs.score >= 0.7

    def test_validate_fix_with_specific_checks(self, quality_validator):
        """Test validating a fix with specific checks."""
        inputs = QualityGateInputs(
            file_path="test.py",
            code_content="def test_function():\n    return True",
            quality_threshold=0.8,
            checks=["syntax"]  # Only syntax check
        )
        
        outputs = quality_validator.validate_fix(inputs)
        
        assert isinstance(outputs, QualityGateOutputs)
        assert outputs.score >= 0.0
        assert outputs.score <= 1.0

    def test_validate_fix_with_recommendations(self, quality_validator):
        """Test validating a fix that generates recommendations."""
        # Code that could be improved
        improvable_code = "def function():\n    return 1"  # Missing docstring, generic name
        
        inputs = QualityGateInputs(
            file_path="test.py",
            code_content=improvable_code,
            quality_threshold=0.6,
            checks=["syntax", "style"]
        )
        
        outputs = quality_validator.validate_fix(inputs)
        
        assert isinstance(outputs, QualityGateOutputs)
        assert len(outputs.recommendations) > 0  # Should have recommendations

    def test_validate_fix_with_issues(self, quality_validator):
        """Test validating a fix that has issues."""
        problematic_code = "def function():\n    return"  # Missing return value
        
        inputs = QualityGateInputs(
            file_path="test.py",
            code_content=problematic_code,
            quality_threshold=0.8,
            checks=["syntax", "style"]
        )
        
        outputs = quality_validator.validate_fix(inputs)
        
        assert isinstance(outputs, QualityGateOutputs)
        assert len(outputs.issues) > 0  # Should have issues


class TestQualityGates:
    """Test QualityGates class."""

    @pytest.fixture
    def quality_gates(self):
        """Create a QualityGates instance for testing."""
        return QualityGates()

    def test_quality_gates_initialization(self, quality_gates):
        """Test QualityGates initialization."""
        assert quality_gates.validator is not None
        assert quality_gates.config is not None

    def test_quality_gates_action(self, quality_gates):
        """Test quality_gates_action function."""
        inputs = QualityGateInputs(
            file_path="test.py",
            code_content="def test_function():\n    return True",
            quality_threshold=0.8,
            checks=["syntax", "style"]
        )
        
        outputs = quality_gates.quality_gates_action(inputs)
        
        assert isinstance(outputs, QualityGateOutputs)
        assert outputs.score >= 0.0
        assert outputs.score <= 1.0

    def test_validate_fix(self, quality_gates):
        """Test validate_fix method."""
        inputs = QualityGateInputs(
            file_path="test.py",
            code_content="def test_function():\n    return True",
            quality_threshold=0.8,
            checks=["syntax", "style"]
        )
        
        outputs = quality_gates.validate_fix(inputs)
        
        assert isinstance(outputs, QualityGateOutputs)
        assert outputs.score >= 0.0
        assert outputs.score <= 1.0

    def test_check_syntax(self, quality_gates):
        """Test _check_syntax method."""
        valid_code = "def test_function():\n    return True"
        
        result = quality_gates._check_syntax(valid_code)
        assert result.check_name == "syntax"
        assert result.passed is True
        assert result.score > 0.0

    def test_check_style(self, quality_gates):
        """Test _check_style method."""
        good_style_code = "def test_function():\n    return True"
        
        result = quality_gates._check_style(good_style_code)
        assert result.check_name == "style"
        assert result.score >= 0.0
        assert result.score <= 1.0

    def test_check_complexity(self, quality_gates):
        """Test _check_complexity method."""
        simple_code = "def simple_function():\n    return 1"
        
        result = quality_gates._check_complexity(simple_code)
        assert result.check_name == "complexity"
        assert result.score >= 0.0
        assert result.score <= 1.0

    def test_check_security(self, quality_gates):
        """Test _check_security method."""
        secure_code = "def secure_function():\n    return 'safe'"
        
        result = quality_gates._check_security(secure_code)
        assert result.check_name == "security"
        assert result.score >= 0.0
        assert result.score <= 1.0

    def test_check_performance(self, quality_gates):
        """Test _check_performance method."""
        efficient_code = "def efficient_function():\n    return sum(range(100))"
        
        result = quality_gates._check_performance(efficient_code)
        assert result.check_name == "performance"
        assert result.score >= 0.0
        assert result.score <= 1.0

    def test_run_tests(self, quality_gates):
        """Test _run_tests method."""
        test_code = "def test_function():\n    return True"
        
        result = quality_gates._run_tests(test_code)
        assert result.check_name == "tests"
        assert result.score >= 0.0
        assert result.score <= 1.0

    def test_run_test_file(self, quality_gates):
        """Test _run_test_file method."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_function():\n    return True")
            test_file = f.name
        
        try:
            result = quality_gates._run_test_file(test_file)
            assert result.check_name == "tests"
            assert result.score >= 0.0
            assert result.score <= 1.0
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_check_dependencies(self, quality_gates):
        """Test _check_dependencies method."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nimport sys\ndef test_function():\n    return True")
            test_file = f.name
        
        try:
            result = quality_gates._check_dependencies(test_file)
            assert result.check_name == "dependencies"
            assert result.score >= 0.0
            assert result.score <= 1.0
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_calculate_python_complexity(self, quality_gates):
        """Test _calculate_python_complexity method."""
        simple_code = "def simple_function():\n    return 1"
        
        complexity = quality_gates._calculate_python_complexity(simple_code)
        assert complexity >= 1  # At least 1 for the function definition

    def test_calculate_python_complexity_complex(self, quality_gates):
        """Test _calculate_python_complexity method with complex code."""
        complex_code = """
def complex_function(x):
    if x > 0:
        if x < 10:
            return "small positive"
        else:
            return "large positive"
    else:
        return "non-positive"
"""
        
        complexity = quality_gates._calculate_python_complexity(complex_code)
        assert complexity > 1  # Should be higher than simple function

    def test_validate_fix_with_file_path(self, quality_gates):
        """Test validate_fix with file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_function():\n    return True")
            test_file = f.name
        
        try:
            inputs = QualityGateInputs(
                file_path=test_file,
                code_content="",
                quality_threshold=0.8,
                checks=["syntax", "style"]
            )
            
            outputs = quality_gates.validate_fix(inputs)
            
            assert isinstance(outputs, QualityGateOutputs)
            assert outputs.score >= 0.0
            assert outputs.score <= 1.0
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_validate_fix_with_all_checks(self, quality_gates):
        """Test validate_fix with all available checks."""
        inputs = QualityGateInputs(
            file_path="test.py",
            code_content="def test_function():\n    return True",
            quality_threshold=0.5,
            checks=["syntax", "style", "complexity", "security", "performance"]
        )
        
        outputs = quality_gates.validate_fix(inputs)
        
        assert isinstance(outputs, QualityGateOutputs)
        assert outputs.score >= 0.0
        assert outputs.score <= 1.0
        assert len(outputs.issues) >= 0
        assert len(outputs.recommendations) >= 0
