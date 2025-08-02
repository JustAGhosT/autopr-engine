#!/usr/bin/env python3
"""
Quality Analyzer Module
======================

Quality trend analysis and insights for template quality assurance.

This module contains the QualityAnalyzer class which provides advanced
analysis capabilities including trend analysis, batch processing, and
improvement recommendations.
"""

import operator
import statistics
from typing import Any

from .quality_models import QualityMetrics
from .quality_scorer import QualityScorer

# from templates.discovery.template_validators import ValidationSeverity


class QualityAnalyzer:
    """Analyzes quality trends and provides insights."""

    def __init__(self) -> None:
        """Initialize the quality analyzer."""
        self.scorer = QualityScorer()

    def analyze_template_quality(self, metrics: QualityMetrics) -> dict[str, Any]:
        """Analyze template quality and provide insights."""
        return {
            "summary": self._get_quality_summary(metrics),
            "strengths": self._identify_strengths(metrics),
            "weaknesses": self._identify_weaknesses(metrics),
            "recommendations": self._generate_recommendations(metrics),
            "priority_fixes": self._get_priority_fixes(metrics),
            "trends": self._analyze_quality_trends(metrics),
        }

    def _get_quality_summary(self, metrics: QualityMetrics) -> dict[str, Any]:
        """Get a summary of quality metrics."""
        return {
            "overall_score": metrics.overall_score,
            "grade": metrics.quality_grade,
            "success_rate": metrics.success_rate,
            "total_issues": len(metrics.issues),
            "critical_issues": metrics.errors_count,
            "warnings": metrics.warnings_count,
            "template_path": metrics.template_path,
        }

    def _identify_strengths(self, metrics: QualityMetrics) -> list[str]:
        """Identify template strengths."""
        strengths = []

        # Check for high category scores
        for category, score in metrics.category_scores.items():
            if score >= 85:
                strengths.append(f"Excellent {category} quality (score: {score:.1f})")
            elif score >= 75:
                strengths.append(f"Good {category} implementation (score: {score:.1f})")

        # Check for low issue counts
        if metrics.errors_count == 0:
            strengths.append("No critical errors found")

        if metrics.warnings_count <= 2:
            strengths.append("Minimal warnings")

        if metrics.success_rate >= 90:
            strengths.append(f"High success rate ({metrics.success_rate:.1f}%)")

        return strengths

    def _identify_weaknesses(self, metrics: QualityMetrics) -> list[str]:
        """Identify template weaknesses."""
        weaknesses = []

        # Check for low category scores
        for category, score in metrics.category_scores.items():
            if score < 50:
                weaknesses.append(f"Poor {category} quality (score: {score:.1f})")
            elif score < 70:
                weaknesses.append(f"Below average {category} implementation (score: {score:.1f})")

        # Check for high issue counts
        if metrics.errors_count > 0:
            weaknesses.append(f"{metrics.errors_count} critical error(s) found")

        if metrics.warnings_count > 5:
            weaknesses.append(f"High number of warnings ({metrics.warnings_count})")

        if metrics.success_rate < 70:
            weaknesses.append(f"Low success rate ({metrics.success_rate:.1f}%)")

        return weaknesses

    def _generate_recommendations(self, metrics: QualityMetrics) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []

        # Category-specific recommendations
        for category, score in metrics.category_scores.items():
            if score < 70:
                if category == "structure":
                    recommendations.append("Review template structure and required fields")
                elif category == "metadata":
                    recommendations.append("Improve template metadata and descriptions")
                elif category == "variables":
                    recommendations.append("Add better variable descriptions and examples")
                elif category == "documentation":
                    recommendations.append("Enhance setup instructions and documentation")
                elif category == "examples":
                    recommendations.append("Add more comprehensive examples")
                elif category == "security":
                    recommendations.append(
                        "Address security concerns and add security documentation"
                    )
                elif category == "performance":
                    recommendations.append("Optimize performance and add performance guidelines")

        # Issue-based recommendations
        error_categories = {
            issue.category for issue in metrics.issues if issue.severity == ValidationSeverity.ERROR
        }
        recommendations.extend(
            f"Fix critical issues in {category} category" for category in error_categories
        )

        # General recommendations
        if metrics.overall_score < 60:
            recommendations.append("Consider comprehensive template review and refactoring")
        elif metrics.overall_score < 80:
            recommendations.append("Focus on addressing highest-priority issues first")

        return recommendations

    def _get_priority_fixes(self, metrics: QualityMetrics) -> list[dict[str, Any]]:
        """Get priority issues that should be fixed first."""

        # Sort issues by severity and category importance
        sorted_issues = sorted(
            metrics.issues,
            key=lambda issue: (
                -self.scorer.severity_weights.get(issue.severity, 1.0),
                -self.scorer.category_weights.get(issue.category, 1.0),
            ),
        )

        # Take top 5 priority issues
        return [
            {
                "category": issue.category,
                "severity": issue.severity.value,
                "message": issue.message,
                "line": getattr(issue, "line", None),
                "priority_score": (
                    self.scorer.severity_weights.get(issue.severity, 1.0)
                    + self.scorer.category_weights.get(issue.category, 1.0)
                ),
            }
            for issue in sorted_issues[:5]
        ]

    def _analyze_quality_trends(self, metrics: QualityMetrics) -> dict[str, Any]:
        """Analyze quality trends (placeholder for historical analysis)."""
        # This would be enhanced with historical data in a real implementation
        return {
            "current_score": metrics.overall_score,
            "trend_direction": "stable",  # Would be calculated from historical data
            "improvement_rate": 0.0,  # Would be calculated from historical data
            "analysis_date": (
                metrics.analysis_timestamp.isoformat() if metrics.analysis_timestamp else None
            ),
        }

    def batch_analyze_templates(self, template_metrics: list[QualityMetrics]) -> dict[str, Any]:
        """Analyze multiple templates and provide comparative insights."""
        if not template_metrics:
            return {"error": "No templates provided for analysis"}

        return {
            "summary": {
                "total_templates": len(template_metrics),
                "average_score": statistics.mean(m.overall_score for m in template_metrics),
                "score_distribution": self._get_quality_distribution(template_metrics),
                "total_issues": sum(len(m.issues) for m in template_metrics),
            },
            "top_performers": self._get_top_performers(template_metrics),
            "common_issues": self._find_common_issues(template_metrics),
            "best_practices": self._identify_best_practices(template_metrics),
            "improvement_opportunities": self._find_improvement_opportunities(template_metrics),
        }

    def _get_quality_distribution(self, template_metrics: list[QualityMetrics]) -> dict[str, int]:
        """Get distribution of quality grades."""
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}

        for metrics in template_metrics:
            grade = metrics.quality_grade
            distribution[grade] += 1

        return distribution

    def _get_top_performers(self, template_metrics: list[QualityMetrics]) -> list[dict[str, Any]]:
        """Get top performing templates."""
        sorted_templates = sorted(template_metrics, key=lambda m: m.overall_score, reverse=True)

        # Top 5
        return [
            {
                "template_path": metrics.template_path,
                "overall_score": metrics.overall_score,
                "grade": metrics.quality_grade,
                "success_rate": metrics.success_rate,
                "issues_count": len(metrics.issues),
            }
            for metrics in sorted_templates[:5]
        ]

    def _find_common_issues(self, template_metrics: list[QualityMetrics]) -> list[dict[str, Any]]:
        """Find issues that appear across multiple templates."""
        issue_counts = {}

        for metrics in template_metrics:
            for issue in metrics.issues:
                key = (issue.category, issue.message)
                if key not in issue_counts:
                    issue_counts[key] = {
                        "category": issue.category,
                        "message": issue.message,
                        "severity": issue.severity,
                        "count": 0,
                        "templates": [],
                    }
                issue_counts[key]["count"] += 1
                issue_counts[key]["templates"].append(metrics.template_path)

        # Return issues that appear in multiple templates
        common_issues = [
            issue_data for issue_data in issue_counts.values() if issue_data["count"] > 1
        ]

        # Sort by frequency
        common_issues.sort(key=operator.itemgetter("count"), reverse=True)

        return common_issues[:10]  # Top 10 common issues

    def _identify_best_practices(self, template_metrics: list[QualityMetrics]) -> list[str]:
        """Identify best practices from high-quality templates."""
        best_practices = []

        # Find high-quality templates (score >= 85)
        high_quality_templates = [
            metrics for metrics in template_metrics if metrics.overall_score >= 85
        ]

        if high_quality_templates:
            # Analyze common characteristics
            avg_scores = {}
            for category in self.scorer.category_weights:
                category_scores = [
                    metrics.category_scores.get(category, 0) for metrics in high_quality_templates
                ]
                if category_scores:
                    avg_scores[category] = statistics.mean(category_scores)

            # Identify strong categories
            for category, avg_score in avg_scores.items():
                if avg_score >= 90:
                    best_practices.append(
                        f"High-quality templates excel in {category} (avg: {avg_score:.1f})"
                    )

        return best_practices

    def _find_improvement_opportunities(self, template_metrics: list[QualityMetrics]) -> list[str]:
        """Find common improvement opportunities across templates."""
        opportunities = []

        # Analyze category scores across all templates
        category_scores = {}
        for category in self.scorer.category_weights:
            scores = [
                metrics.category_scores[category]
                for metrics in template_metrics
                if category in metrics.category_scores
            ]

            if scores:
                category_scores[category] = statistics.mean(scores)

        # Identify weak areas
        for category, avg_score in category_scores.items():
            if avg_score < 70:
                opportunities.append(
                    f"Organization-wide improvement needed in {category} (avg: {avg_score:.1f})"
                )
            elif avg_score < 80:
                opportunities.append(
                    f"Moderate improvement opportunity in {category} (avg: {avg_score:.1f})"
                )

        return opportunities

    def generate_quality_report(self, template_metrics: list[QualityMetrics]) -> dict[str, Any]:
        """Generate a comprehensive quality report."""
        individual_analyses = [
            {
                "template_path": metrics.template_path,
                "analysis": self.analyze_template_quality(metrics),
            }
            for metrics in template_metrics
        ]

        batch_analysis = self.batch_analyze_templates(template_metrics)

        return {
            "report_metadata": {
                "total_templates_analyzed": len(template_metrics),
                "analysis_timestamp": (
                    template_metrics[0].analysis_timestamp.isoformat()
                    if template_metrics and template_metrics[0].analysis_timestamp
                    else None
                ),
            },
            "batch_analysis": batch_analysis,
            "individual_analyses": individual_analyses,
        }
