"""Core markdown linter implementation."""

import operator
import re
from collections.abc import Callable
from pathlib import Path

try:
    from .models import FileReport, IssueSeverity, LintIssue
except ImportError:
    from models import FileReport, IssueSeverity, LintIssue


class MarkdownLinter:
    """Markdown linter and fixer."""

    # Default configuration
    DEFAULT_CONFIG = {
        "max_line_length": 120,
        "require_blank_line_before_heading": True,
        "require_blank_line_after_heading": True,
        "allow_multiple_blank_lines": False,
        "trim_trailing_whitespace": True,
        "end_of_line": "lf",  # 'lf' or 'crlf'
        "insert_final_newline": True,
        "check_markdownlint": True,
        "check_common_mistakes": True,
        "check_blank_lines_around_headings": True,  # MD022
        "check_blank_lines_around_lists": True,  # MD032
        "check_ordered_list_numbering": True,  # MD029
        "check_fenced_code_blocks": True,  # MD031, MD040
        "check_duplicate_headings": True,  # MD024
        "check_bare_urls": True,  # MD034
    }

    # Common markdown patterns
    HEADING_PATTERN = re.compile(r"^(?P<level>#{1,6})\s+(?P<content>.+)$")
    CODE_BLOCK_PATTERN = re.compile(r"^```[\w\-]*$")
    CODE_BLOCK_START_PATTERN = re.compile(r"^```(?P<language>[\w\-]*)$")
    HTML_COMMENT_PATTERN = re.compile(r"^<!--.*?-->\s*$")
    LIST_ITEM_PATTERN = re.compile(r"^\s*([*+-]|\d+\.)\s+")
    ORDERED_LIST_PATTERN = re.compile(r"^\s*(?P<number>\d+)\.(?P<content>\s+.*)$")
    UNORDERED_LIST_PATTERN = re.compile(r"^\s*[*+-]\s+")
    BLANK_LINE_PATTERN = re.compile(r"^\s*$")
    BARE_URL_PATTERN = re.compile(r"(?<![<\[\(])(https?://[^\s<>\[\]()]+)(?![>\]\)])")
    EMAIL_PATTERN = re.compile(
        r"(?<![<\[\(])([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?![>\]\)])"
    )
    CLOSED_ATX_HEADING_PATTERN = re.compile(r"^#+\s+.*\s+#+\s*$")

    def __init__(self, config: dict | None = None):
        """Initialize the linter with the given configuration."""
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.reports: dict[Path, FileReport] = {}

    def check_file(self, file_path: str | Path) -> FileReport:
        """Check a single markdown file for issues."""
        file_path = Path(file_path)
        report = FileReport(file_path)
        self.reports[file_path] = report

        try:
            # Read file content
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines(keepends=False)

            # Initialize state
            in_code_block = False
            in_html_comment = False
            in_list = False
            prev_line = ""
            prev_line_blank = True  # Start as if previous line was blank
            current_list_type = None  # 'ordered' or 'unordered'
            expected_ordered_number = 1
            list_start_line = 0
            seen_headings = set()  # Track headings for MD024
            code_block_start_line = 0  # Track code block start for MD031

            # Process each line
            for i, line in enumerate(lines, 1):
                is_blank = self.BLANK_LINE_PATTERN.match(line)

                # Skip empty lines for most checks, but track them
                if is_blank:
                    prev_line = line
                    prev_line_blank = True
                    # Check if we're ending a list
                    if in_list and current_list_type:
                        self._check_list_end_spacing(report, i - 1, lines, list_start_line)
                        in_list = False
                        current_list_type = None
                        expected_ordered_number = 1
                    continue

                # Check for code blocks
                code_block_match = self.CODE_BLOCK_START_PATTERN.match(line)
                if code_block_match:
                    if not in_code_block:
                        # Starting a code block
                        code_block_start_line = i
                        if self.config["check_fenced_code_blocks"]:
                            self._check_fenced_code_block_start(
                                report, i, lines, prev_line_blank, code_block_match
                            )
                    # Ending a code block
                    elif self.config["check_fenced_code_blocks"]:
                        self._check_fenced_code_block_end(report, i, lines, code_block_start_line)

                    in_code_block = not in_code_block
                    prev_line = line
                    prev_line_blank = False
                    continue

                # Skip code blocks and HTML comments
                if in_code_block or in_html_comment:
                    prev_line = line
                    prev_line_blank = False
                    continue

                # Check for HTML comments
                if self.HTML_COMMENT_PATTERN.match(line):
                    in_html_comment = False  # Single line comment
                    prev_line = line
                    prev_line_blank = False
                    continue

                # Check line length
                self._check_line_length(report, i, line)

                # Check for trailing whitespace
                if self.config["trim_trailing_whitespace"] and line.rstrip() != line:
                    self._add_issue(
                        report, i, "Trim trailing whitespace", "MD009", fix=lambda l: l.rstrip()
                    )

                # Check for consistent line endings
                if "\r\n" in line:
                    self._add_issue(
                        report,
                        i,
                        "Inconsistent line endings (CRLF)",
                        "MD001",
                        fix=lambda l: l.replace("\r\n", "\n"),
                    )

                # Check headings
                heading_match = self.HEADING_PATTERN.match(line)
                if heading_match:
                    self._check_heading(report, i, line, heading_match)
                    # MD022: Check blank lines around headings
                    if self.config["check_blank_lines_around_headings"]:
                        self._check_heading_spacing(report, i, lines, prev_line_blank)
                    # MD024: Check for duplicate headings
                    if self.config["check_duplicate_headings"]:
                        self._check_duplicate_headings(report, i, heading_match, seen_headings)

                # Check list items
                list_match = self.LIST_ITEM_PATTERN.match(line)
                ordered_match = self.ORDERED_LIST_PATTERN.match(line)
                unordered_match = self.UNORDERED_LIST_PATTERN.match(line)

                if list_match:
                    self._check_list_item(report, i, line, list_match)

                    # MD032: Check blank lines around lists
                    if self.config["check_blank_lines_around_lists"]:
                        if not in_list:
                            self._check_list_start_spacing(report, i, prev_line_blank)
                            list_start_line = i
                        in_list = True

                    # MD029: Check ordered list numbering
                    if ordered_match and self.config["check_ordered_list_numbering"]:
                        number = int(ordered_match.group("number"))
                        if current_list_type != "ordered":
                            current_list_type = "ordered"
                            expected_ordered_number = 1
                        self._check_ordered_list_numbering(
                            report, i, line, number, expected_ordered_number
                        )
                        expected_ordered_number += (
                            1  # Always increment by 1 regardless of actual number
                        )
                    elif unordered_match:
                        if current_list_type != "unordered":
                            current_list_type = "unordered"
                            expected_ordered_number = 1
                elif in_list and current_list_type:
                    # We're no longer in a list
                    self._check_list_end_spacing(report, i - 1, lines, list_start_line)
                    in_list = False
                    current_list_type = None
                    expected_ordered_number = 1

                # Check for common markdown mistakes
                if self.config["check_common_mistakes"]:
                    self._check_common_mistakes(report, i, line, prev_line)

                prev_line = line
                prev_line_blank = False

            # Check for final newline
            if self.config["insert_final_newline"] and content and not content.endswith("\n"):
                self._add_issue(
                    report,
                    len(lines),
                    "Missing final newline",
                    "MD047",
                    fix=lambda c: c + "\n",
                    file_level=True,
                )

            # Store the fixed content if there are fixes
            if any(issue.fixable for issue in report.issues):
                report.fixed_content = self._apply_fixes(content, report.issues)

        except Exception as e:
            self._add_issue(
                report, 0, f"Error processing file: {e!s}", "ERROR", severity=IssueSeverity.ERROR
            )

        return report

    def _check_line_length(self, report: FileReport, line_num: int, line: str) -> None:
        """Check if the line exceeds the maximum allowed length."""
        max_length = self.config["max_line_length"]
        if len(line) > max_length:
            # Try to determine if we can auto-fix this line
            fix_func = self._get_line_length_fix(line, max_length)
            self._add_issue(
                report,
                line_num,
                f"Line too long ({len(line)} > {max_length} characters)",
                "MD013",
                fix=fix_func,
            )

    def _get_line_length_fix(self, line: str, max_length: int) -> Callable[[str], str] | None:
        """Determine if and how to fix a long line."""
        stripped = line.strip()

        # Don't auto-fix code blocks, tables, or very complex structures
        if stripped.startswith(("```", "|", "    ")) or "---" in stripped:
            return None

        # Don't auto-fix headings or very short overruns (< 10 chars)
        if stripped.startswith("#") or len(line) - max_length < 10:
            return None

        # Auto-fix text paragraphs and list items
        if self._can_wrap_text(stripped):
            return lambda l: self._wrap_text_line(l, max_length)

        return None

    def _can_wrap_text(self, line: str) -> bool:
        """Check if a line can be safely wrapped."""
        stripped = line.strip()
        # Can wrap normal text, list items, and simple markdown
        return (
            not stripped.startswith(">")  # Not blockquote
            and not re.match(r"^\s*\d+\.", stripped)  # Not numbered list (for now)
            and "http" not in stripped  # Not URLs (handle separately)
            and "[" not in stripped
            and "]" not in stripped
        )  # Not complex links

    def _wrap_text_line(self, line: str, max_length: int) -> str:
        """Wrap a text line at word boundaries."""
        if len(line) <= max_length:
            return line

        # Preserve leading whitespace
        leading_space = len(line) - len(line.lstrip())
        indent = line[:leading_space]
        content = line[leading_space:]

        # Find the best break point
        break_point = max_length - leading_space
        if break_point >= len(content):
            return line

        # Find word boundary before break point
        space_before = content.rfind(" ", 0, break_point)
        if space_before > break_point // 2:  # Reasonable break point found
            return indent + content[:space_before] + "\n" + indent + content[space_before:].lstrip()

        return line  # Can't find good break point

    def _check_heading(self, report: FileReport, line_num: int, line: str, match: re.Match) -> None:
        """Check heading formatting and spacing."""
        level = len(match.group("level"))
        content = match.group("content")

        # Check for space after heading markers
        if not line.startswith(f"{'#' * level} "):
            self._add_issue(
                report,
                line_num,
                "Missing space after heading marker",
                "MD018",
                fix=lambda l: f"{'#' * level} {l.lstrip('#').lstrip()}",
            )

        # Check for trailing hashes
        if " #" in content:
            self._add_issue(
                report,
                line_num,
                "Remove trailing hash characters from heading",
                "MD026",
                fix=lambda l: l.split(" #")[0].rstrip(),
            )

        # Check for proper capitalization (first word only)
        if content and content[0].islower() and content[0].isalpha():
            self._add_issue(
                report,
                line_num,
                "First word in heading should be capitalized",
                "MD002",
                fix=lambda l: re.sub(
                    r"^(#+\s*)([a-z])", lambda m: m.group(1) + m.group(2).upper(), l
                ),
            )

    def _check_heading_spacing(
        self, report: FileReport, line_num: int, lines: list[str], prev_line_blank: bool
    ) -> None:
        """Check MD022: Headings should be surrounded by blank lines."""
        # Check if previous line is blank (unless it's the first line)
        if line_num > 1 and not prev_line_blank:
            self._add_issue(
                report,
                line_num,
                "Headings should be surrounded by blank lines",
                "MD022",
                severity=IssueSeverity.WARNING,
                fix=lambda content: content,  # Handled by _apply_spacing_fixes
            )

        # Check if next line is blank (unless it's the last line)
        if line_num < len(lines):
            next_line = lines[line_num] if line_num < len(lines) else ""
            if next_line.strip() and not self.BLANK_LINE_PATTERN.match(next_line):
                self._add_issue(
                    report,
                    line_num,
                    "Headings should be surrounded by blank lines",
                    "MD022",
                    severity=IssueSeverity.WARNING,
                    fix=lambda content: content,  # Handled by _apply_spacing_fixes
                )

    def _check_list_start_spacing(
        self, report: FileReport, line_num: int, prev_line_blank: bool
    ) -> None:
        """Check MD032: Lists should be surrounded by blank lines (start)."""
        if line_num > 1 and not prev_line_blank:
            self._add_issue(
                report,
                line_num,
                "Lists should be surrounded by blank lines (start)",
                "MD032",
                severity=IssueSeverity.WARNING,
                fix=lambda content: content,  # Handled by _apply_spacing_fixes
            )

    def _check_list_end_spacing(
        self, report: FileReport, last_list_line: int, lines: list[str], list_start_line: int
    ) -> None:
        """Check MD032: Lists should be surrounded by blank lines (end)."""
        # Check if there's a line after the list and it's not blank
        if last_list_line < len(lines):
            next_line_idx = last_list_line  # 0-based index
            if next_line_idx < len(lines):
                next_line = lines[next_line_idx]
                if next_line.strip() and not self.BLANK_LINE_PATTERN.match(next_line):
                    # Make sure the next line is not another list item
                    if not self.LIST_ITEM_PATTERN.match(next_line):
                        self._add_issue(
                            report,
                            last_list_line + 1,
                            "Lists should be surrounded by blank lines (end)",
                            "MD032",
                            severity=IssueSeverity.WARNING,
                            fix=lambda content: content,  # Handled by _apply_spacing_fixes
                        )

    def _check_ordered_list_numbering(
        self, report: FileReport, line_num: int, line: str, actual_number: int, expected_number: int
    ) -> None:
        """Check MD029: Ordered list item prefix should be sequential."""
        if actual_number != expected_number:
            # Create a fix function that captures the correct expected number
            def fix_ordered_number(line_content, expected=expected_number):
                # Preserve the original indentation
                match = re.match(r"^(\s*)\d+\.(.*)$", line_content)
                if match:
                    indent, rest = match.groups()
                    return f"{indent}{expected}.{rest}"
                return line_content

            # Create a closure to capture the expected number
            def fix_func(content):
                return fix_ordered_number(content, expected_number)

            self._add_issue(
                report,
                line_num,
                f"Ordered list item prefix [Expected: {expected_number}; Actual: {actual_number}]",
                "MD029",
                severity=IssueSeverity.WARNING,
                fix=fix_func,
            )

    def _check_fenced_code_block_start(
        self,
        report: FileReport,
        line_num: int,
        lines: list[str],
        prev_line_blank: bool,
        match: re.Match,
    ) -> None:
        """Check MD031 and MD040 for fenced code block start."""
        # MD031: Check blank line before code block
        if line_num > 1 and not prev_line_blank:
            self._add_issue(
                report,
                line_num,
                "Fenced code blocks should be surrounded by blank lines",
                "MD031",
                severity=IssueSeverity.WARNING,
                fix=lambda content: content,  # Handled by _apply_spacing_fixes
            )

        # MD040: Check if language is specified
        language = match.group("language") if match else ""
        if not language.strip():

            def add_language_fix(line_content):
                return line_content.replace("```", "```text")

            self._add_issue(
                report,
                line_num,
                "Fenced code blocks should have a language specified",
                "MD040",
                severity=IssueSeverity.WARNING,
                fix=add_language_fix,
            )

    def _check_fenced_code_block_end(
        self, report: FileReport, line_num: int, lines: list[str], code_block_start_line: int
    ) -> None:
        """Check MD031 for fenced code block end."""
        # MD031: Check blank line after code block
        if line_num < len(lines):
            next_line_idx = line_num  # 0-based index for next line
            if next_line_idx < len(lines):
                next_line = lines[next_line_idx]
                if next_line.strip() and not self.BLANK_LINE_PATTERN.match(next_line):
                    self._add_issue(
                        report,
                        line_num + 1,
                        "Fenced code blocks should be surrounded by blank lines",
                        "MD031",
                        severity=IssueSeverity.WARNING,
                        fix=lambda content: content,  # Handled by _apply_spacing_fixes
                    )

    def _check_duplicate_headings(
        self, report: FileReport, line_num: int, match: re.Match, seen_headings: set
    ) -> None:
        """Check MD024: Multiple headings with the same content."""
        heading_text = match.group("content").strip().lower()
        original_heading = match.group("content").strip()

        if heading_text in seen_headings:
            # Find the next available number for this heading
            counter = 2
            while f"{heading_text} {counter}" in seen_headings:
                counter += 1

            new_heading_text = f"{heading_text} {counter}"
            new_heading_display = f"{original_heading} {counter}"

            def fix_duplicate_heading(line_content):
                level = match.group("level")
                return line_content.replace(
                    f"{level} {original_heading}", f"{level} {new_heading_display}"
                )

            self._add_issue(
                report,
                line_num,
                f"Multiple headings with the same content (auto-numbering to '{new_heading_display}')",
                "MD024",
                severity=IssueSeverity.WARNING,
                fix=fix_duplicate_heading,
            )

            # Add the new numbered heading to seen_headings
            seen_headings.add(new_heading_text)
        else:
            seen_headings.add(heading_text)

    def _get_url_title(self, url: str) -> str:
        """Get a title for a URL using AI or web scraping."""
        try:
            import re as regex_module

            import requests

            # Try to fetch the page title
            response = requests.get(
                url,
                timeout=5,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            response.raise_for_status()

            # Extract title from HTML
            title_match = regex_module.search(
                r"<title[^>]*>([^<]+)</title>", response.text, regex_module.IGNORECASE
            )
            if title_match:
                title = title_match.group(1).strip()
                # Clean up the title
                title = regex_module.sub(r"\s+", " ", title)
                if len(title) > 100:
                    title = title[:97] + "..."
                return title

        except Exception:
            pass

        # Fallback: Generate a simple title from the URL
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            path_parts = [p for p in parsed.path.split("/") if p]

            if path_parts:
                # Use the last meaningful path component
                last_part = path_parts[-1]
                if "." in last_part:
                    last_part = last_part.split(".")[0]
                title = last_part.replace("-", " ").replace("_", " ").title()
                return f"{title} - {domain}"
            return domain.title()

        except Exception:
            # Final fallback
            return "Link"

    def _check_list_item(
        self, report: FileReport, line_num: int, line: str, match: re.Match
    ) -> None:
        """Check list item formatting and indentation."""
        # Check for proper indentation (2 or 4 spaces)
        indent = len(line) - len(line.lstrip())
        if indent % 2 != 0 and indent > 0:
            self._add_issue(
                report,
                line_num,
                "List items should be indented with multiples of 2 spaces",
                "MD007",
                fix=lambda l: " " * (indent + 1) + l.lstrip(),
            )

    def _check_common_mistakes(
        self, report: FileReport, line_num: int, line: str, prev_line: str
    ) -> None:
        """Check for common markdown mistakes."""
        if self.config["check_bare_urls"]:
            # Check for bare URLs
            if "http://" in line or "https://" in line:
                matches = re.finditer(self.BARE_URL_PATTERN, line)
                for match in matches:
                    url = match.group(1)
                    # Make sure it's not part of a markdown link [text](url)
                    start_pos = match.start()
                    if (
                        start_pos > 0
                        and line[start_pos - 1 : start_pos + 2] != "]("
                        and line[start_pos - 1] != "]"
                    ):
                        # Create a fix function that fetches a proper title and creates a markdown link
                        def create_url_fix(url_to_fix):
                            def fix_url(line_content):
                                title = self._get_url_title(url_to_fix)
                                return line_content.replace(url_to_fix, f"[{title}]({url_to_fix})")

                            return fix_url

                        self._add_issue(
                            report,
                            line_num,
                            "Bare URL used, converting to markdown link with title",
                            "MD034",
                            fix=create_url_fix(url),
                        )

            # Check for bare email addresses
            if "@" in line:
                matches = re.finditer(self.EMAIL_PATTERN, line)
                for match in matches:
                    email = match.group(1)
                    # Make sure it's not already in a markdown link or angle brackets
                    start_pos = match.start(1)  # Use group 1 start position
                    if start_pos == 0 or (
                        line[start_pos - 1] not in "<[]("
                        and not (start_pos > 1 and line[start_pos - 2 : start_pos] == "](")
                    ):
                        # Create a fix function for email addresses
                        def create_email_fix(email_to_fix):
                            def fix_email(line_content):
                                # Use word boundaries to ensure exact match
                                pattern = r"\b" + re.escape(email_to_fix) + r"\b"
                                return re.sub(pattern, f"<{email_to_fix}>", line_content)

                            return fix_email

                        self._add_issue(
                            report,
                            line_num,
                            "Bare email address used, converting to angle bracket format",
                            "MD034",
                            fix=create_email_fix(email),
                        )

        # Check for multiple spaces after list markers
        if re.match(r"^\s*[*+-]\s{2,}\S", line):
            self._add_issue(
                report,
                line_num,
                "Use a single space after list markers",
                "MD030",
                fix=lambda l: re.sub(r"^([*+-])\s+", r"\1 ", l),
            )

    def _add_issue(
        self,
        report: FileReport,
        line_num: int,
        message: str,
        code: str,
        fix: Callable[[str], str] | None = None,
        severity: IssueSeverity = IssueSeverity.WARNING,
        file_level: bool = False,
    ) -> None:
        """Add an issue to the report."""
        issue = LintIssue(
            line=line_num if not file_level else 0,
            message=message,
            code=code,
            severity=severity,
            fixable=fix is not None,
            fix=fix,
        )
        report.add_issue(issue)

    def _apply_fixes(self, content: str, issues: list[LintIssue]) -> list[str]:
        """Apply all fixes to the content and return the fixed lines."""
        lines = content.splitlines(keepends=False)

        # Separate different types of fixes
        line_fixes = [
            i
            for i in issues
            if i.fixable and i.line > 0 and i.code not in {"MD022", "MD032", "MD031"}
        ]
        spacing_fixes = [i for i in issues if i.fixable and i.code in {"MD022", "MD032", "MD031"}]
        file_fixes = [i for i in issues if i.fixable and i.line == 0]

        # Apply line-level fixes first (sort descending to avoid offset issues)
        sorted_line_fixes = sorted(line_fixes, key=lambda x: x.line, reverse=True)
        for issue in sorted_line_fixes:
            if issue.fix and 0 < issue.line <= len(lines):
                line_idx = issue.line - 1
                lines[line_idx] = issue.fix(lines[line_idx])

        # Apply spacing fixes (requires more complex handling)
        lines = self._apply_spacing_fixes(lines, spacing_fixes)

        # Handle file-level fixes
        for issue in file_fixes:
            if issue.fix:
                # Apply to the entire content
                fixed_content = issue.fix("\n".join(lines))
                lines = fixed_content.splitlines(keepends=False)

        # Ensure lines end with newlines (except the last one which will be handled by file write)
        return [line + "\n" if not line.endswith("\n") else line for line in lines]

    def _apply_spacing_fixes(self, lines: list[str], spacing_issues: list[LintIssue]) -> list[str]:
        """Apply MD022, MD032, and MD031 spacing fixes by inserting blank lines."""
        # Collect all blank line insertions needed
        insertions = []  # List of (line_index, position) tuples

        for issue in spacing_issues:
            line_num = issue.line
            line_idx = line_num - 1  # Convert to 0-based index

            if issue.code == "MD022":  # Heading spacing
                # For headings, we need to check context to determine if before/after
                if line_idx > 0 and line_idx - 1 < len(lines):
                    prev_line = lines[line_idx - 1]
                    if prev_line.strip():  # Previous line is not blank
                        insertions.append((line_idx, "before"))

                if line_idx + 1 < len(lines):
                    next_line = lines[line_idx + 1]
                    if next_line.strip() and not self.BLANK_LINE_PATTERN.match(next_line):
                        insertions.append((line_idx + 1, "before"))  # Insert before next line

            elif issue.code == "MD032":  # List spacing
                if "(start)" in issue.message:
                    # Add blank line before the list
                    insertions.append((line_idx, "before"))
                elif "(end)" in issue.message:
                    # Add blank line after the list (before the next content)
                    insertions.append((line_idx, "before"))  # Insert before the non-list line

            elif issue.code == "MD031":  # Fenced code block spacing
                if "Fenced code blocks should be surrounded by blank lines" in issue.message:
                    # Check if this is a start or end of code block
                    if line_idx < len(lines) and lines[line_idx].strip().startswith("```"):
                        # Check if previous line needs spacing (start of code block)
                        if line_idx > 0 and lines[line_idx - 1].strip():
                            insertions.append((line_idx, "before"))
                        # Check if next line needs spacing (end of code block)
                        if line_idx + 1 < len(lines) and lines[line_idx + 1].strip():
                            insertions.append((line_idx + 1, "before"))

        # Sort insertions by line index in descending order to avoid offset issues
        insertions.sort(key=operator.itemgetter(0), reverse=True)

        # Remove duplicates
        seen = set()
        unique_insertions = []
        for insertion in insertions:
            if insertion not in seen:
                seen.add(insertion)
                unique_insertions.append(insertion)

        # Apply insertions
        new_lines = lines.copy()
        for line_idx, position in unique_insertions:
            if position == "before" and 0 <= line_idx <= len(new_lines):
                # Insert blank line before the specified line
                new_lines.insert(line_idx, "")

        return new_lines

    def check_directory(
        self, directory: str | Path, exclude: list[str] | None = None
    ) -> dict[Path, FileReport]:
        """Check all markdown files in a directory."""
        from tools.find_markdown_files import find_markdown_files

        directory = Path(directory).resolve()
        exclude = exclude or []

        # Find all markdown files
        files = find_markdown_files(
            directory,
            exclude_dirs={".git", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache"},
            exclude_files=exclude,
        )

        # Check each file
        for file_path in files:
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
