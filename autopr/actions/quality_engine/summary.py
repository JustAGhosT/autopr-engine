"""
Summary generation for quality engine results
"""

from .models import ToolResult


def build_comprehensive_summary(
    results: dict[str, ToolResult], ai_summary: str | None = None
) -> str:
    """Build a detailed summary of all quality tool results."""
    summary_lines = ["# Quality Analysis Summary"]

    total_issues = sum(len(result.issues) for result in results.values())
    total_files_with_issues: set[str] = set()
    for result in results.values():
        total_files_with_issues.update(result.files_with_issues)

    summary_lines.append("\n## Overview")
    summary_lines.append(f"- Total issues found: {total_issues}")
    summary_lines.append(f"- Files with issues: {len(total_files_with_issues)}")
    summary_lines.append(f"- Tools executed: {len(results)}")

    if ai_summary:
        summary_lines.append("\n## AI-Enhanced Analysis")
        summary_lines.append(ai_summary)

    summary_lines.append("\n## Details by Tool")

    for tool_name, result in sorted(results.items(), key=lambda x: x[0]):
        summary_lines.append(f"\n### {tool_name.upper()}")
        summary_lines.append(f"- Issues found: {len(result.issues)}")
        summary_lines.append(f"- Files affected: {len(result.files_with_issues)}")
        summary_lines.append(f"- Execution time: {result.execution_time:.2f}s")

        if result.issues:
            summary_lines.append("\n#### Top Issues:")
            for issue in result.issues[:5]:  # Show first 5 issues
                file = issue.get("file", "unknown")
                line = issue.get("line", "?")
                message = issue.get("message", "No details")
                summary_lines.append(f"- {file}:{line} - {message}")

            if len(result.issues) > 5:
                summary_lines.append(f"- ... and {len(result.issues) - 5} more issues")

    return "\n".join(summary_lines)
