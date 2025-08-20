"""
Template System Core Models

This module defines the core data models for the template system.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class TemplateType(StrEnum):
    """Enumeration of template types."""

    FILE = "file"
    DIRECTORY = "directory"
    COMPONENT = "component"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"


class TemplateVariableType(StrEnum):
    """Supported template variable types."""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    PATH = "path"
    CHOICE = "choice"


@dataclass
class TemplateVariable:
    """Represents a variable that can be used within a template."""

    name: str
    type: TemplateVariableType
    description: str = ""
    default: Any | None = None
    required: bool = False
    choices: list[Any] | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None

    def validate(self, value: Any) -> bool:
        """Validate a value against the variable's constraints."""
        if value is None:
            return not self.required

        # Type checking
        try:
            if self.type == TemplateVariableType.INTEGER:
                int(value)
            elif self.type == TemplateVariableType.BOOLEAN:
                if not isinstance(value, bool):
                    value = str(value).lower() in {"true", "1", "t", "y", "yes"}
            elif (self.type == TemplateVariableType.LIST and not isinstance(value, list)) or (
                self.type == TemplateVariableType.DICT and not isinstance(value, dict)
            ):
                return False
        except (ValueError, TypeError):
            return False

        # Length validation
        str_value = str(value)
        if self.min_length is not None and len(str_value) < self.min_length:
            return False
        if self.max_length is not None and len(str_value) > self.max_length:
            return False

        # Pattern matching
        if self.pattern is not None:
            import re

            if not re.match(self.pattern, str(value)):
                return False

        # Choices validation
        return not (self.choices is not None and value not in self.choices)


@dataclass
class TemplateVariant:
    """Represents a variant of a template with specific modifications."""

    name: str
    description: str
    modifications: list[dict[str, Any]] = field(default_factory=list)
    variables: dict[str, TemplateVariable] = field(default_factory=dict)


@dataclass
class TemplateMetadata:
    """Comprehensive metadata for a template."""

    id: str
    name: str
    description: str
    type: TemplateType
    source_path: Path

    # Template configuration
    category: str = ""
    tags: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    dependencies: dict[str, str] = field(default_factory=dict)

    # Variables and variants
    variables: dict[str, TemplateVariable] = field(default_factory=dict)
    variants: dict[str, TemplateVariant] = field(default_factory=dict)

    # Versioning
    version: str = "1.0.0"
    min_auto_pr_version: str | None = None

    # Documentation
    examples: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def get_variable(self, name: str) -> TemplateVariable | None:
        """Get a variable by name, including variant variables."""
        return self.variables.get(name)

    def validate_variables(self, variables: dict[str, Any]) -> dict[str, str]:
        """Validate template variables and return any errors."""
        errors = {}

        # Check required variables
        for name, var in self.variables.items():
            if var.required and name not in variables:
                errors[name] = "This field is required"

            if name in variables and not var.validate(variables[name]):
                errors[name] = f"Invalid value for {name}"

        return errors
