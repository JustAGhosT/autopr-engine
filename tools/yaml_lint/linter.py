"""Core YAML linter implementation with auto-fixing."""

import re
from pathlib import Path
from typing import Any

from tools.yaml_lint.models import FileReport, IssueSeverity, LintIssue

# Constants for magic numbers
MIN_LINE_NUMBER = 1
SERVICES_INDENT = 4
INPUTS_INDENT = 4
JOBS_INDENT = 0
JOBS_SECTION_INDENT = 2
ENVIRONMENT_INDENT = 4
DEFAULT_INDENT_SIZE = 2


class YAMLLinter:
    """YAML linter for checking and fixing common issues."""

    # Default configuration
    DEFAULT_CONFIG = {
        "max_line_length": 120,
        "indent_size": 2,
        "enforce_document_start": True,
        "enforce_document_end": False,
        "check_empty_values": True,
        "check_key_ordering": False,
        "check_truthy": True,
        "allow_non_breakable_words": True,
        "allow_non_breakable_inline_mappings": False,
    }

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or self.DEFAULT_CONFIG.copy()
        self.reports = {}

    def lint_file(self, file_path: Path) -> FileReport:
        """Lint a single YAML file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return FileReport(
                file_path,
                [
                    LintIssue(
                        line=1,
                        column=1,
                        message=f"Could not read file: {e}",
                        code="YML001",
                        severity=IssueSeverity.ERROR,
                        fixable=False,
                    )
                ],
            )

        return self.lint_content(content, file_path)

    def lint_content(self, content: str, file_path: Path | None = None) -> FileReport:
        """Lint YAML content."""
        lines = content.splitlines()
        report = FileReport(file_path or Path("unknown"), [])

        # Check line-level issues
        self._check_line_issues(report, lines)

        # Check document-level issues
        self._check_document_issues(report, content, lines)

        # Check key ordering if enabled
        if self.config["check_key_ordering"]:
            self._check_key_ordering(report, lines)

        return report

    def _check_line_issues(self, report: FileReport, lines: list[str]) -> None:
        """Check line-level issues."""
        for i, line in enumerate(lines):
            line_num = i + 1

            # Check line length
            if len(line) > self.config["max_line_length"]:
                report.add_issue(
                    LintIssue(
                        line=line_num,
                        column=self.config["max_line_length"] + 1,
                        message=f"Line too long ({len(line)} > {self.config['max_line_length']} characters)",
                        code="YML010",
                        severity=IssueSeverity.WARNING,
                        fix=lambda line_content: line_content.rstrip()
                        + ("\n" if line_content.endswith(("\n", "\r\n")) else ""),
                        fixable=True,
                    )
                )

            # Check for tabs
            if "\t" in line:
                report.add_issue(
                    LintIssue(
                        line=line_num,
                        column=line.find("\t") + 1,
                        message="Use spaces instead of tabs",
                        code="YML012",
                        severity=IssueSeverity.WARNING,
                        fix=lambda line_content: line_content.replace(
                            "\t", " " * self.config["indent_size"]
                        ),
                        fixable=True,
                    )
                )

            # Check indentation
            self._check_indentation(report, line, line_num)

            # Check for trailing whitespace
            if line.rstrip() != line:
                report.add_issue(
                    LintIssue(
                        line=line_num,
                        column=len(line.rstrip()) + 1,
                        message="Trailing whitespace",
                        code="YML013",
                        severity=IssueSeverity.STYLE,
                        fix=lambda line_content: line_content.rstrip(),
                        fixable=True,
                    )
                )

            # Check for missing space after colon
            if ":" in line and not line.strip().endswith(":"):
                colon_pos = line.find(":")
                if colon_pos < len(line) - 1 and line[colon_pos + 1] != " ":
                    report.add_issue(
                        LintIssue(
                            line=line_num,
                            column=colon_pos + 1,
                            message="Missing space after colon",
                            code="YML021",
                            severity=IssueSeverity.STYLE,
                            fix=lambda line_content: re.sub(
                                r"(\w):(?!\s|$)", r"\1: ", line_content
                            ),
                            fixable=True,
                        )
                    )

            # Check for multiple spaces after colon
            if ":" in line:
                colon_pos = line.find(":")
                if (
                    colon_pos < len(line) - 2
                    and line[colon_pos + 1 : colon_pos + 3] == "  "
                ):
                    report.add_issue(
                        LintIssue(
                            line=line_num,
                            column=colon_pos + 2,
                            message="Multiple spaces after colon",
                            code="YML022",
                            severity=IssueSeverity.STYLE,
                            fix=lambda line_content: re.sub(
                                r":  +", ": ", line_content
                            ),
                            fixable=True,
                        )
                    )

            # Check for truthy values if enabled
            if self.config["check_truthy"]:
                self._check_truthy_values(report, line, line_num)

    def _check_indentation(self, report: FileReport, line: str, line_num: int) -> None:
        """Check indentation of a line."""
        if not line.strip():
            return

        leading_spaces = len(line) - len(line.lstrip())
        expected_indent = self.config["indent_size"]

        # Check if indentation is consistent
        if leading_spaces > 0 and leading_spaces % expected_indent != 0:
            report.add_issue(
                LintIssue(
                    line=line_num,
                    column=1,
                    message=f"Indentation should be multiple of {expected_indent} spaces",
                    code="YML030",
                    severity=IssueSeverity.WARNING,
                    fix=lambda line_content: " "
                    * (leading_spaces // expected_indent * expected_indent)
                    + line_content.lstrip(),
                    fixable=True,
                )
            )

    def _check_truthy_values(
        self, report: FileReport, line: str, line_num: int
    ) -> None:
        """Check for truthy values that should be explicit."""
        if ":" not in line:
            return

        # Extract value after colon
        parts = line.split(":", 1)
        if len(parts) != 2:
            return

        value = parts[1].strip()
        truthy_mappings = {
            "yes": "true",
            "no": "false",
            "on": "true",
            "off": "false",
            "true": "true",
            "false": "false",
        }

        if value.lower() in truthy_mappings:
            old_val = value
            new_val = truthy_mappings[value.lower()]

            def create_truthy_fix(old_val: str, new_val: str):
                return lambda line_content: re.sub(
                    rf":\s+{re.escape(old_val)}\s*$", f": {new_val}", line_content
                )

            report.add_issue(
                LintIssue(
                    line=line_num,
                    column=line.find(":") + 2,
                    message=f"Use explicit boolean '{new_val}' instead of '{old_val}'",
                    code="YML040",
                    severity=IssueSeverity.STYLE,
                    fix=create_truthy_fix(old_val, new_val),
                    fixable=True,
                )
            )

    def _check_document_issues(
        self, report: FileReport, content: str, lines: list[str]
    ) -> None:
        """Check document-level issues."""
        # Check for document start marker
        if self.config["enforce_document_start"] and not content.strip().startswith(
            "---"
        ):
            report.add_issue(
                LintIssue(
                    line=1,
                    column=1,
                    message="Document should start with '---'",
                    code="YML040",
                    severity=IssueSeverity.STYLE,
                    fix=lambda line_content: (
                        "---\n" + line_content if line_content.strip() else "---\n"
                    ),
                    fixable=True,
                )
            )

        # Check for document end marker
        if self.config["enforce_document_end"] and not content.strip().endswith("..."):
            report.add_issue(
                LintIssue(
                    line=len(lines),
                    column=1,
                    message="Document should end with '...'",
                    code="YML041",
                    severity=IssueSeverity.STYLE,
                    fix=lambda line_content: line_content.rstrip() + "\n...\n",
                    fixable=True,
                )
            )

        # Check for empty values
        if self.config["check_empty_values"]:
            self._check_empty_values(report, lines)

    def _check_empty_values(self, report: FileReport, lines: list[str]) -> None:
        """Check for empty values that should be explicit."""
        for i, line in enumerate(lines):
            line_num = i + 1
            line_content = line.strip()

            if ":" in line_content and line_content.endswith(":"):
                report.add_issue(
                    LintIssue(
                        line=line_num,
                        column=len(line_content),
                        message="Empty value should be explicit (use 'null' or '')",
                        code="YML050",
                        severity=IssueSeverity.WARNING,
                        fix=lambda line_content: re.sub(
                            r"^(\s*\w+:)\s*$", r"\1 null", line_content
                        ),
                        fixable=True,
                    )
                )

    def _check_key_ordering(self, report: FileReport, lines: list[str]) -> None:
        """Check for key ordering issues."""
        # This is a simplified implementation
        # In practice, you'd want to parse the YAML structure and check ordering

    def fix_files(self, dry_run: bool = False) -> int:
        """Apply all fixes to files with issues."""
        fixed_count = 0

        for file_path, report in self.reports.items():
            if report.fixed_content is not None:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.writelines(report.fixed_content)
                    fixed_count += 1
                except Exception:
                    pass

        return fixed_count
