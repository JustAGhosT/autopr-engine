#!/usr/bin/env python3
"""
Report Generators Module
=======================

Multiple report format generators for quality assurance results.

Features:
- JSON, Markdown, and HTML report generation
- Factory pattern for different report types
- Customizable report templates
- Rich formatting and styling
"""

from abc import ABC, abstractmethod
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from autopr.quality.template_metrics import QualityMetrics

from .template_validators import ValidationSeverity


class ReportGenerator(ABC):
    """Abstract base class for report generators."""

    @abstractmethod
    def generate_report(
        self, metrics: QualityMetrics, analysis: dict[str, Any] | None = None
    ) -> str:
        """Generate a quality assurance report."""

    @abstractmethod
    def generate_batch_report(
        self,
        template_metrics: list[QualityMetrics],
        batch_analysis: dict[str, Any] | None = None,
    ) -> str:
        """Generate a batch report for multiple templates."""


class JSONReportGenerator(ReportGenerator):
    """Generates JSON format reports."""

    def __init__(self, indent: int = 2):
        """Initialize JSON report generator."""
        self.indent = indent

    def generate_report(
        self, metrics: QualityMetrics, analysis: dict[str, Any] | None = None
    ) -> str:
        """Generate JSON report for a single template."""
        report_data = {
            "template_path": metrics.template_path,
            "analysis_timestamp": (
                metrics.analysis_timestamp.isoformat() if metrics.analysis_timestamp else None
            ),
            "quality_metrics": {
                "overall_score": metrics.overall_score,
                "quality_grade": metrics.quality_grade,
                "success_rate": metrics.success_rate,
                "category_scores": metrics.category_scores,
                "total_checks": metrics.total_checks,
                "passed_checks": metrics.passed_checks,
                "issues_summary": {
                    "total_issues": len(metrics.issues),
                    "errors": metrics.errors_count,
                    "warnings": metrics.warnings_count,
                    "info": metrics.info_count,
                },
            },
            "issues": [
                {
                    "severity": issue.severity.value,
                    "category": issue.category,
                    "message": issue.message,
                    "location": issue.location,
                    "suggestion": issue.suggestion,
                    "rule_id": issue.rule_id,
                }
                for issue in metrics.issues
            ],
        }

        if analysis:
            report_data["analysis"] = analysis

        return json.dumps(report_data, indent=self.indent, ensure_ascii=False)

    def generate_batch_report(
        self,
        template_metrics: list[QualityMetrics],
        batch_analysis: dict[str, Any] | None = None,
    ) -> str:
        """Generate JSON batch report for multiple templates."""
        report_data = {
            "batch_analysis_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_templates": len(template_metrics),
                "average_score": (
                    sum(m.overall_score for m in template_metrics) / len(template_metrics)
                    if template_metrics
                    else 0
                ),
                "total_issues": sum(len(m.issues) for m in template_metrics),
                "total_errors": sum(m.errors_count for m in template_metrics),
                "total_warnings": sum(m.warnings_count for m in template_metrics),
            },
            "templates": [
                {
                    "path": metrics.template_path,
                    "score": metrics.overall_score,
                    "grade": metrics.quality_grade,
                    "issues_count": len(metrics.issues),
                    "has_critical_issues": metrics.has_critical_issues,
                }
                for metrics in template_metrics
            ],
        }

        if batch_analysis:
            report_data["batch_analysis"] = batch_analysis

        return json.dumps(report_data, indent=self.indent, ensure_ascii=False)


class MarkdownReportGenerator(ReportGenerator):
    """Generates Markdown format reports."""

    def generate_report(
        self, metrics: QualityMetrics, analysis: dict[str, Any] | None = None
    ) -> str:
        """Generate Markdown report for a single template."""
        lines = []

        # Header
        template_name = Path(metrics.template_path).name if metrics.template_path else "Template"
        lines.extend((f"# Quality Assurance Report: {template_name}", ""))

        # Metadata
        if metrics.analysis_timestamp:
            lines.append(
                f"**Analysis Date:** {metrics.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        lines.append(f"**Template Path:** `{metrics.template_path}`")
        lines.append("")

        # Quality Summary
        lines.append("## Quality Summary")
        lines.append("")
        lines.append(
            f"- **Overall Score:** {metrics.overall_score:.1f}/100 (Grade: {metrics.quality_grade})"
        )
        lines.append(f"- **Success Rate:** {metrics.success_rate:.1f}%")
        lines.append(
            f"- **Total Issues:** {len(metrics.issues)} ({metrics.errors_count} errors, {metrics.warnings_count} warnings)"
        )
        lines.append("")

        # Category Scores
        if metrics.category_scores:
            lines.extend(
                (
                    "### Category Scores",
                    "",
                    "| Category | Score | Status |",
                    "|----------|-------|--------|",
                )
            )

            for category, score in metrics.category_scores.items():
                status = "✅ Good" if score >= 80 else "🟡 Fair" if score >= 60 else "🔴 Poor"
                lines.append(f"| {category.title()} | {score:.1f}/100 | {status} |")
            lines.append("")

        # Issues Details
        if metrics.issues:
            lines.extend(("## Issues Details", ""))

            # Group issues by severity
            errors = metrics.get_issues_by_severity(ValidationSeverity.ERROR)
            warnings = metrics.get_issues_by_severity(ValidationSeverity.WARNING)
            info_issues = metrics.get_issues_by_severity(ValidationSeverity.INFO)

            for severity_name, issues_list, icon in [
                ("Errors", errors, "🔴"),
                ("Warnings", warnings, "🟡"),
                ("Information", info_issues, "🔵"),
            ]:
                if issues_list:
                    lines.extend((f"### {icon} {severity_name} ({len(issues_list)})", ""))
                    for i, issue in enumerate(issues_list, 1):
                        lines.extend(
                            (
                                f"**{i}. {issue.message}**",
                                f"- Category: {issue.category}",
                                f"- Rule: {issue.rule_id}",
                            )
                        )
                        if issue.suggestion:
                            lines.append(f"- Suggestion: {issue.suggestion}")
                        lines.append("")

        # Analysis Section
        if analysis:
            lines.extend(("## Quality Analysis", ""))

            if analysis.get("recommendations"):
                lines.extend(("### 💡 Recommendations", ""))
                for i, recommendation in enumerate(analysis["recommendations"], 1):
                    lines.append(f"{i}. {recommendation}")
                lines.append("")

        return "\n".join(lines)

    def generate_batch_report(
        self,
        template_metrics: list[QualityMetrics],
        batch_analysis: dict[str, Any] | None = None,
    ) -> str:
        """Generate Markdown batch report for multiple templates."""
        lines = []

        # Header
        lines.extend(
            (
                "# Batch Quality Assurance Report",
                "",
                f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Total Templates:** {len(template_metrics)}",
                "",
            )
        )

        # Summary Statistics
        if template_metrics:
            avg_score = sum(m.overall_score for m in template_metrics) / len(template_metrics)
            total_issues = sum(len(m.issues) for m in template_metrics)

            lines.extend(
                (
                    "## Summary Statistics",
                    "",
                    f"- **Average Score:** {avg_score:.1f}/100",
                    f"- **Total Issues:** {total_issues}",
                    f"- **Templates with Errors:** {sum(1 for m in template_metrics if m.has_critical_issues)}",
                    "",
                )
            )

        # Template Overview
        lines.extend(
            (
                "## Template Overview",
                "",
                "| Template | Score | Grade | Issues | Status |",
                "|----------|-------|-------|--------|--------|",
            )
        )

        for metrics in sorted(template_metrics, key=lambda m: m.overall_score, reverse=True):
            template_name = Path(metrics.template_path).name if metrics.template_path else "Unknown"
            status = (
                "🔴 Critical"
                if metrics.has_critical_issues
                else "✅ Good"
                if metrics.overall_score >= 80
                else "🟡 Needs Work"
            )
            lines.append(
                f"| {template_name} | {metrics.overall_score:.1f} | {metrics.quality_grade} | {len(metrics.issues)} | {status} |"
            )

        lines.append("")
        return "\n".join(lines)


class HTMLReportGenerator(ReportGenerator):
    """Generates HTML format reports with basic styling."""

    def generate_report(
        self, metrics: QualityMetrics, analysis: dict[str, Any] | None = None
    ) -> str:
        """Generate HTML report for a single template."""
        template_name = Path(metrics.template_path).name if metrics.template_path else "Template"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>QA Report: {template_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e9ecef; border-radius: 3px; }}
        .issues {{ margin: 20px 0; }}
        .error {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .info {{ color: #17a2b8; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Quality Assurance Report: {template_name}</h1>
        <p>Analysis Date: {metrics.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S') if metrics.analysis_timestamp else 'N/A'}</p>
    </div>

    <div class="summary">
        <h2>Quality Summary</h2>
        <div class="metric">Overall Score: {metrics.overall_score:.1f}/100 (Grade: {metrics.quality_grade})</div>
        <div class="metric">Success Rate: {metrics.success_rate:.1f}%</div>
        <div class="metric">Total Issues: {len(metrics.issues)}</div>
        <div class="metric error">Errors: {metrics.errors_count}</div>
        <div class="metric warning">Warnings: {metrics.warnings_count}</div>
    </div>

    <div class="issues">
        <h2>Issues</h2>"""

        if metrics.issues:
            for issue in metrics.issues:
                severity_class = issue.severity.value.lower()
                html += f"""
        <div class="{severity_class}">
            <strong>{issue.category}: {issue.message}</strong><br>
            Rule: {issue.rule_id}<br>
            {f'Suggestion: {issue.suggestion}<br>' if issue.suggestion else ''}
        </div>"""
        else:
            html += "<p>No issues found!</p>"

        html += """
    </div>
</body>
</html>"""

        return html

    def generate_batch_report(
        self,
        template_metrics: list[QualityMetrics],
        batch_analysis: dict[str, Any] | None = None,
    ) -> str:
        """Generate HTML batch report for multiple templates."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Batch QA Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .template {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 3px; }}
        .good {{ border-left: 4px solid #28a745; }}
        .warning {{ border-left: 4px solid #ffc107; }}
        .critical {{ border-left: 4px solid #dc3545; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Batch Quality Assurance Report</h1>
        <p>Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Templates: {len(template_metrics)}</p>
    </div>

    <h2>Template Overview</h2>"""

        for metrics in sorted(template_metrics, key=lambda m: m.overall_score, reverse=True):
            template_name = Path(metrics.template_path).name if metrics.template_path else "Unknown"
            status_class = (
                "critical"
                if metrics.has_critical_issues
                else "good"
                if metrics.overall_score >= 80
                else "warning"
            )

            html += f"""
    <div class="template {status_class}">
        <strong>{template_name}</strong> - Score: {metrics.overall_score:.1f} (Grade: {metrics.quality_grade})<br>
        Issues: {len(metrics.issues)} ({metrics.errors_count} errors)
    </div>"""

        html += """
</body>
</html>"""

        return html


class ReportGeneratorFactory:
    """Factory for creating report generators."""

    @staticmethod
    def create_generator(format_type: str) -> ReportGenerator:
        """Create a report generator for the specified format."""
        format_type = format_type.lower()

        if format_type == "json":
            return JSONReportGenerator()
        if format_type in {"markdown", "md"}:
            return MarkdownReportGenerator()
        if format_type == "html":
            return HTMLReportGenerator()
        msg = f"Unsupported report format: {format_type}"
        raise ValueError(msg)

    @staticmethod
    def get_supported_formats() -> list[str]:
        """Get list of supported report formats."""
        return ["json", "markdown", "md", "html"]


# Convenience functions
def generate_report(
    metrics: QualityMetrics,
    format_type: str = "markdown",
    analysis: dict[str, Any] | None = None,
) -> str:
    """Generate a quality assurance report in the specified format."""
    generator = ReportGeneratorFactory.create_generator(format_type)
    return generator.generate_report(metrics, analysis)


def generate_batch_report(
    template_metrics: list[QualityMetrics],
    format_type: str = "markdown",
    batch_analysis: dict[str, Any] | None = None,
) -> str:
    """Generate a batch quality assurance report in the specified format."""
    generator = ReportGeneratorFactory.create_generator(format_type)
    return generator.generate_batch_report(template_metrics, batch_analysis)


def save_report(content: str, output_path: Path, format_type: str = "markdown") -> str:
    """Save report content to file."""
    # Ensure proper file extension
    extensions = {"json": ".json", "markdown": ".md", "md": ".md", "html": ".html"}
    extension = extensions.get(format_type.lower(), ".txt")

    if not str(output_path).endswith(extension):
        output_path = output_path.with_suffix(extension)

    # Create directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write content
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(output_path)
    return str(output_path)
