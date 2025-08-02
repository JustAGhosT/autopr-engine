#!/usr/bin/env python3
"""
Quality Models Module
====================

Data models and structures for template quality metrics.

This module contains the core data structures used throughout the quality
assessment system, including the main QualityMetrics dataclass and related
utility functions.
"""

from dataclasses import dataclass, field
from datetime import datetime

from ...templates.discovery.template_validators import ValidationIssue, ValidationSeverity


@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for a template."""

    overall_score: float = 0.0
    category_scores: dict[str, float] = field(default_factory=dict)
    issues: list[ValidationIssue] = field(default_factory=list)
    total_checks: int = 0
    passed_checks: int = 0
    warnings_count: int = 0
    errors_count: int = 0
    info_count: int = 0
    template_path: str = ""
    analysis_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Calculate derived metrics after initialization."""
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now()

        # Count issues by severity
        self.errors_count = sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.ERROR
        )
        self.warnings_count = sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING
        )
        self.info_count = sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.INFO
        )

        # Calculate passed checks
        self.passed_checks = self.total_checks - len(self.issues)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_checks == 0:
            return 0.0
        return (self.passed_checks / self.total_checks) * 100

    @property
    def quality_grade(self) -> str:
        """Get quality grade based on overall score."""
        if self.overall_score >= 90:
            return "A"
        if self.overall_score >= 80:
            return "B"
        if self.overall_score >= 70:
            return "C"
        if self.overall_score >= 60:
            return "D"
        return "F"

    @property
    def has_critical_issues(self) -> bool:
        """Check if template has critical issues (errors)."""
        return self.errors_count > 0

    def get_issues_by_category(self, category: str) -> list[ValidationIssue]:
        """Get issues for a specific category."""
        return [issue for issue in self.issues if issue.category == category]

    def get_issues_by_severity(self, severity: ValidationSeverity) -> list[ValidationIssue]:
        """Get issues by severity level."""
        return [issue for issue in self.issues if issue.severity == severity]


# Quality grade constants
QUALITY_GRADES = {
    "A": {"min_score": 90, "description": "Excellent"},
    "B": {"min_score": 80, "description": "Good"},
    "C": {"min_score": 70, "description": "Satisfactory"},
    "D": {"min_score": 60, "description": "Needs Improvement"},
    "F": {"min_score": 0, "description": "Poor"},
}

# Default severity weights
DEFAULT_SEVERITY_WEIGHTS = {
    ValidationSeverity.ERROR: 10.0,
    ValidationSeverity.WARNING: 5.0,
    ValidationSeverity.INFO: 1.0,
}

# Default category weights
DEFAULT_CATEGORY_WEIGHTS = {
    "structure": 2.0,
    "metadata": 1.5,
    "variables": 1.2,
    "documentation": 1.0,
    "examples": 0.8,
    "security": 2.5,
    "performance": 0.8,
}
