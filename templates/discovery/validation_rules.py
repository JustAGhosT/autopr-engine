#!/usr/bin/env python3
"""
Validation Rules Module
======================

Centralized validation rule definitions and configurations for template quality assurance.

Features:
- Rule definitions and loading
- Validation criteria configuration
- Scoring weights and thresholds
- Rule management and organization
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ValidationRule:
    """Represents a single validation rule."""

    rule_id: str
    category: str
    severity: str
    description: str
    check_function: str
    weight: float = 1.0
    enabled: bool = True
    parameters: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ValidationRuleSet:
    """Collection of validation rules organized by category."""

    structure_rules: list[ValidationRule]
    metadata_rules: list[ValidationRule]
    variables_rules: list[ValidationRule]
    documentation_rules: list[ValidationRule]
    examples_rules: list[ValidationRule]
    security_rules: list[ValidationRule]
    performance_rules: list[ValidationRule]

    def get_all_rules(self) -> list[ValidationRule]:
        """Get all rules as a flat list."""
        return (
            self.structure_rules
            + self.metadata_rules
            + self.variables_rules
            + self.documentation_rules
            + self.examples_rules
            + self.security_rules
            + self.performance_rules
        )

    def get_rules_by_category(self, category: str) -> list[ValidationRule]:
        """Get rules for a specific category."""
        category_map = {
            "structure": self.structure_rules,
            "metadata": self.metadata_rules,
            "variables": self.variables_rules,
            "documentation": self.documentation_rules,
            "examples": self.examples_rules,
            "security": self.security_rules,
            "performance": self.performance_rules,
        }
        return category_map.get(category, [])


class ValidationRuleLoader:
    """Loads and manages validation rules from configuration files."""

    def __init__(self, rules_root: Path | None = None):
        """Initialize the rule loader."""
        if rules_root is None:
            self.rules_root = Path(__file__).parent / "validation_rules"
        else:
            self.rules_root = Path(rules_root)

        # Create rules directory if it doesn't exist
        self.rules_root.mkdir(exist_ok=True)

    @lru_cache(maxsize=1)
    def load_rules(self) -> ValidationRuleSet:
        """Load all validation rules from configuration files."""
        try:
            # Try to load from external configuration files first
            return self._load_from_files()
        except Exception:
            # Fallback to default built-in rules
            return self._load_default_rules()

    def _load_from_files(self) -> ValidationRuleSet:
        """Load rules from external configuration files."""
        rules_file = self.rules_root / "validation_rules.yml"

        if not rules_file.exists():
            return self._load_default_rules()

        with open(rules_file, encoding="utf-8") as f:
            rules_data = yaml.safe_load(f)

        return ValidationRuleSet(
            structure_rules=self._parse_rules(rules_data.get("structure", [])),
            metadata_rules=self._parse_rules(rules_data.get("metadata", [])),
            variables_rules=self._parse_rules(rules_data.get("variables", [])),
            documentation_rules=self._parse_rules(rules_data.get("documentation", [])),
            examples_rules=self._parse_rules(rules_data.get("examples", [])),
            security_rules=self._parse_rules(rules_data.get("security", [])),
            performance_rules=self._parse_rules(rules_data.get("performance", [])),
        )

    def _parse_rules(self, rules_data: list[dict[str, Any]]) -> list[ValidationRule]:
        """Parse rule data into ValidationRule objects."""
        rules = []
        for rule_data in rules_data:
            rule = ValidationRule(
                rule_id=rule_data.get("rule_id", ""),
                category=rule_data.get("category", ""),
                severity=rule_data.get("severity", "warning"),
                description=rule_data.get("description", ""),
                check_function=rule_data.get("check_function", ""),
                weight=rule_data.get("weight", 1.0),
                enabled=rule_data.get("enabled", True),
                parameters=rule_data.get("parameters", {}),
            )
            rules.append(rule)
        return rules

    def _load_default_rules(self) -> ValidationRuleSet:
        """Load default built-in validation rules."""
        return ValidationRuleSet(
            structure_rules=[
                ValidationRule(
                    rule_id="STR001",
                    category="structure",
                    severity="error",
                    description="Template must have required fields",
                    check_function="check_required_fields",
                    weight=2.0,
                    parameters={
                        "required_fields": [
                            "name",
                            "description",
                            "category",
                            "platforms",
                        ]
                    },
                ),
                ValidationRule(
                    rule_id="STR002",
                    category="structure",
                    severity="error",
                    description="Field types must be correct",
                    check_function="check_field_types",
                    weight=1.5,
                ),
                ValidationRule(
                    rule_id="STR003",
                    category="structure",
                    severity="warning",
                    description="Template should have version field",
                    check_function="check_version_field",
                    weight=0.5,
                ),
            ],
            metadata_rules=[
                ValidationRule(
                    rule_id="META001",
                    category="metadata",
                    severity="warning",
                    description="Name should be descriptive and clear",
                    check_function="check_name_quality",
                    weight=1.0,
                    parameters={"min_length": 5, "max_length": 100},
                ),
                ValidationRule(
                    rule_id="META002",
                    category="metadata",
                    severity="error",
                    description="Description must be present and meaningful",
                    check_function="check_description_quality",
                    weight=1.5,
                    parameters={"min_length": 20, "max_length": 500},
                ),
                ValidationRule(
                    rule_id="META003",
                    category="metadata",
                    severity="warning",
                    description="Category should be valid",
                    check_function="check_category_validity",
                    weight=1.0,
                    parameters={
                        "valid_categories": ["platform", "use_case", "integration"]
                    },
                ),
            ],
            variables_rules=[
                ValidationRule(
                    rule_id="VAR001",
                    category="variables",
                    severity="warning",
                    description="Variables should have descriptions",
                    check_function="check_variable_descriptions",
                    weight=1.0,
                ),
                ValidationRule(
                    rule_id="VAR002",
                    category="variables",
                    severity="warning",
                    description="Variables should have examples",
                    check_function="check_variable_examples",
                    weight=0.8,
                ),
                ValidationRule(
                    rule_id="VAR003",
                    category="variables",
                    severity="error",
                    description="Required variables must be marked",
                    check_function="check_required_variables",
                    weight=1.5,
                ),
            ],
            documentation_rules=[
                ValidationRule(
                    rule_id="DOC001",
                    category="documentation",
                    severity="warning",
                    description="Template should have setup instructions",
                    check_function="check_setup_instructions",
                    weight=1.2,
                ),
                ValidationRule(
                    rule_id="DOC002",
                    category="documentation",
                    severity="info",
                    description="Template should have best practices",
                    check_function="check_best_practices",
                    weight=0.8,
                ),
                ValidationRule(
                    rule_id="DOC003",
                    category="documentation",
                    severity="info",
                    description="Template should have troubleshooting guide",
                    check_function="check_troubleshooting",
                    weight=0.6,
                ),
            ],
            examples_rules=[
                ValidationRule(
                    rule_id="EX001",
                    category="examples",
                    severity="warning",
                    description="Template should have practical examples",
                    check_function="check_example_presence",
                    weight=1.0,
                ),
                ValidationRule(
                    rule_id="EX002",
                    category="examples",
                    severity="info",
                    description="Examples should be complete and realistic",
                    check_function="check_example_quality",
                    weight=0.8,
                ),
            ],
            security_rules=[
                ValidationRule(
                    rule_id="SEC001",
                    category="security",
                    severity="error",
                    description="No hardcoded secrets or credentials",
                    check_function="check_hardcoded_secrets",
                    weight=2.0,
                ),
                ValidationRule(
                    rule_id="SEC002",
                    category="security",
                    severity="warning",
                    description="Security best practices should be documented",
                    check_function="check_security_documentation",
                    weight=1.0,
                ),
            ],
            performance_rules=[
                ValidationRule(
                    rule_id="PERF001",
                    category="performance",
                    severity="info",
                    description="Performance considerations should be documented",
                    check_function="check_performance_documentation",
                    weight=0.8,
                ),
                ValidationRule(
                    rule_id="PERF002",
                    category="performance",
                    severity="warning",
                    description="Large files or resources should be optimized",
                    check_function="check_resource_optimization",
                    weight=1.0,
                ),
            ],
        )

    def save_rules_template(self) -> str:
        """Save a template rules configuration file for customization."""
        template_file = self.rules_root / "validation_rules_template.yml"

        default_rules = self._load_default_rules()
        rules_data = {
            "structure": [
                self._rule_to_dict(rule) for rule in default_rules.structure_rules
            ],
            "metadata": [
                self._rule_to_dict(rule) for rule in default_rules.metadata_rules
            ],
            "variables": [
                self._rule_to_dict(rule) for rule in default_rules.variables_rules
            ],
            "documentation": [
                self._rule_to_dict(rule) for rule in default_rules.documentation_rules
            ],
            "examples": [
                self._rule_to_dict(rule) for rule in default_rules.examples_rules
            ],
            "security": [
                self._rule_to_dict(rule) for rule in default_rules.security_rules
            ],
            "performance": [
                self._rule_to_dict(rule) for rule in default_rules.performance_rules
            ],
        }

        with open(template_file, "w", encoding="utf-8") as f:
            yaml.dump(rules_data, f, default_flow_style=False, indent=2)

        return str(template_file)

    def _rule_to_dict(self, rule: ValidationRule) -> dict[str, Any]:
        """Convert ValidationRule to dictionary for serialization."""
        return {
            "rule_id": rule.rule_id,
            "category": rule.category,
            "severity": rule.severity,
            "description": rule.description,
            "check_function": rule.check_function,
            "weight": rule.weight,
            "enabled": rule.enabled,
            "parameters": rule.parameters,
        }


# Global rule loader instance
_rule_loader: ValidationRuleLoader | None = None


def get_validation_rules() -> ValidationRuleSet:
    """Get the global validation rules instance."""
    global _rule_loader
    if _rule_loader is None:
        _rule_loader = ValidationRuleLoader()
    return _rule_loader.load_rules()


def reload_validation_rules() -> ValidationRuleSet:
    """Reload validation rules (clears cache)."""
    global _rule_loader
    if _rule_loader is not None:
        _rule_loader.load_rules.cache_clear()
    return get_validation_rules()
