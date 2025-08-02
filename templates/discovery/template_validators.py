#!/usr/bin/env python3
"""
Template Validators Module
=========================

Individual validation functions for template quality assurance.

Features:
- Modular validation functions by category
- Reusable validation components
- Extensible validation framework
- Detailed validation reporting
"""

import ast
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any

# Forward reference types to avoid circular imports
if TYPE_CHECKING:
    from .validation_rules import ValidationRule

# Type variable for validator functions
ValidatorFunc = Callable[[dict[str, Any], Path, "ValidationRule"], list["ValidationIssue"]]


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a template."""

    severity: ValidationSeverity
    category: str
    message: str
    location: str
    suggestion: str | None = None
    rule_id: str = ""


class StructureValidator:
    """Validates template structure and basic requirements."""

    @staticmethod
    def check_required_fields(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check that all required fields are present."""
        required_fields = (rule.parameters or {}).get("required_fields", [])

        issues: list[ValidationIssue] = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="structure",
                message=f"Missing required field: {field}",
                location=str(file_path),
                suggestion=f"Add the required '{field}' field to the template",
                rule_id=rule.rule_id,
            )
            for field in required_fields
            if field not in data
        ]
        return issues

    @staticmethod
    def check_field_types(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check that fields have the correct types."""
        issues: list[ValidationIssue] = []
        field_types = (rule.parameters or {}).get("field_types", {})

        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], ast.literal_eval(expected_type)):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="structure",
                        message=f"Field '{field}' has incorrect type (expected {expected_type})",
                        location=str(file_path),
                        suggestion=f"Ensure '{field}' is of type {expected_type}",
                        rule_id=rule.rule_id,
                    )
                )
        return issues

    @staticmethod
    def check_version_field(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check that the version field follows semantic versioning."""
        issues: list[ValidationIssue] = []
        if "version" in data:
            version = str(data["version"])
            if not re.match(r"^\d+\.\d+\.\d+$", version):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="versioning",
                        message="Version should follow semantic versioning (e.g., 1.0.0)",
                        location=str(file_path),
                        suggestion="Update version to follow semantic versioning (MAJOR.MINOR.PATCH)",
                        rule_id=rule.rule_id,
                    )
                )
        return issues


class MetadataValidator:
    """Validates template metadata quality."""

    @staticmethod
    def check_name_quality(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check name field quality."""
        issues: list[ValidationIssue] = []
        if "name" not in data:
            return issues

        name = str(data["name"]).strip()
        if not name:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="metadata",
                    message="Name cannot be empty",
                    location=str(file_path),
                    suggestion="Provide a non-empty name for the template",
                    rule_id=rule.rule_id,
                )
            )
        elif len(name) > 50:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="metadata",
                    message="Name is too long (max 50 characters recommended)",
                    location=str(file_path),
                    suggestion="Shorten the template name",
                    rule_id=rule.rule_id,
                )
            )
        return issues

    @staticmethod
    def check_description_quality(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check description field quality."""
        issues: list[ValidationIssue] = []
        if "description" not in data:
            return issues

        description = str(data["description"]).strip()
        if not description:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="metadata",
                    message="Description cannot be empty",
                    location=str(file_path),
                    suggestion="Provide a meaningful description for the template",
                    rule_id=rule.rule_id,
                )
            )
        elif len(description) < 20:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="metadata",
                    message="Description is too short (min 20 characters recommended)",
                    location=str(file_path),
                    suggestion="Provide a more detailed description",
                    rule_id=rule.rule_id,
                )
            )
        return issues

    @staticmethod
    def check_category_validity(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check category field validity."""
        issues: list[ValidationIssue] = []
        if "category" not in data:
            return issues

        category = str(data["category"]).lower()
        valid_categories = (rule.parameters or {}).get("valid_categories", [])

        if valid_categories and category not in valid_categories:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="metadata",
                    message=f"Category '{category}' is not in the list of recommended categories",
                    location=str(file_path),
                    suggestion=f"Use one of: {', '.join(valid_categories)}",
                    rule_id=rule.rule_id,
                )
            )
        return issues


class VariablesValidator:
    """Validates template variables configuration."""

    @staticmethod
    def check_variable_descriptions(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check that variables have descriptions."""
        issues: list[ValidationIssue] = []
        variables = data.get("variables", {})

        for var_name, var_config in variables.items():
            if not isinstance(var_config, dict):
                continue

            if not var_config.get("description"):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="variables",
                        message=f"Variable '{var_name}' is missing a description",
                        location=str(file_path),
                        suggestion=f"Add a description for the '{var_name}' variable",
                        rule_id=rule.rule_id,
                    )
                )
        return issues

    @staticmethod
    def check_variable_examples(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check that variables have examples."""
        issues: list[ValidationIssue] = []
        variables = data.get("variables", {})

        for var_name, var_config in variables.items():
            if not isinstance(var_config, dict):
                continue

            if "example" not in var_config and "examples" not in var_config:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="variables",
                        message=f"Variable '{var_name}' is missing an example",
                        location=str(file_path),
                        suggestion=f"Add an example for the '{var_name}' variable",
                        rule_id=rule.rule_id,
                    )
                )
        return issues

    @staticmethod
    def check_required_variables(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check that required variables are properly marked."""
        issues: list[ValidationIssue] = []
        variables = data.get("variables", {})

        for var_name, var_config in variables.items():
            if not isinstance(var_config, dict):
                continue

            is_required = var_config.get("required", False)
            has_default = "default" in var_config

            if is_required and has_default:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="variables",
                        message=f"Required variable '{var_name}' has a default value",
                        location=str(file_path),
                        suggestion="Remove either 'required: true' or the 'default' value",
                        rule_id=rule.rule_id,
                    )
                )
        return issues


class DocumentationValidator:
    """Validates documentation completeness."""

    @staticmethod
    def check_setup_instructions(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check for setup instructions."""
        issues: list[ValidationIssue] = []

        if not data.get("setup_instructions"):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="documentation",
                    message="Missing setup instructions",
                    location=str(file_path),
                    suggestion="Add setup instructions to help users get started",
                    rule_id=rule.rule_id,
                )
            )
        return issues

    @staticmethod
    def check_best_practices(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check for best practices documentation."""
        issues: list[ValidationIssue] = []

        if not data.get("best_practices"):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="documentation",
                    message="Missing best practices documentation",
                    location=str(file_path),
                    suggestion="Add best practices to help users follow conventions",
                    rule_id=rule.rule_id,
                )
            )
        return issues

    @staticmethod
    def check_troubleshooting(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check for troubleshooting documentation."""
        issues: list[ValidationIssue] = []

        if not data.get("troubleshooting"):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="documentation",
                    message="Missing troubleshooting documentation",
                    location=str(file_path),
                    suggestion="Add troubleshooting tips for common issues",
                    rule_id=rule.rule_id,
                )
            )
        return issues


class ExamplesValidator:
    """Validates examples quality and completeness."""

    @staticmethod
    def check_example_presence(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check for presence of examples."""
        issues: list[ValidationIssue] = []

        if not data.get("examples"):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="examples",
                    message="No examples provided",
                    location=str(file_path),
                    suggestion="Add usage examples to help users understand how to use the template",
                    rule_id=rule.rule_id,
                )
            )
        return issues

    @staticmethod
    def check_example_quality(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check quality of examples."""
        issues: list[ValidationIssue] = []
        examples = data.get("examples", [])

        if not isinstance(examples, list):
            return issues

        for i, example in enumerate(examples, 1):
            if not isinstance(example, dict):
                continue

            if not example.get("name") or not example.get("code"):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="examples",
                        message=f"Example {i} is missing name or code",
                        location=str(file_path),
                        suggestion="Ensure all examples have both a name and code snippet",
                        rule_id=rule.rule_id,
                    )
                )
        return issues


class SecurityValidator:
    """Validates security considerations."""

    @staticmethod
    def check_hardcoded_secrets(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check for hardcoded secrets or credentials."""
        issues: list[ValidationIssue] = []

        def check_for_secrets(text: str, context: str = "") -> None:
            secrets_patterns = [
                (r'(?i)password\s*[:=]\s*[\'"].*?[\'"]', "Hardcoded password"),
                (r'(?i)secret\s*[:=]\s*[\'"].*?[\'"]', "Hardcoded secret"),
                (r'(?i)api[_-]?key\s*[:=]\s*[\'"].*?[\'"]', "Hardcoded API key"),
                (r'(?i)token\s*[:=]\s*[\'"].*?[\'"]', "Hardcoded token"),
                (r'(?i)access[_-]?key\s*[:=]\s*[\'"].*?[\'"]', "Hardcoded access key"),
            ]

            for pattern, message in secrets_patterns:
                if re.search(pattern, text):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category="security",
                            message=f"{message} found in {context}",
                            location=str(file_path),
                            suggestion="Remove hardcoded secrets and use environment variables",
                            rule_id=rule.rule_id,
                        )
                    )

        # Check in template content if available
        if "template" in data and isinstance(data["template"], str):
            check_for_secrets(data["template"], "template content")

        # Check in examples
        examples = data.get("examples", [])
        if isinstance(examples, list):
            for i, example in enumerate(examples, 1):
                if (
                    isinstance(example, dict)
                    and "code" in example
                    and isinstance(example["code"], str)
                ):
                    check_for_secrets(example["code"], f"example {i}")

        return issues

    @staticmethod
    def check_security_documentation(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check for security documentation."""
        issues: list[ValidationIssue] = []

        if not data.get("security_considerations"):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="security",
                    message="Missing security considerations",
                    location=str(file_path),
                    suggestion="Add security considerations to help users understand potential risks",
                    rule_id=rule.rule_id,
                )
            )
        return issues


class PerformanceValidator:
    """Validates performance considerations."""

    @staticmethod
    def check_performance_documentation(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check for performance documentation."""
        issues: list[ValidationIssue] = []

        if not data.get("performance_considerations"):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="performance",
                    message="Missing performance considerations",
                    location=str(file_path),
                    suggestion="Add performance considerations to help users optimize their usage",
                    rule_id=rule.rule_id,
                )
            )
        return issues

    @staticmethod
    def check_resource_optimization(
        data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Check for resource optimization considerations."""
        issues: list[ValidationIssue] = []

        # This is a placeholder for more sophisticated resource optimization checks
        # In a real implementation, this would analyze the template for potential
        # performance bottlenecks or resource-intensive operations

        return issues


class ValidatorRegistry:
    """Registry of all validation functions."""

    def __init__(self) -> None:
        """Initialize the validator registry."""
        self._validators = {
            # Structure validators
            "check_required_fields": StructureValidator.check_required_fields,
            "check_field_types": StructureValidator.check_field_types,
            "check_version_field": StructureValidator.check_version_field,
            # Metadata validators
            "check_name_quality": MetadataValidator.check_name_quality,
            "check_description_quality": MetadataValidator.check_description_quality,
            "check_category_validity": MetadataValidator.check_category_validity,
            # Variables validators
            "check_variable_descriptions": VariablesValidator.check_variable_descriptions,
            "check_variable_examples": VariablesValidator.check_variable_examples,
            "check_required_variables": VariablesValidator.check_required_variables,
            # Documentation validators
            "check_setup_instructions": DocumentationValidator.check_setup_instructions,
            "check_best_practices": DocumentationValidator.check_best_practices,
            "check_troubleshooting": DocumentationValidator.check_troubleshooting,
            # Examples validators
            "check_example_presence": ExamplesValidator.check_example_presence,
            "check_example_quality": ExamplesValidator.check_example_quality,
            # Security validators
            "check_hardcoded_secrets": SecurityValidator.check_hardcoded_secrets,
            "check_security_documentation": SecurityValidator.check_security_documentation,
            # Performance validators
            "check_performance_documentation": PerformanceValidator.check_performance_documentation,
            "check_resource_optimization": PerformanceValidator.check_resource_optimization,
        }

    def get_validator(self, check_function: str) -> ValidatorFunc | None:
        """Get a validator function by name."""
        return self._validators.get(check_function)

    def run_validation(
        self, check_function: str, data: dict[str, Any], file_path: Path, rule: "ValidationRule"
    ) -> list[ValidationIssue]:
        """Run a specific validation check."""
        validator = self.get_validator(check_function)
        if validator:
            try:
                return validator(data, file_path, rule) or []
            except Exception as e:
                return [
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="validation",
                        message=f"Error running validation '{check_function}': {e!s}",
                        location=str(file_path),
                        suggestion="Check the validation implementation for issues",
                        rule_id=rule.rule_id,
                    )
                ]
        return []


# Global validator registry instance
_validator_registry = ValidatorRegistry()


def get_validator_registry() -> ValidatorRegistry:
    """Get the global validator registry instance."""
    return _validator_registry
