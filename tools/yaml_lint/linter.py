"""Core YAML linter implementation with auto-fixing."""

from collections.abc import Callable
from pathlib import Path
import re
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

from .models import FileReport, IssueSeverity, LintIssue


class YAMLLinter:
    """YAML linter and auto-fixer."""

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
        """Initialize the YAML linter with configuration."""
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.reports: dict[Path, FileReport] = {}

    def check_file(self, file_path: str | Path) -> FileReport:
        """Check a single YAML file for issues."""
        file_path = Path(file_path)

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            report = FileReport(file_path)
            report.add_issue(
                LintIssue(
                    line=0,
                    message=f"Failed to read file: {e}",
                    code="YML001",
                    severity=IssueSeverity.ERROR,
                )
            )
            return report

        report = self._check_content(content, file_path)
        self.reports[file_path] = report

        # Apply fixes if there are any fixable issues
        if report.has_fixable_issues:
            report.fixed_content = self._apply_fixes(content, report.issues)

        return report

    def _check_content(self, content: str, file_path: Path) -> FileReport:
        """Check YAML content for various issues."""
        report = FileReport(file_path)
        lines = content.splitlines(keepends=True)

        # Check if file is valid YAML first
        if yaml is not None:
            try:
                yaml.safe_load(content)
            except yaml.YAMLError as e:
                line_num = getattr(e, "problem_mark", None)
                line_num = line_num.line + 1 if line_num else 1
                report.add_issue(
                    LintIssue(
                        line=line_num,
                        message=f"YAML syntax error: {e}",
                        code="YML002",
                        severity=IssueSeverity.ERROR,
                    )
                )
                return report  # Don't continue if YAML is invalid

        # Check each line for issues
        for line_num, line in enumerate(lines, 1):
            self._check_line_issues(report, line_num, line)

        # Check document-level issues
        self._check_document_issues(report, content, lines)

        return report

    def _check_line_issues(self, report: FileReport, line_num: int, line: str) -> None:
        """Check individual line for various issues."""
        # Check line length
        if len(line.rstrip()) > self.config["max_line_length"]:
            fix_func = self._get_line_length_fix(line)
            report.add_issue(
                LintIssue(
                    line=line_num,
                    message=f"Line too long ({len(line.rstrip())} > {self.config['max_line_length']} characters)",
                    code="YML010",
                    severity=IssueSeverity.WARNING,
                    fix=fix_func,
                    fixable=fix_func is not None,
                )
            )

        # Check trailing whitespace
        if line.rstrip() != line.rstrip("\n\r"):
            report.add_issue(
                LintIssue(
                    line=line_num,
                    message="Trailing whitespace",
                    code="YML011",
                    severity=IssueSeverity.STYLE,
                    fix=lambda l: l.rstrip() + ("\n" if l.endswith(("\n", "\r\n")) else ""),
                    fixable=True,
                )
            )

        # Check for tabs instead of spaces
        if "\t" in line:
            report.add_issue(
                LintIssue(
                    line=line_num,
                    message="Use spaces instead of tabs for indentation",
                    code="YML012",
                    severity=IssueSeverity.WARNING,
                    fix=lambda l: l.replace("\t", " " * self.config["indent_size"]),
                    fixable=True,
                )
            )

        # Check indentation
        self._check_indentation(report, line_num, line)

        # Check key-value formatting
        self._check_key_value_formatting(report, line_num, line)

        # Check for common truthy issues
        if self.config["check_truthy"]:
            self._check_truthy_values(report, line_num, line)

    def _check_indentation(self, report: FileReport, line_num: int, line: str) -> None:
        """Check YAML indentation issues."""
        if not line.strip():
            return

        leading_spaces = len(line) - len(line.lstrip(" "))
        expected_indent = self.config["indent_size"]

        # Check if indentation is consistent with configured size
        if leading_spaces > 0 and leading_spaces % expected_indent != 0:
            # Calculate correct indentation
            indent_level = leading_spaces // expected_indent
            if leading_spaces % expected_indent > expected_indent // 2:
                indent_level += 1
            correct_indent = indent_level * expected_indent

            def fix_indentation(l: str) -> str:
                return " " * correct_indent + l.lstrip(" ")

            report.add_issue(
                LintIssue(
                    line=line_num,
                    message=f"Incorrect indentation: {leading_spaces} spaces, expected multiple of {expected_indent}",
                    code="YML020",
                    severity=IssueSeverity.WARNING,
                    fix=fix_indentation,
                    fixable=True,
                )
            )

    def _check_key_value_formatting(self, report: FileReport, line_num: int, line: str) -> None:
        """Check key-value pair formatting."""
        # Check for missing space after colon
        if ":" in line and not line.strip().startswith("#"):
            colon_pattern = r"(\w):(?!\s|$)"
            if re.search(colon_pattern, line):
                report.add_issue(
                    LintIssue(
                        line=line_num,
                        message="Missing space after colon",
                        code="YML021",
                        severity=IssueSeverity.STYLE,
                        fix=lambda l: re.sub(r"(\w):(?!\s|$)", r"\1: ", l),
                        fixable=True,
                    )
                )

        # Check for multiple spaces after colon
        multiple_spaces_pattern = r":  +"
        if re.search(multiple_spaces_pattern, line) and not line.strip().startswith("#"):
            report.add_issue(
                LintIssue(
                    line=line_num,
                    message="Too many spaces after colon",
                    code="YML022",
                    severity=IssueSeverity.STYLE,
                    fix=lambda l: re.sub(r":  +", ": ", l),
                    fixable=True,
                )
            )

    def _check_truthy_values(self, report: FileReport, line_num: int, line: str) -> None:
        """Check for potentially confusing truthy values."""
        if ":" not in line or line.strip().startswith("#"):
            return

        # Look for potentially problematic truthy values
        problematic_values = {
            "yes": "true",
            "no": "false",
            "on": "true",
            "off": "false",
            "Yes": "true",
            "No": "false",
            "YES": "true",
            "NO": "false",
            "On": "true",
            "Off": "false",
            "ON": "true",
            "OFF": "false",
        }

        for problematic, replacement in problematic_values.items():
            pattern = rf":\s+{re.escape(problematic)}\s*$"
            if re.search(pattern, line):

                def create_truthy_fix(old_val: str, new_val: str):
                    return lambda l: re.sub(rf":\s+{re.escape(old_val)}\s*$", f": {new_val}", l)

                report.add_issue(
                    LintIssue(
                        line=line_num,
                        message=f"Truthy value '{problematic}' should be '{replacement}' for clarity",
                        code="YML030",
                        severity=IssueSeverity.STYLE,
                        fix=create_truthy_fix(problematic, replacement),
                        fixable=True,
                    )
                )

    def _check_document_issues(self, report: FileReport, content: str, lines: list[str]) -> None:
        """Check document-level issues."""
        # Check for document start marker
        if self.config["enforce_document_start"] and not content.startswith("---"):
            report.add_issue(
                LintIssue(
                    line=1,
                    message="Document should start with '---'",
                    code="YML040",
                    severity=IssueSeverity.STYLE,
                    fix=lambda l: "---\n" + l if l.strip() else "---\n",
                    fixable=True,
                )
            )

        # Check for document end marker
        if self.config["enforce_document_end"] and not content.rstrip().endswith("..."):
            report.add_issue(
                LintIssue(
                    line=len(lines),
                    message="Document should end with '...'",
                    code="YML041",
                    severity=IssueSeverity.STYLE,
                    fix=lambda l: l.rstrip() + "\n...\n",
                    fixable=True,
                )
            )

        # Check for empty values (but be smart about workflow files)
        if self.config["check_empty_values"]:
            is_workflow = "workflow" in str(report.path).lower() or ".github" in str(report.path)
            is_compose = (
                "docker-compose" in str(report.path).lower()
                or "compose" in str(report.path).lower()
            )

            empty_value_pattern = r"^\s*\w+:\s*$"
            for line_num, line in enumerate(lines, 1):
                if re.match(empty_value_pattern, line):
                    # Skip common workflow/compose patterns that are intentionally empty
                    line_content = line.strip()
                    should_skip = False

                    if is_workflow:
                        # Check if it's a GitHub Actions structural keyword
                        workflow_keywords = [
                            # Top-level workflow structure
                            "on:",
                            "jobs:",
                            "env:",
                            "defaults:",
                            "concurrency:",
                            "permissions:",
                            # Job-level structure
                            "steps:",
                            "outputs:",
                            "strategy:",
                            "matrix:",
                            "include:",
                            "exclude:",
                            "services:",
                            "container:",
                            "continue-on-error:",
                            "timeout-minutes:",
                            # Event triggers
                            "push:",
                            "pull_request:",
                            "workflow_dispatch:",
                            "schedule:",
                            "release:",
                            "issues:",
                            "issue_comment:",
                            "pull_request_target:",
                            # Inputs and outputs
                            "inputs:",
                            "outputs:",
                            "secrets:",
                            "with:",
                            "options:",
                            # Service configurations
                            "ports:",
                            "volumes:",
                            "env:",
                            "credentials:",
                            "image:",
                            # Step configurations
                            "uses:",
                            "run:",
                            "shell:",
                            "working-directory:",
                            "if:",
                            "needs:",
                        ]
                        if any(line_content == keyword for keyword in workflow_keywords):
                            should_skip = True

                        # Check for workflow structural patterns based on context
                        if not should_skip and line_num > 1:
                            prev_lines = lines[: line_num - 1]
                            current_indent = len(line) - len(line.lstrip())

                            # Look back to determine context - find the most specific/recent context
                            context_section = None

                            # Look backwards to find the immediate context for this line
                            for i in range(line_num - 2, max(-1, line_num - 100), -1):
                                prev_line = prev_lines[i].strip()
                                prev_indent = len(prev_lines[i]) - len(prev_lines[i].lstrip())

                                # Skip empty lines and comments as they don't provide structural context
                                if not prev_line or prev_line.startswith("#"):
                                    continue

                                # Stop when we hit a section that's at a higher level than current line
                                if prev_indent < current_indent:
                                    # Check if this is a section we care about
                                    if prev_line == "services:" and prev_indent >= 4:
                                        context_section = "services:"
                                        break
                                    if prev_line == "inputs:" and prev_indent == 4:
                                        context_section = "inputs:"
                                        break
                                    if prev_line == "jobs:" and prev_indent == 0:
                                        context_section = "jobs:"
                                        break

                            # Skip based on context and indentation patterns
                            if context_section == "jobs:" and current_indent == 2:
                                # Job names under jobs: section (2-space indent)
                                should_skip = True
                            elif context_section == "services:":
                                # Service names - can be at various indents depending on nesting
                                if current_indent in {6, 4}:
                                    should_skip = True
                            elif context_section == "inputs:" and current_indent >= 4:
                                # Input parameter names
                                should_skip = True
                            elif line_content == "environment:" and current_indent >= 4:
                                # Environment configurations anywhere
                                should_skip = True

                            # Comprehensive job name detection: in workflow files, any indent=2 key that looks like a job name
                            # and has a jobs: section above should be considered a job name
                            if (
                                not should_skip
                                and current_indent == 2
                                and re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*:$", line_content)
                            ):
                                # Search extensively for jobs: section - it should be at line 26
                                jobs_found_above = False
                                for i in range(line_num - 1):
                                    if prev_lines[i].strip() == "jobs:":
                                        jobs_found_above = True
                                        break
                                if jobs_found_above:
                                    should_skip = True
                    if not should_skip and is_compose:
                        # Docker-compose patterns that are structure containers
                        compose_keywords = [
                            "services:",
                            "volumes:",
                            "networks:",
                            "configs:",
                            "secrets:",
                            "environment:",
                            "ports:",
                            "depends_on:",
                            "command:",
                            "entrypoint:",
                            "labels:",
                            "expose:",
                            "external_links:",
                            "extra_hosts:",
                            "healthcheck:",
                            "deploy:",
                            "restart:",
                            "stdin_open:",
                            "tty:",
                            "working_dir:",
                            "user:",
                            "domainname:",
                            "hostname:",
                            "ipc:",
                            "mac_address:",
                            "privileged:",
                            "read_only:",
                            "shm_size:",
                            "stop_grace_period:",
                            "stop_signal:",
                            "sysctls:",
                            "ulimits:",
                        ]
                        if any(line_content == keyword for keyword in compose_keywords):
                            should_skip = True

                    # Report empty value if no pattern matched
                    if not should_skip:
                        report.add_issue(
                            LintIssue(
                                line=line_num,
                                message="Empty value, consider using 'null' or removing the key",
                                code="YML050",
                                severity=IssueSeverity.WARNING,
                                fix=lambda l: re.sub(r"^(\s*\w+:)\s*$", r"\1 null", l),
                                fixable=True,
                            )
                        )

    def _get_line_length_fix(self, line: str) -> Callable[[str], str] | None:
        """Determine if and how to fix a long line."""
        stripped = line.strip()

        # Don't auto-fix certain types of lines
        if stripped.startswith(("#", "- ")) or "http" in stripped:  # List items (complex)
            return None

        # Can fix simple key-value pairs
        if ":" in stripped and not any(char in stripped for char in "[]{},"):
            return self._wrap_yaml_line

        return None

    def _wrap_yaml_line(self, line: str) -> str:
        """Wrap a YAML line intelligently."""
        max_length = self.config["max_line_length"]
        if len(line.rstrip()) <= max_length:
            return line

        # Preserve leading whitespace
        leading_space = len(line) - len(line.lstrip())
        indent = line[:leading_space]
        content = line[leading_space:].rstrip()

        # For key-value pairs, try to break at reasonable points
        if ":" in content:
            key_part, value_part = content.split(":", 1)
            key_part = key_part.strip()
            value_part = value_part.strip()

            # If the value is long, try to put it on the next line
            if len(key_part) + len(value_part) + 2 > max_length - leading_space:
                return f"{indent}{key_part}:\n{indent}  {value_part}\n"

        return line  # Can't fix safely

    def _apply_fixes(self, content: str, issues: list[LintIssue]) -> list[str]:
        """Apply all fixes to the content and return the fixed lines."""
        lines = content.splitlines(keepends=True)

        # Sort issues by line number (descending) to avoid offset issues
        sorted_issues = sorted(
            [i for i in issues if i.fixable and i.line > 0], key=lambda x: x.line, reverse=True
        )

        # Apply fixes from bottom to top
        for issue in sorted_issues:
            if issue.fix and 0 < issue.line <= len(lines):
                line_idx = issue.line - 1
                lines[line_idx] = issue.fix(lines[line_idx])

        # Handle file-level fixes (line 0 or document-wide)
        for issue in issues:
            if issue.fix and issue.line <= 1 and issue.code == "YML040":  # Document start
                if lines and not "".join(lines).startswith("---"):
                    lines.insert(0, "---\n")

        return lines

    def check_directory(
        self, directory: str | Path, exclude: list[str] | None = None
    ) -> dict[Path, FileReport]:
        """Check all YAML files in a directory."""
        directory = Path(directory).resolve()
        exclude = exclude or []

        # Find all YAML files
        yaml_files = []
        for pattern in ["**/*.yml", "**/*.yaml"]:
            yaml_files.extend(directory.glob(pattern))

        # Filter out excluded files
        filtered_files = []
        for file_path in yaml_files:
            should_exclude = False
            for exclude_pattern in exclude:
                if exclude_pattern in str(file_path):
                    should_exclude = True
                    break
            if not should_exclude:
                filtered_files.append(file_path)

        # Check each file
        for file_path in filtered_files:
            self.check_file(file_path)

        return self.reports

    def fix_files(self, dry_run: bool = False) -> int:
        """Apply all fixes to files with issues."""
        fixed_count = 0

        for file_path, report in self.reports.items():
            if not report.has_fixable_issues:
                continue

            if dry_run:
                continue

            if report.fixed_content is not None:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.writelines(report.fixed_content)
                    fixed_count += 1
                except Exception:
                    pass

        return fixed_count
