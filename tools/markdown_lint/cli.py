"""Command-line interface for the markdown linter."""

import argparse
from pathlib import Path
import sys
from typing import Any

try:
    from .linter import MarkdownLinter
    from .models import IssueSeverity
except ImportError:
    from linter import MarkdownLinter
    from models import IssueSeverity


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Lint and fix markdown files.",
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
        "--no-blank-line-before-heading",
        action="store_false",
        dest="require_blank_line_before_heading",
        help="Don't require blank lines before headings",
    )
    lint_group.add_argument(
        "--no-blank-line-after-heading",
        action="store_false",
        dest="require_blank_line_after_heading",
        help="Don't require blank lines after headings",
    )
    lint_group.add_argument(
        "--allow-multiple-blank-lines",
        action="store_true",
        help="Allow multiple consecutive blank lines",
    )
    lint_group.add_argument(
        "--no-trim-trailing-whitespace",
        action="store_false",
        dest="trim_trailing_whitespace",
        help="Don't trim trailing whitespace",
    )
    lint_group.add_argument(
        "--no-check-blank-lines-around-headings",
        action="store_false",
        dest="check_blank_lines_around_headings",
        help="Disable MD022: Don't check for blank lines around headings",
    )
    lint_group.add_argument(
        "--no-check-blank-lines-around-lists",
        action="store_false",
        dest="check_blank_lines_around_lists",
        help="Disable MD032: Don't check for blank lines around lists",
    )
    lint_group.add_argument(
        "--no-check-ordered-list-numbering",
        action="store_false",
        dest="check_ordered_list_numbering",
        help="Disable MD029: Don't check ordered list item numbering",
    )
    lint_group.add_argument(
        "--no-check-fenced-code-blocks",
        action="store_false",
        dest="check_fenced_code_blocks",
        help="Disable MD031/MD040: Don't check fenced code blocks spacing and language",
    )
    lint_group.add_argument(
        "--no-check-duplicate-headings",
        action="store_false",
        dest="check_duplicate_headings",
        help="Disable MD024: Don't check for duplicate headings",
    )
    lint_group.add_argument(
        "--no-check-bare-urls",
        action="store_false",
        dest="check_bare_urls",
        help="Disable MD034: Don't check for bare URLs",
    )
    lint_group.add_argument(
        "--no-insert-final-newline",
        action="store_false",
        dest="insert_final_newline",
        help="Don't require a final newline at the end of files",
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
        "--verbose",
        "-v",
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

    # Other options
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__import__('tools.markdown_lint', fromlist=['__version__']).__version__}",
    )

    return parser.parse_args(args)


def format_issue(issue, path: Path, verbose: int = 0) -> str:
    """Format an issue as a string."""
    severity = issue.severity.name.lower()

    if verbose >= 1:
        return (
            f"{path!s}:{issue.line}:{issue.column}: {severity}: {issue.code}: {issue.message}\n"
            f"  {issue.context or ''}"
        )
    return f"{path!s}:{issue.line}:{issue.column}: {severity}: {issue.message}"


def print_report(reports: dict[Path, Any], args: argparse.Namespace) -> int:
    """Print a report of all issues found."""
    issue_count = 0
    file_count = 0

    if args.format == "json":
        output = []
        for path, report in reports.items():
            if report["issues"]:
                file_count += 1
                issue_count += len(report["issues"])
                output.append(
                    {
                        "file": str(path),
                        "issues": [
                            {
                                "line": issue.line,
                                "column": issue.column,
                                "code": issue.code,
                                "message": issue.message,
                                "severity": issue.severity.name.lower(),
                                "fixable": issue.fixable,
                            }
                            for issue in report["issues"]
                        ],
                    }
                )

        if output or args.verbose > 0:
            pass
    else:
        # Text output
        for path, report in sorted(reports.items()):
            if report["issues"]:
                file_count += 1
                issue_count += len(report["issues"])

                for _issue in sorted(report["issues"], key=lambda x: x.line):
                    pass

        # Print summary
        if issue_count > 0 or args.verbose > 0:
            pass

    return 1 if issue_count > 0 else 0


def main() -> int:
    """Main entry point for the CLI."""
    args = parse_args(sys.argv[1:])

    # Initialize linter with configuration
    linter = MarkdownLinter(
        {
            "max_line_length": args.max_line_length,
            "require_blank_line_before_heading": args.require_blank_line_before_heading,
            "require_blank_line_after_heading": args.require_blank_line_after_heading,
            "allow_multiple_blank_lines": args.allow_multiple_blank_lines,
            "trim_trailing_whitespace": args.trim_trailing_whitespace,
            "insert_final_newline": args.insert_final_newline,
            "check_blank_lines_around_headings": args.check_blank_lines_around_headings,
            "check_blank_lines_around_lists": args.check_blank_lines_around_lists,
            "check_ordered_list_numbering": args.check_ordered_list_numbering,
            "check_fenced_code_blocks": args.check_fenced_code_blocks,
            "check_duplicate_headings": args.check_duplicate_headings,
            "check_bare_urls": args.check_bare_urls,
        }
    )

    # Process each path
    paths = [Path(p) for p in args.paths]
    for path in paths:
        if path.is_file():
            linter.check_file(path)
        elif path.is_dir():
            linter.check_directory(path, exclude=args.exclude)
        else:
            return 1

    # Filter issues by severity
    min_severity = {
        "error": IssueSeverity.ERROR,
        "warning": IssueSeverity.WARNING,
        "style": IssueSeverity.STYLE,
    }[args.severity.lower()]

    filtered_reports = {}
    for path, report in linter.reports.items():
        filtered_issues = [
            issue for issue in report.issues if issue.severity.value >= min_severity.value
        ]
        if filtered_issues:
            filtered_reports[path] = {"issues": filtered_issues}

    # Apply fixes if requested
    if args.fix and not args.dry_run:
        fixed_count = linter.fix_files(dry_run=False)
        if fixed_count > 0:
            pass
    elif args.dry_run:
        linter.fix_files(dry_run=True)

    # Print report
    if not args.fix or args.dry_run:
        return print_report(filtered_reports, args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
