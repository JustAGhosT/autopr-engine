#!/usr/bin/env python3
"""
Comprehensive tests for template validators module.
"""

import json
import os
import tempfile

import pytest


# Import the modules we're testing
try:
    from templates.discovery.template_validators import (
        ContentValidator,
        FormatValidator,
        SchemaValidator,
        TemplateValidator,
        ValidationError,
        ValidationResult,
    )
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestValidationResult:
    """Test ValidationResult class."""

    def test_validation_result_initialization(self):
        """Test ValidationResult initialization."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Warning 1", "Warning 2"],
            metadata={"test": "value"}
        )

        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == ["Warning 1", "Warning 2"]
        assert result.metadata == {"test": "value"}

    def test_validation_result_with_errors(self):
        """Test ValidationResult with errors."""
        errors = [
            ValidationError("Field 'name' is required", "name"),
            ValidationError("Invalid format", "email")
        ]
        result = ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=[]
        )

        assert result.is_valid is False
        assert len(result.errors) == 2
        assert result.errors[0].message == "Field 'name' is required"
        assert result.errors[0].field == "name"

    def test_validation_result_to_dict(self):
        """Test ValidationResult to_dict method."""
        errors = [ValidationError("Test error", "test_field")]
        result = ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=["Test warning"],
            metadata={"count": 1}
        )

        result_dict = result.to_dict()
        expected = {
            "is_valid": False,
            "errors": [{"message": "Test error", "field": "test_field"}],
            "warnings": ["Test warning"],
            "metadata": {"count": 1}
        }
        assert result_dict == expected

    def test_validation_result_from_dict(self):
        """Test ValidationResult from_dict method."""
        data = {
            "is_valid": True,
            "errors": [{"message": "Test error", "field": "test_field"}],
            "warnings": ["Test warning"],
            "metadata": {"count": 1}
        }

        result = ValidationResult.from_dict(data)
        assert result.is_valid is True
        assert len(result.errors) == 1
        assert result.errors[0].message == "Test error"
        assert result.warnings == ["Test warning"]
        assert result.metadata == {"count": 1}


class TestValidationError:
    """Test ValidationError class."""

    def test_validation_error_initialization(self):
        """Test ValidationError initialization."""
        error = ValidationError(
            message="Field is required",
            field="name",
            code="REQUIRED_FIELD",
            severity="error"
        )

        assert error.message == "Field is required"
        assert error.field == "name"
        assert error.code == "REQUIRED_FIELD"
        assert error.severity == "error"

    def test_validation_error_defaults(self):
        """Test ValidationError with default values."""
        error = ValidationError("Test message", "test_field")

        assert error.message == "Test message"
        assert error.field == "test_field"
        assert error.code == "VALIDATION_ERROR"
        assert error.severity == "error"

    def test_validation_error_to_dict(self):
        """Test ValidationError to_dict method."""
        error = ValidationError(
            message="Invalid format",
            field="email",
            code="INVALID_FORMAT",
            severity="warning"
        )

        error_dict = error.to_dict()
        expected = {
            "message": "Invalid format",
            "field": "email",
            "code": "INVALID_FORMAT",
            "severity": "warning"
        }
        assert error_dict == expected

    def test_validation_error_from_dict(self):
        """Test ValidationError from_dict method."""
        data = {
            "message": "Test error",
            "field": "test_field",
            "code": "TEST_ERROR",
            "severity": "error"
        }

        error = ValidationError.from_dict(data)
        assert error.message == "Test error"
        assert error.field == "test_field"
        assert error.code == "TEST_ERROR"
        assert error.severity == "error"


class TestSchemaValidator:
    """Test SchemaValidator class."""

    @pytest.fixture
    def schema_validator(self):
        """Create a SchemaValidator instance for testing."""
        return SchemaValidator()

    def test_schema_validator_initialization(self, schema_validator):
        """Test SchemaValidator initialization."""
        assert schema_validator.schemas == {}
        assert schema_validator.default_schema is None

    def test_register_schema(self, schema_validator):
        """Test registering a schema."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }

        schema_validator.register_schema("user", schema)
        assert "user" in schema_validator.schemas
        assert schema_validator.schemas["user"] == schema

    def test_set_default_schema(self, schema_validator):
        """Test setting default schema."""
        schema = {"type": "object"}
        schema_validator.register_schema("default", schema)
        schema_validator.set_default_schema("default")

        assert schema_validator.default_schema == "default"

    def test_validate_with_schema(self, schema_validator):
        """Test validation with schema."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        schema_validator.register_schema("user", schema)

        # Valid data
        valid_data = {"name": "John", "age": 30}
        result = schema_validator.validate(valid_data, "user")
        assert result.is_valid is True
        assert len(result.errors) == 0

        # Invalid data
        invalid_data = {"age": "not_a_number"}
        result = schema_validator.validate(invalid_data, "user")
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_with_default_schema(self, schema_validator):
        """Test validation with default schema."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        schema_validator.register_schema("default", schema)
        schema_validator.set_default_schema("default")

        data = {"name": "John"}
        result = schema_validator.validate(data)
        assert result.is_valid is True

    def test_validate_invalid_schema(self, schema_validator):
        """Test validation with invalid schema."""
        data = {"name": "John"}
        result = schema_validator.validate(data, "nonexistent")

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("Schema not found" in error.message for error in result.errors)


class TestContentValidator:
    """Test ContentValidator class."""

    @pytest.fixture
    def content_validator(self):
        """Create a ContentValidator instance for testing."""
        return ContentValidator()

    def test_content_validator_initialization(self, content_validator):
        """Test ContentValidator initialization."""
        assert content_validator.rules == []
        assert content_validator.custom_validators == {}

    def test_add_rule(self, content_validator):
        """Test adding a validation rule."""
        def name_rule(data):
            if "name" not in data:
                return ValidationError("Name is required", "name")
            return None

        content_validator.add_rule(name_rule)
        assert len(content_validator.rules) == 1

    def test_add_custom_validator(self, content_validator):
        """Test adding a custom validator."""
        def email_validator(value):
            if "@" not in value:
                return ValidationError("Invalid email format", "email")
            return None

        content_validator.add_custom_validator("email", email_validator)
        assert "email" in content_validator.custom_validators

    def test_validate_content(self, content_validator):
        """Test content validation."""
        # Add a rule
        def name_rule(data):
            if "name" not in data:
                return ValidationError("Name is required", "name")
            return None

        content_validator.add_rule(name_rule)

        # Valid data
        valid_data = {"name": "John", "email": "john@example.com"}
        result = content_validator.validate(valid_data)
        assert result.is_valid is True
        assert len(result.errors) == 0

        # Invalid data
        invalid_data = {"email": "john@example.com"}
        result = content_validator.validate(invalid_data)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].message == "Name is required"

    def test_validate_with_custom_validator(self, content_validator):
        """Test validation with custom validator."""
        def email_validator(value):
            if "@" not in value:
                return ValidationError("Invalid email format", "email")
            return None

        content_validator.add_custom_validator("email", email_validator)

        # Valid email
        result = content_validator.validate_field("john@example.com", "email")
        assert result is None

        # Invalid email
        result = content_validator.validate_field("invalid-email", "email")
        assert result is not None
        assert result.message == "Invalid email format"

    def test_validate_multiple_rules(self, content_validator):
        """Test validation with multiple rules."""
        def name_rule(data):
            if "name" not in data:
                return ValidationError("Name is required", "name")
            return None

        def age_rule(data):
            if "age" in data and data["age"] < 0:
                return ValidationError("Age must be positive", "age")
            return None

        content_validator.add_rule(name_rule)
        content_validator.add_rule(age_rule)

        # Data with multiple issues
        invalid_data = {"age": -5}
        result = content_validator.validate(invalid_data)
        assert result.is_valid is False
        assert len(result.errors) == 2


class TestFormatValidator:
    """Test FormatValidator class."""

    @pytest.fixture
    def format_validator(self):
        """Create a FormatValidator instance for testing."""
        return FormatValidator()

    def test_format_validator_initialization(self, format_validator):
        """Test FormatValidator initialization."""
        assert format_validator.formats == {}
        assert format_validator.default_formats is not None

    def test_register_format(self, format_validator):
        """Test registering a format."""
        def phone_format(value):
            import re
            pattern = r'^\+?1?\d{9,15}$'
            if not re.match(pattern, value):
                return ValidationError("Invalid phone format", "phone")
            return None

        format_validator.register_format("phone", phone_format)
        assert "phone" in format_validator.formats

    def test_validate_format(self, format_validator):
        """Test format validation."""
        def email_format(value):
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, value):
                return ValidationError("Invalid email format", "email")
            return None

        format_validator.register_format("email", email_format)

        # Valid email
        result = format_validator.validate_format("john@example.com", "email")
        assert result is None

        # Invalid email
        result = format_validator.validate_format("invalid-email", "email")
        assert result is not None
        assert result.message == "Invalid email format"

    def test_validate_unknown_format(self, format_validator):
        """Test validation with unknown format."""
        result = format_validator.validate_format("test", "unknown_format")
        assert result is not None
        assert "Unknown format" in result.message

    def test_validate_multiple_formats(self, format_validator):
        """Test validation with multiple formats."""
        def email_format(value):
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, value):
                return ValidationError("Invalid email format", "email")
            return None

        def phone_format(value):
            import re
            pattern = r'^\+?1?\d{9,15}$'
            if not re.match(pattern, value):
                return ValidationError("Invalid phone format", "phone")
            return None

        format_validator.register_format("email", email_format)
        format_validator.register_format("phone", phone_format)

        # Valid formats
        assert format_validator.validate_format("john@example.com", "email") is None
        assert format_validator.validate_format("+1234567890", "phone") is None

        # Invalid formats
        assert format_validator.validate_format("invalid-email", "email") is not None
        assert format_validator.validate_format("invalid-phone", "phone") is not None


class TestTemplateValidator:
    """Test TemplateValidator class."""

    @pytest.fixture
    def template_validator(self):
        """Create a TemplateValidator instance for testing."""
        return TemplateValidator()

    def test_template_validator_initialization(self, template_validator):
        """Test TemplateValidator initialization."""
        assert template_validator.schema_validator is not None
        assert template_validator.content_validator is not None
        assert template_validator.format_validator is not None

    def test_validate_template(self, template_validator):
        """Test template validation."""
        # Set up schema
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["name"]
        }
        template_validator.schema_validator.register_schema("user", schema)

        # Add content rule
        def email_rule(data):
            if "email" in data and "@" not in data["email"]:
                return ValidationError("Invalid email format", "email")
            return None
        template_validator.content_validator.add_rule(email_rule)

        # Valid template
        valid_template = {
            "name": "John Doe",
            "email": "john@example.com"
        }
        result = template_validator.validate_template(valid_template, "user")
        assert result.is_valid is True
        assert len(result.errors) == 0

        # Invalid template
        invalid_template = {
            "email": "invalid-email"
        }
        result = template_validator.validate_template(invalid_template, "user")
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_template_file(self, template_validator):
        """Test template file validation."""
        # Create a temporary template file
        template_data = {
            "name": "Test Template",
            "version": "1.0",
            "fields": ["name", "email"]
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(template_data, f)
            temp_file = f.name

        try:
            # Set up schema for template file
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "version": {"type": "string"},
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["name", "version", "fields"]
            }
            template_validator.schema_validator.register_schema("template_file", schema)

            result = template_validator.validate_template_file(temp_file, "template_file")
            assert result.is_valid is True

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_validate_template_directory(self, template_validator):
        """Test template directory validation."""
        # Create a temporary directory with template files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create template files
            template1 = {"name": "Template 1", "version": "1.0"}
            template2 = {"name": "Template 2", "version": "1.0"}

            with open(os.path.join(temp_dir, "template1.json"), 'w') as f:
                json.dump(template1, f)
            with open(os.path.join(temp_dir, "template2.json"), 'w') as f:
                json.dump(template2, f)

            # Set up schema
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "version": {"type": "string"}
                },
                "required": ["name", "version"]
            }
            template_validator.schema_validator.register_schema("template", schema)

            results = template_validator.validate_template_directory(temp_dir, "template")
            assert len(results) == 2
            assert all(result.is_valid for result in results.values())

    def test_get_validation_summary(self, template_validator):
        """Test getting validation summary."""
        # Set up some validation results
        results = {
            "template1.json": ValidationResult(is_valid=True, errors=[], warnings=[]),
            "template2.json": ValidationResult(
                is_valid=False,
                errors=[ValidationError("Invalid format", "name")],
                warnings=["Deprecated field"]
            )
        }

        summary = template_validator.get_validation_summary(results)
        assert summary["total_templates"] == 2
        assert summary["valid_templates"] == 1
        assert summary["invalid_templates"] == 1
        assert summary["total_errors"] == 1
        assert summary["total_warnings"] == 1

    def test_validate_with_custom_rules(self, template_validator):
        """Test validation with custom rules."""
        # Add custom content rule
        def custom_rule(data):
            if "name" in data and len(data["name"]) < 2:
                return ValidationError("Name must be at least 2 characters", "name")
            return None

        template_validator.content_validator.add_rule(custom_rule)

        # Add custom format validator
        def custom_format(value):
            if not value.startswith("test_"):
                return ValidationError("Value must start with 'test_'", "prefix")
            return None

        template_validator.format_validator.register_format("test_prefix", custom_format)

        # Test validation
        data = {"name": "a", "prefix": "invalid"}
        result = template_validator.validate_template(data)
        assert result.is_valid is False
        assert len(result.errors) >= 1

    def test_validate_complex_template(self, template_validator):
        """Test validation of complex template structure."""
        # Complex schema
        schema = {
            "type": "object",
            "properties": {
                "metadata": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "author": {"type": "string"}
                    },
                    "required": ["name", "version"]
                },
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "required": {"type": "boolean"}
                        },
                        "required": ["name", "type"]
                    }
                }
            },
            "required": ["metadata", "fields"]
        }

        template_validator.schema_validator.register_schema("complex_template", schema)

        # Valid complex template
        valid_template = {
            "metadata": {
                "name": "User Template",
                "version": "1.0",
                "author": "John Doe"
            },
            "fields": [
                {"name": "username", "type": "string", "required": True},
                {"name": "email", "type": "email", "required": True},
                {"name": "age", "type": "integer", "required": False}
            ]
        }

        result = template_validator.validate_template(valid_template, "complex_template")
        assert result.is_valid is True
