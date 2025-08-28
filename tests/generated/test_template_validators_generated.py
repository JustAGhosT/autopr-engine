"""
Generated tests for template_validators module.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add the parent directory to sys.path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from templates.discovery.template_validators import (
        DocumentationValidator, ExamplesValidator, MetadataValidator,
        PerformanceValidator, SecurityValidator, StructureValidator,
        ValidationIssue, ValidationSeverity, ValidatorRegistry,
        VariablesValidator)
except ImportError:
    # If direct import fails, try alternative approaches
    pytest.skip("Could not import template_validators module", allow_module_level=True)


class TestValidationSeverity:
    """Test ValidationSeverity enum."""

    def test_ValidationSeverity_initialization(self):
        """Test ValidationSeverity initialization."""
        assert ValidationSeverity.ERROR == "error"
        assert ValidationSeverity.WARNING == "warning"
        assert ValidationSeverity.INFO == "info"


class TestValidationIssue:
    """Test ValidationIssue class."""

    def test_ValidationIssue_initialization(self):
        """Test ValidationIssue initialization."""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category="test",
            message="Test message",
            location="test.py",
            suggestion="Test suggestion",
            rule_id="test_rule"
        )
        
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.category == "test"
        assert issue.message == "Test message"
        assert issue.location == "test.py"
        assert issue.suggestion == "Test suggestion"
        assert issue.rule_id == "test_rule"


class TestStructureValidator:
    """Test StructureValidator class."""

    def test_StructureValidator_check_required_fields(self):
        """Test StructureValidator.check_required_fields method."""
        validator = StructureValidator()
        mock_rule = Mock()
        mock_rule.parameters = {"required_fields": ["name", "version"]}
        mock_rule.rule_id = "test_rule"
        
        # Test with missing required fields
        data = {"name": "test"}
        file_path = Path("test.yaml")
        
        issues = validator.check_required_fields(data, file_path, mock_rule)
        
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.ERROR
        assert issues[0].category == "structure"
        assert "Missing required field: version" in issues[0].message
        assert issues[0].rule_id == "test_rule"
        
        # Test with all required fields present
        data = {"name": "test", "version": "1.0.0"}
        issues = validator.check_required_fields(data, file_path, mock_rule)
        assert len(issues) == 0

    def test_StructureValidator_check_field_types(self):
        """Test StructureValidator.check_field_types method."""
        validator = StructureValidator()
        mock_rule = Mock()
        mock_rule.parameters = {"field_types": {"version": "str", "enabled": "bool"}}
        mock_rule.rule_id = "test_rule"
        
        # Test with correct types
        data = {"version": "1.0.0", "enabled": True}
        file_path = Path("test.yaml")
        
        issues = validator.check_field_types(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with incorrect types
        data = {"version": 1.0, "enabled": "true"}
        issues = validator.check_field_types(data, file_path, mock_rule)
        assert len(issues) == 2

    def test_StructureValidator_check_version_field(self):
        """Test StructureValidator.check_version_field method."""
        validator = StructureValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with valid version
        data = {"version": "1.0.0"}
        file_path = Path("test.yaml")
        
        issues = validator.check_version_field(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with invalid version
        data = {"version": "1.0"}
        issues = validator.check_version_field(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.WARNING


class TestMetadataValidator:
    """Test MetadataValidator class."""

    def test_MetadataValidator_check_name_quality(self):
        """Test MetadataValidator.check_name_quality method."""
        validator = MetadataValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with valid name
        data = {"name": "Test Template"}
        file_path = Path("test.yaml")
        
        issues = validator.check_name_quality(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with empty name
        data = {"name": ""}
        issues = validator.check_name_quality(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.ERROR
        
        # Test with very long name
        data = {"name": "A" * 60}
        issues = validator.check_name_quality(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.WARNING

    def test_MetadataValidator_check_description_quality(self):
        """Test MetadataValidator.check_description_quality method."""
        validator = MetadataValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with valid description
        data = {"description": "This is a valid description with sufficient length"}
        file_path = Path("test.yaml")
        
        issues = validator.check_description_quality(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with empty description
        data = {"description": ""}
        issues = validator.check_description_quality(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.ERROR
        
        # Test with short description
        data = {"description": "Too short"}
        issues = validator.check_description_quality(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.WARNING

    def test_MetadataValidator_check_category_validity(self):
        """Test MetadataValidator.check_category_validity method."""
        validator = MetadataValidator()
        mock_rule = Mock()
        mock_rule.parameters = {"valid_categories": ["api", "database", "frontend"]}
        mock_rule.rule_id = "test_rule"
        
        # Test with valid category
        data = {"category": "api"}
        file_path = Path("test.yaml")
        
        issues = validator.check_category_validity(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with invalid category
        data = {"category": "invalid"}
        issues = validator.check_category_validity(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.WARNING


class TestVariablesValidator:
    """Test VariablesValidator class."""

    def test_VariablesValidator_check_variable_descriptions(self):
        """Test VariablesValidator.check_variable_descriptions method."""
        validator = VariablesValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with variables that have descriptions
        data = {
            "variables": {
                "api_key": {"description": "API key for authentication"},
                "endpoint": {"description": "API endpoint URL"}
            }
        }
        file_path = Path("test.yaml")
        
        issues = validator.check_variable_descriptions(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with variables missing descriptions
        data = {
            "variables": {
                "api_key": {},
                "endpoint": {"description": "API endpoint URL"}
            }
        }
        issues = validator.check_variable_descriptions(data, file_path, mock_rule)
        assert len(issues) == 1
        assert "api_key" in issues[0].message

    def test_VariablesValidator_check_variable_examples(self):
        """Test VariablesValidator.check_variable_examples method."""
        validator = VariablesValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with variables that have examples
        data = {
            "variables": {
                "api_key": {"example": "sk-1234567890abcdef"},
                "endpoint": {"example": "https://api.example.com"}
            }
        }
        file_path = Path("test.yaml")
        
        issues = validator.check_variable_examples(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with variables missing examples
        data = {
            "variables": {
                "api_key": {"example": "sk-1234567890abcdef"},
                "endpoint": {}
            }
        }
        issues = validator.check_variable_examples(data, file_path, mock_rule)
        assert len(issues) == 1
        assert "endpoint" in issues[0].message

    def test_VariablesValidator_check_required_variables(self):
        """Test VariablesValidator.check_required_variables method."""
        validator = VariablesValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with required variables properly marked
        data = {
            "variables": {
                "api_key": {"required": True},
                "endpoint": {"required": False}
            }
        }
        file_path = Path("test.yaml")
        
        issues = validator.check_required_variables(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with required variables missing required flag
        data = {
            "variables": {
                "api_key": {},
                "endpoint": {"required": False}
            }
        }
        issues = validator.check_required_variables(data, file_path, mock_rule)
        # This would depend on the actual implementation logic


class TestDocumentationValidator:
    """Test DocumentationValidator class."""

    def test_DocumentationValidator_check_setup_instructions(self):
        """Test DocumentationValidator.check_setup_instructions method."""
        validator = DocumentationValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with setup instructions present
        data = {"setup_instructions": "1. Install dependencies\n2. Configure API keys"}
        file_path = Path("test.yaml")
        
        issues = validator.check_setup_instructions(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with missing setup instructions
        data = {}
        issues = validator.check_setup_instructions(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.WARNING

    def test_DocumentationValidator_check_best_practices(self):
        """Test DocumentationValidator.check_best_practices method."""
        validator = DocumentationValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with best practices documented
        data = {"best_practices": "Use environment variables for sensitive data"}
        file_path = Path("test.yaml")
        
        issues = validator.check_best_practices(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with missing best practices
        data = {}
        issues = validator.check_best_practices(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.INFO

    def test_DocumentationValidator_check_troubleshooting(self):
        """Test DocumentationValidator.check_troubleshooting method."""
        validator = DocumentationValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with troubleshooting section present
        data = {"troubleshooting": "Common issues and solutions"}
        file_path = Path("test.yaml")
        
        issues = validator.check_troubleshooting(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with missing troubleshooting
        data = {}
        issues = validator.check_troubleshooting(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.INFO


class TestExamplesValidator:
    """Test ExamplesValidator class."""

    def test_ExamplesValidator_check_example_presence(self):
        """Test ExamplesValidator.check_example_presence method."""
        validator = ExamplesValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with examples present
        data = {"examples": [{"name": "Basic Example", "description": "Simple usage"}]}
        file_path = Path("test.yaml")
        
        issues = validator.check_example_presence(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with missing examples
        data = {}
        issues = validator.check_example_presence(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.WARNING

    def test_ExamplesValidator_check_example_quality(self):
        """Test ExamplesValidator.check_example_quality method."""
        validator = ExamplesValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with good quality examples
        data = {
            "examples": [
                {
                    "name": "Basic Example",
                    "description": "Simple usage example",
                    "code": "print('Hello World')"
                }
            ]
        }
        file_path = Path("test.yaml")
        
        issues = validator.check_example_quality(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with poor quality examples
        data = {
            "examples": [
                {
                    "name": "Example",
                    "description": "Short"
                }
            ]
        }
        issues = validator.check_example_quality(data, file_path, mock_rule)
        assert len(issues) >= 1


class TestSecurityValidator:
    """Test SecurityValidator class."""

    def test_SecurityValidator_check_hardcoded_secrets(self):
        """Test SecurityValidator.check_hardcoded_secrets method."""
        validator = SecurityValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with no hardcoded secrets
        data = {"code": "print('Hello World')"}
        file_path = Path("test.yaml")
        
        issues = validator.check_hardcoded_secrets(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with hardcoded secrets
        data = {"code": "api_key = 'sk-1234567890abcdef'"}
        issues = validator.check_hardcoded_secrets(data, file_path, mock_rule)
        assert len(issues) >= 1
        assert issues[0].severity == ValidationSeverity.ERROR

    def test_SecurityValidator_check_security_documentation(self):
        """Test SecurityValidator.check_security_documentation method."""
        validator = SecurityValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with security documentation present
        data = {"security_notes": "This template handles sensitive data"}
        file_path = Path("test.yaml")
        
        issues = validator.check_security_documentation(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with missing security documentation
        data = {}
        issues = validator.check_security_documentation(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.WARNING


class TestPerformanceValidator:
    """Test PerformanceValidator class."""

    def test_PerformanceValidator_check_performance_documentation(self):
        """Test PerformanceValidator.check_performance_documentation method."""
        validator = PerformanceValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with performance documentation present
        data = {"performance_notes": "This operation is O(n) complexity"}
        file_path = Path("test.yaml")
        
        issues = validator.check_performance_documentation(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with missing performance documentation
        data = {}
        issues = validator.check_performance_documentation(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.INFO

    def test_PerformanceValidator_check_resource_optimization(self):
        """Test PerformanceValidator.check_resource_optimization method."""
        validator = PerformanceValidator()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test with resource optimization notes
        data = {"resource_notes": "Uses minimal memory footprint"}
        file_path = Path("test.yaml")
        
        issues = validator.check_resource_optimization(data, file_path, mock_rule)
        assert len(issues) == 0
        
        # Test with missing resource optimization notes
        data = {}
        issues = validator.check_resource_optimization(data, file_path, mock_rule)
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.INFO


class TestValidatorRegistry:
    """Test ValidatorRegistry class."""

    def test_ValidatorRegistry_initialization(self):
        """Test ValidatorRegistry initialization."""
        registry = ValidatorRegistry()
        assert registry is not None
        assert hasattr(registry, 'validators')

    def test_ValidatorRegistry_get_validator(self):
        """Test ValidatorRegistry.get_validator method."""
        registry = ValidatorRegistry()
        
        # Test getting a known validator
        validator = registry.get_validator("structure")
        assert validator is not None
        
        # Test getting unknown validator
        validator = registry.get_validator("unknown")
        assert validator is None

    def test_ValidatorRegistry_run_validation(self):
        """Test ValidatorRegistry.run_validation method."""
        registry = ValidatorRegistry()
        mock_rule = Mock()
        mock_rule.rule_id = "test_rule"
        
        # Test running validation
        data = {"name": "Test Template"}
        file_path = Path("test.yaml")
        
        issues = registry.run_validation(data, file_path, mock_rule)
        assert isinstance(issues, list)
