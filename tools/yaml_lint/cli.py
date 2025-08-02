"""Command-line interface for the YAML linter."""

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .linter import YAMLLinter
from .models import IssueSeverity


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Lint and fix YAML files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Positional arguments
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to check (default: current directory)",
    )

    # Linting options
    lint_group = parser.add_argument_group("Linting Options")
    lint_group.add_argument(
        "--max-line-length",
        type=int,
        default=120,
        help="Maximum allowed line length",
    )
    lint_group.add_argument(
        "--indent-size",
        type=int,
        default=2,
        help="Expected indentation size",
    )
    lint_group.add_argument(
        "--no-document-start",
        dest="enforce_document_start",
        action="store_false",
        default=True,
        help="Don't require document start marker (---)",
    )
    lint_group.add_argument(
        "--document-end",
        dest="enforce_document_end",
        action="store_true",
        default=False,
        help="Require document end marker (...)",
    )
    lint_group.add_argument(
        "--no-empty-values",
        dest="check_empty_values",
        action="store_false",
        default=True,
        help="Don't check for empty values",
    )
    lint_group.add_argument(
        "--no-truthy",
        dest="check_truthy",
        action="store_false",
        default=True,
        help="Don't check for problematic truthy values",
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    output_group.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    output_group.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times)",
    )

    # Fixing options
    fix_group = parser.add_argument_group("Fixing Options")
    fix_group.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix fixable issues",
    )
    fix_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )

    # Filtering options
    filter_group = parser.add_argument_group("Filtering Options")
    filter_group.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Exclude files/directories that match the given glob patterns",
    )
    filter_group.add_argument(
        "--severity",
        choices=["error", "warning", "style"],
        default="warning",
        help="Minimum severity to report",
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser.parse_args(args)


def get_severity_threshold(severity_name: str) -> IssueSeverity:
    """Convert severity name to IssueSeverity enum."""
    mapping = {
        "error": IssueSeverity.ERROR,
        "warning": IssueSeverity.WARNING,
        "style": IssueSeverity.STYLE,
    }
    return mapping[severity_name]


def format_issue_text(issue, file_path: Path, use_color: bool = True) -> str:
    """Format a single issue for text output."""
    colors = {
        IssueSeverity.ERROR: "\033[31m" if use_color else "",  # Red
        IssueSeverity.WARNING: "\033[33m" if use_color else "",  # Yellow
        IssueSeverity.STYLE: "\033[36m" if use_color else "",  # Cyan
    }
    reset = "\033[0m" if use_color else ""

    severity_color = colors.get(issue.severity, "")
    severity_name = issue.severity.name.lower()

    location = f"{file_path}:{issue.line}:{issue.column}"
    message = f"{severity_color}{severity_name}{reset}: {issue.message}"

    if issue.code:
        message += f" [{issue.code}]"

    return f"  {location}: {message}"


def format_output_text(reports: dict[Path, Any], args: argparse.Namespace) -> str:
    """Format output in text format."""
    lines = []
    severity_threshold = get_severity_threshold(args.severity)
    use_color = not args.no_color and sys.stdout.isatty()

    total_issues = 0
    total_files = 0

    for file_path, report in reports.items():
        if not report.has_issues:
            continue

        # Filter issues by severity
        filtered_issues = [
            issue for issue in report.issues if issue.severity.value <= severity_threshold.value
        ]

        if not filtered_issues:
            continue

        total_files += 1
        total_issues += len(filtered_issues)

        lines.append(f"\n{file_path}:")

        lines.extend(format_issue_text(issue, file_path, use_color) for issue in filtered_issues)

    if total_issues > 0:
        lines.append(f"\nFound {total_issues} issue(s) in {total_files} file(s)")
    elif args.verbose > 0:
        lines.append("No issues found")

    return "\n".join(lines)


def format_output_json(reports: dict[Path, Any], args: argparse.Namespace) -> str:
    """Format output in JSON format."""
    severity_threshold = get_severity_threshold(args.severity)

    output = []
    for file_path, report in reports.items():
        if not report.has_issues:
            continue

        # Filter issues by severity
        filtered_issues = [
            issue for issue in report.issues if issue.severity.value <= severity_threshold.value
        ]

        if not filtered_issues:
            continue

        file_data = {"file": str(file_path), "issues": []}

        for issue in filtered_issues:
            issue_data = {
                "line": issue.line,
                "column": issue.column,
                "code": issue.code,
                "message": issue.message,
                "severity": issue.severity.name.lower(),
                "fixable": issue.fixable,
            }
            file_data["issues"].append(issue_data)

        output.append(file_data)

    return json.dumps(output, indent=2)


def run_linter(args: argparse.Namespace) -> int:
    """Run the YAML linter with the given arguments."""
    # Create linter configuration
    config = {
        "max_line_length": args.max_line_length,
        "indent_size": args.indent_size,
        "enforce_document_start": args.enforce_document_start,
        "enforce_document_end": args.enforce_document_end,
        "check_empty_values": args.check_empty_values,
        "check_truthy": args.check_truthy,
    }

    linter = YAMLLinter(config)

    # Check all specified paths
    for path_str in args.paths:
        path = Path(path_str)

        if path.is_file():
            if path.suffix in {".yml", ".yaml"}:
                linter.check_file(path)
            elif args.verbose > 0:
                pass
        elif path.is_dir():
            linter.check_directory(path, exclude=args.exclude)

    # Apply fixes if requested
    if args.fix:
        if args.dry_run:
            fixed_count = linter.fix_files(dry_run=True)
            if fixed_count == 0 and args.verbose > 0:
                pass
        else:
            fixed_count = linter.fix_files(dry_run=False)
            if fixed_count > 0:
                # Re-run linter to show remaining issues
                if args.verbose > 0:
                    new_linter = YAMLLinter(config)
                    for file_path in linter.reports:
                        new_linter.check_file(file_path)
                    linter.reports = new_linter.reports

    # Generate output
    if args.format == "json":
        output = format_output_json(linter.reports, args)
    else:
        output = format_output_text(linter.reports, args)

    if output.strip():
        pass

    # Determine exit code
    severity_threshold = get_severity_threshold(args.severity)
    has_issues_at_threshold = any(
        any(issue.severity.value <= severity_threshold.value for issue in report.issues)
        for report in linter.reports.values()
    )

    return 1 if has_issues_at_threshold else 0


def main(args: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    try:
        parsed_args = parse_args(args or sys.argv[1:])
        return run_linter(parsed_args)
    except KeyboardInterrupt:
        return 130
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())
