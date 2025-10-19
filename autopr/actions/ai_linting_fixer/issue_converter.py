"""
Issue Converter Utility

This module provides utilities for converting between different LintingIssue representations
to avoid circular imports and schema mismatches.
"""

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from autopr.actions.ai_linting_fixer.detection import LintingIssue
    from autopr.actions.ai_linting_fixer.models import LintingIssue as ModelLintingIssue


def convert_detection_issue_to_model_issue(detection_issue: "LintingIssue") -> "ModelLintingIssue":
    """Convert a LintingIssue from detection module to models module."""
    # Import here to avoid circular imports
    from autopr.actions.ai_linting_fixer.models import LintingIssue as ModelLintingIssue

    # Build a candidate dict with superset keys
    candidate = {
        "file_path": detection_issue.file_path,
        "line_number": getattr(detection_issue, "line_number", None),
        "error_code": detection_issue.error_code,
        "message": detection_issue.message,
        "line_content": getattr(detection_issue, "line_content", ""),
        # Prefer column_number; also support models that use "column"
        "column_number": getattr(detection_issue, "column_number", None),
        "column": getattr(detection_issue, "column_number", None),
    }
    # Filter by the target model's constructor fields
    allowed = set(getattr(ModelLintingIssue, "__annotations__", {}).keys() or [])
    payload = {k: v for k, v in candidate.items() if k in allowed and v is not None}
    return ModelLintingIssue(**payload)


def convert_detection_issues_to_model_issues(
    detection_issues: list["LintingIssue"]
) -> list["ModelLintingIssue"]:
    """Convert a list of LintingIssues from detection module to models module."""
    return [convert_detection_issue_to_model_issue(issue) for issue in detection_issues]
