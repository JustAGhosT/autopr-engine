#!/usr/bin/env python3
"""
Quality Scorer Module
====================

Quality scoring algorithms and calculations for template validation results.

This module contains the QualityScorer class which implements the core
scoring algorithms used to calculate quality metrics from validation results.
"""

from typing import Any

from ...templates.discovery.template_validators import ValidationIssue, ValidationSeverity
from .quality_models import DEFAULT_CATEGORY_WEIGHTS, DEFAULT_SEVERITY_WEIGHTS, QualityMetrics


class QualityScorer:
    """Calculates quality scores based on validation results."""

    def __init__(self) -> None:
        """Initialize the quality scorer."""
        # Severity weights for scoring
        self.severity_weights = DEFAULT_SEVERITY_WEIGHTS.copy()

        # Category importance weights
        self.category_weights = DEFAULT_CATEGORY_WEIGHTS.copy()

    def calculate_metrics(
        self, issues: list[ValidationIssue], total_checks: int, template_path: str = ""
    ) -> QualityMetrics:
        """Calculate comprehensive quality metrics."""

        # Initialize metrics
        metrics = QualityMetrics(
            issues=issues, total_checks=total_checks, template_path=template_path
        )

        # Calculate category scores
        metrics.category_scores = self._calculate_category_scores(issues, total_checks)

        # Calculate overall score
        metrics.overall_score = self._calculate_overall_score(metrics.category_scores, issues)

        return metrics

    def _calculate_category_scores(
        self, issues: list[ValidationIssue], total_checks: int
    ) -> dict[str, float]:
        """Calculate scores for each category."""
        category_scores = {}

        # Group issues by category
        category_issues: dict[str, list[ValidationIssue]] = {}
        for issue in issues:
            if issue.category not in category_issues:
                category_issues[issue.category] = []
            category_issues[issue.category].append(issue)

        # Calculate score for each category
        for category in self.category_weights:
            category_issue_list = category_issues.get(category, [])

            # Calculate penalty based on issues
            penalty = 0.0
            for issue in category_issue_list:
                penalty += self.severity_weights.get(issue.severity, 1.0)

            # Calculate base score (assuming equal distribution of checks)
            category_checks = max(1, total_checks // len(self.category_weights))
            base_score = 100.0

            # Apply penalty (normalize by number of checks)
            normalized_penalty = (penalty / category_checks) * 10  # Scale penalty
            final_score = max(0.0, base_score - normalized_penalty)

            category_scores[category] = final_score

        return category_scores

    def _calculate_overall_score(
        self, category_scores: dict[str, float], issues: list[ValidationIssue]
    ) -> float:
        """Calculate weighted overall score."""
        if not category_scores:
            return 0.0

        # Calculate weighted average of category scores
        total_weight = 0.0
        weighted_sum = 0.0

        for category, score in category_scores.items():
            weight = self.category_weights.get(category, 1.0)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        base_score = weighted_sum / total_weight

        # Apply additional penalties for critical issues
        critical_penalty = 0.0
        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                critical_penalty += 5.0  # Heavy penalty for errors

        # Ensure score doesn't go below 0
        final_score = max(0.0, base_score - critical_penalty)

        return min(100.0, final_score)  # Cap at 100

    def compare_metrics(self, metrics1: QualityMetrics, metrics2: QualityMetrics) -> dict[str, Any]:
        """Compare two quality metrics."""
        comparison = {
            "template1": {
                "path": metrics1.template_path,
                "overall_score": metrics1.overall_score,
                "grade": metrics1.quality_grade,
                "issues_count": len(metrics1.issues),
                "success_rate": metrics1.success_rate,
            },
            "template2": {
                "path": metrics2.template_path,
                "overall_score": metrics2.overall_score,
                "grade": metrics2.quality_grade,
                "issues_count": len(metrics2.issues),
                "success_rate": metrics2.success_rate,
            },
            "differences": {
                "score_diff": metrics1.overall_score - metrics2.overall_score,
                "issues_diff": len(metrics1.issues) - len(metrics2.issues),
                "success_rate_diff": metrics1.success_rate - metrics2.success_rate,
            },
            "better_template": None,
        }

        # Determine which template is better
        if metrics1.overall_score > metrics2.overall_score:
            comparison["better_template"] = "template1"
        elif metrics2.overall_score > metrics1.overall_score:
            comparison["better_template"] = "template2"
        else:
            comparison["better_template"] = "tie"

        # Category comparison
        comparison["category_comparison"] = {}
        all_categories = set(metrics1.category_scores.keys()) | set(metrics2.category_scores.keys())

        for category in all_categories:
            score1 = metrics1.category_scores.get(category, 0.0)
            score2 = metrics2.category_scores.get(category, 0.0)
            comparison["category_comparison"][category] = {
                "template1_score": score1,
                "template2_score": score2,
                "difference": score1 - score2,
            }

        return comparison

    def update_weights(
        self,
        severity_weights: dict[ValidationSeverity, float] | None = None,
        category_weights: dict[str, float] | None = None,
    ) -> None:
        """Update scoring weights."""
        if severity_weights:
            self.severity_weights.update(severity_weights)

        if category_weights:
            self.category_weights.update(category_weights)

    def get_scoring_config(self) -> dict[str, Any]:
        """Get current scoring configuration."""
        return {
            "severity_weights": dict(self.severity_weights),
            "category_weights": dict(self.category_weights),
        }
