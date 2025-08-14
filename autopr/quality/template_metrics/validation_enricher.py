"""
Validation Issue Enricher Module
================================

Enriches ValidationIssue objects with additional attributes needed by report generators.

This module provides utilities to add missing attributes like location, suggestion, and rule_id
to ValidationIssue objects from autopr.quality.template_metrics.validation_types
so they can be properly rendered by report generators.
"""

from dataclasses import dataclass
from typing import Any

from .validation_types import ValidationIssue, ValidationSeverity


@dataclass
class EnrichedValidationIssue:
    """Enriched ValidationIssue with additional attributes for reporting."""

    # Original ValidationIssue attributes
    category: str
    severity: ValidationSeverity
    message: str
    line: int | None = None
    metadata: dict[str, Any] | None = None

    # Additional attributes for reporting
    location: str = ""
    suggestion: str | None = None
    rule_id: str = ""

    @classmethod
    def from_validation_issue(cls, issue: ValidationIssue, template_path: str = "") -> "EnrichedValidationIssue":
        """Create an enriched ValidationIssue from a base ValidationIssue."""
        # Extract location from line number or metadata
        location = template_path
        if issue.line is not None:
            location = f"{template_path}:{issue.line}"
        elif issue.metadata and "file_path" in issue.metadata:
            location = issue.metadata["file_path"]
            if "line" in issue.metadata:
                location = f"{location}:{issue.metadata['line']}"

        # Extract suggestion from metadata
        suggestion = None
        if issue.metadata:
            suggestion = issue.metadata.get("suggestion")
            if not suggestion and "fix" in issue.metadata:
                suggestion = issue.metadata["fix"]

        # Extract rule_id from metadata
        rule_id = ""
        if issue.metadata:
            rule_id = issue.metadata.get("rule_id", "")

        return cls(
            category=issue.category,
            severity=issue.severity,
            message=issue.message,
            line=issue.line,
            metadata=issue.metadata,
            location=location,
            suggestion=suggestion,
            rule_id=rule_id,
        )


def enrich_validation_issues(issues: list[ValidationIssue], template_path: str = "") -> list[EnrichedValidationIssue]:
    """Enrich a list of ValidationIssue objects with additional attributes."""
    return [EnrichedValidationIssue.from_validation_issue(issue, template_path) for issue in issues]


def enrich_quality_metrics_issues(metrics: Any) -> Any:
    """Enrich ValidationIssue objects in a QualityMetrics object."""
    if hasattr(metrics, "issues") and hasattr(metrics, "template_path"):
        enriched_issues = enrich_validation_issues(metrics.issues, metrics.template_path)
        # Create a new object with enriched issues
        enriched_metrics = type(metrics)(
            overall_score=metrics.overall_score,
            category_scores=metrics.category_scores,
            issues=enriched_issues,
            total_checks=metrics.total_checks,
            passed_checks=metrics.passed_checks,
            warnings_count=metrics.warnings_count,
            errors_count=metrics.errors_count,
            info_count=metrics.info_count,
            template_path=metrics.template_path,
            analysis_timestamp=metrics.analysis_timestamp,
        )
        return enriched_metrics
    return metrics
