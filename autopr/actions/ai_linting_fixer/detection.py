"""
Issue Detection and Parsing Module

Handles detection, parsing, and analysis of linting issues from various tools
including flake8, pylint, mypy, and other Python linting tools.
"""

from dataclasses import dataclass
from enum import Enum
import logging
import operator
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class IssueCategory(Enum):
    """Categories of linting issues for prioritization and handling."""

    CRITICAL = "critical"  # Syntax errors, undefined names
    HIGH = "high"  # Logic errors, unused imports
    MEDIUM = "medium"  # Style violations, long lines
    LOW = "low"  # Minor style issues, docstring format
    INFO = "info"  # Informational messages


class IssueSeverity(Enum):
    """Severity levels for linting issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LintingIssue:
    """Represents a single linting issue with comprehensive metadata."""

    # Basic issue information
    file_path: str
    line_number: int
    column_number: int
    error_code: str
    message: str

    # Extended metadata
    tool: str = "flake8"
    category: IssueCategory = IssueCategory.MEDIUM
    severity: IssueSeverity = IssueSeverity.WARNING
    line_content: str = ""

    # Context information
    function_name: str | None = None
    class_name: str | None = None

    # Fix metadata
    fix_priority: int = 5  # 1-10, higher = more priority
    estimated_confidence: float = 0.7
    requires_human_review: bool = False

    def __str__(self):
        return f"{self.file_path}:{self.line_number}:{self.column_number}: {self.error_code} {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for database storage."""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "error_code": self.error_code,
            "message": self.message,
            "tool": self.tool,
            "category": self.category.value,
            "severity": self.severity.value,
            "line_content": self.line_content,
            "function_name": self.function_name,
            "class_name": self.class_name,
            "fix_priority": self.fix_priority,
            "estimated_confidence": self.estimated_confidence,
            "requires_human_review": self.requires_human_review,
        }


class IssueClassifier:
    """Classifies linting issues into categories and assigns metadata."""

    # Issue classification rules
    ISSUE_CLASSIFICATIONS = {
        # Critical issues
        "F821": (IssueCategory.CRITICAL, IssueSeverity.ERROR, 9),  # Undefined name
        "F822": (IssueCategory.CRITICAL, IssueSeverity.ERROR, 9),  # Undefined name in __all__
        "E999": (IssueCategory.CRITICAL, IssueSeverity.ERROR, 10),  # Syntax error
        # High priority issues
        "F401": (IssueCategory.HIGH, IssueSeverity.WARNING, 8),  # Unused import
        "F811": (IssueCategory.HIGH, IssueSeverity.WARNING, 7),  # Redefined name
        "F841": (IssueCategory.HIGH, IssueSeverity.WARNING, 7),  # Unused variable
        "E722": (IssueCategory.HIGH, IssueSeverity.WARNING, 6),  # Bare except
        "B001": (IssueCategory.HIGH, IssueSeverity.WARNING, 6),  # Bare except
        # Medium priority issues
        "E501": (IssueCategory.MEDIUM, IssueSeverity.WARNING, 6),  # Line too long
        "F541": (IssueCategory.MEDIUM, IssueSeverity.WARNING, 5),  # F-string missing placeholders
        "E741": (IssueCategory.MEDIUM, IssueSeverity.WARNING, 4),  # Ambiguous variable name
        # Low priority issues
        "W293": (IssueCategory.LOW, IssueSeverity.INFO, 3),  # Blank line with whitespace
        "W291": (IssueCategory.LOW, IssueSeverity.INFO, 3),  # Trailing whitespace
        "E302": (IssueCategory.LOW, IssueSeverity.INFO, 2),  # Expected 2 blank lines
        "E303": (IssueCategory.LOW, IssueSeverity.INFO, 2),  # Too many blank lines
        # Documentation issues
        "D100": (IssueCategory.INFO, IssueSeverity.INFO, 1),  # Missing docstring
        "D101": (IssueCategory.INFO, IssueSeverity.INFO, 1),  # Missing docstring
        "D102": (IssueCategory.INFO, IssueSeverity.INFO, 1),  # Missing docstring
    }

    @classmethod
    def classify_issue(cls, error_code: str) -> tuple[IssueCategory, IssueSeverity, int]:
        """Classify an issue by its error code."""
        # Look for exact match first
        if error_code in cls.ISSUE_CLASSIFICATIONS:
            return cls.ISSUE_CLASSIFICATIONS[error_code]

        # Look for prefix match (e.g., E501 matches E5xx patterns)
        for code, classification in cls.ISSUE_CLASSIFICATIONS.items():
            if error_code.startswith(code[:2]):  # Match first 2 characters
                return classification

        # Default classification
        return IssueCategory.MEDIUM, IssueSeverity.WARNING, 5

    @classmethod
    def estimate_fix_confidence(cls, error_code: str) -> float:
        """Estimate confidence for fixing this type of issue."""
        confidence_map = {
            "F401": 0.9,  # Unused imports - very reliable
            "F841": 0.8,  # Unused variables - quite reliable
            "E501": 0.7,  # Line length - moderately reliable
            "E722": 0.6,  # Bare except - somewhat reliable
            "F541": 0.5,  # F-string issues - less reliable
            "E741": 0.4,  # Variable naming - needs human judgment
        }

        # Look for exact or prefix match
        for code, confidence in confidence_map.items():
            if error_code.startswith(code):
                return confidence

        return 0.6  # Default confidence


class Flake8Parser:
    """Parser for flake8 output in various formats."""

    def __init__(self):
        self.classifier = IssueClassifier()

    def run_flake8(self, target_path: str, config_file: str | None = None) -> list[LintingIssue]:
        """Run flake8 and parse the results."""
        try:
            # Build flake8 command
            cmd = ["python", "-m", "flake8", target_path]
            if config_file:
                cmd.extend(["--config", config_file])

            # Run flake8
            result = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=".")

            if result.stdout.strip():
                return self.parse_standard_output(result.stdout)
            return []

        except Exception as e:
            logger.exception(f"Error running flake8: {e}")
            return []

    def parse_standard_output(self, output: str) -> list[LintingIssue]:
        """Parse flake8 standard output format."""
        issues = []

        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            try:
                issue = self._parse_flake8_line(line)
                if issue:
                    issues.append(issue)
            except Exception as e:
                logger.debug(f"Failed to parse flake8 line: {line} - {e}")
                continue

        return issues

    def _parse_flake8_line(self, line: str) -> LintingIssue | None:
        """Parse a single line of flake8 output."""
        # Format: file:line:col: code message
        parts = line.split(":", 3)
        if len(parts) < 4:
            return None

        try:
            file_path = parts[0].strip()
            line_number = int(parts[1].strip())
            column_number = int(parts[2].strip())
            code_message = parts[3].strip()

            # Extract error code and message
            code_parts = code_message.split(" ", 1)
            error_code = code_parts[0]
            message = code_parts[1] if len(code_parts) > 1 else ""

            # Classify the issue
            category, severity, priority = self.classifier.classify_issue(error_code)
            confidence = self.classifier.estimate_fix_confidence(error_code)

            # Get line content if possible
            line_content = self._get_line_content(file_path, line_number)

            # Extract context (function/class names)
            function_name, class_name = self._extract_context(file_path, line_number)

            return LintingIssue(
                file_path=file_path,
                line_number=line_number,
                column_number=column_number,
                error_code=error_code,
                message=message,
                tool="flake8",
                category=category,
                severity=severity,
                line_content=line_content,
                function_name=function_name,
                class_name=class_name,
                fix_priority=priority,
                estimated_confidence=confidence,
                requires_human_review=category == IssueCategory.CRITICAL,
            )

        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to parse flake8 line components: {line} - {e}")
            return None

    def _get_line_content(self, file_path: str, line_number: int) -> str:
        """Get the content of a specific line from a file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
                if 1 <= line_number <= len(lines):
                    return lines[line_number - 1].rstrip("\n\r")
        except Exception as e:
            logger.debug(f"Failed to read line content from {file_path}:{line_number} - {e}")
        return ""

    def _extract_context(self, file_path: str, line_number: int) -> tuple[str | None, str | None]:
        """Extract function and class context for the given line."""
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            function_name = None
            class_name = None

            # Look backwards from the line to find function/class definitions
            for i in range(min(line_number - 1, len(lines)), -1, -1):
                line = lines[i].strip()

                if line.startswith("def ") and function_name is None:
                    # Extract function name
                    try:
                        func_part = line.split("(")[0]
                        function_name = func_part.replace("def ", "").strip()
                    except:
                        pass

                if line.startswith("class ") and class_name is None:
                    # Extract class name
                    try:
                        class_part = line.split("(")[0].split(":")[0]
                        class_name = class_part.replace("class ", "").strip()
                    except:
                        pass

                # Stop if we found both or reached the beginning
                if (function_name and class_name) or i == 0:
                    break

            return function_name, class_name

        except Exception as e:
            logger.debug(f"Failed to extract context from {file_path}:{line_number} - {e}")
            return None, None


class IssueDetector:
    """Main class for detecting and analyzing linting issues."""

    def __init__(self):
        self.flake8_parser = Flake8Parser()
        self.supported_tools = ["flake8"]

    def detect_issues(
        self, target_path: str, tools: list[str] | None = None, config_file: str | None = None
    ) -> list[LintingIssue]:
        """Detect linting issues using specified tools."""
        if tools is None:
            tools = ["flake8"]

        all_issues = []

        for tool in tools:
            if tool == "flake8":
                issues = self.flake8_parser.run_flake8(target_path, config_file)
                all_issues.extend(issues)
            else:
                logger.warning(f"Unsupported tool: {tool}")

        return all_issues

    def filter_issues(
        self,
        issues: list[LintingIssue],
        categories: list[IssueCategory] | None = None,
        severities: list[IssueSeverity] | None = None,
        error_codes: list[str] | None = None,
        min_priority: int = 1,
    ) -> list[LintingIssue]:
        """Filter issues based on various criteria."""
        filtered = issues

        if categories:
            filtered = [issue for issue in filtered if issue.category in categories]

        if severities:
            filtered = [issue for issue in filtered if issue.severity in severities]

        if error_codes:
            filtered = [
                issue
                for issue in filtered
                if any(issue.error_code.startswith(code) for code in error_codes)
            ]

        if min_priority > 1:
            filtered = [issue for issue in filtered if issue.fix_priority >= min_priority]

        return filtered

    def group_issues_by_file(self, issues: list[LintingIssue]) -> dict[str, list[LintingIssue]]:
        """Group issues by file path."""
        grouped = {}
        for issue in issues:
            if issue.file_path not in grouped:
                grouped[issue.file_path] = []
            grouped[issue.file_path].append(issue)
        return grouped

    def get_issue_statistics(self, issues: list[LintingIssue]) -> dict[str, Any]:
        """Get comprehensive statistics about detected issues."""
        if not issues:
            return {}

        # Count by category
        category_counts = {}
        for category in IssueCategory:
            category_counts[category.value] = sum(
                1 for issue in issues if issue.category == category
            )

        # Count by severity
        severity_counts = {}
        for severity in IssueSeverity:
            severity_counts[severity.value] = sum(
                1 for issue in issues if issue.severity == severity
            )

        # Count by error code
        error_code_counts = {}
        for issue in issues:
            error_code_counts[issue.error_code] = error_code_counts.get(issue.error_code, 0) + 1

        # File statistics
        files_affected = len({issue.file_path for issue in issues})

        # Priority statistics
        avg_priority = sum(issue.fix_priority for issue in issues) / len(issues)
        high_priority_count = sum(1 for issue in issues if issue.fix_priority >= 7)

        return {
            "total_issues": len(issues),
            "files_affected": files_affected,
            "category_breakdown": category_counts,
            "severity_breakdown": severity_counts,
            "error_code_breakdown": dict(
                sorted(error_code_counts.items(), key=operator.itemgetter(1), reverse=True)
            ),
            "average_priority": round(avg_priority, 2),
            "high_priority_issues": high_priority_count,
            "estimated_fix_confidence": round(
                sum(issue.estimated_confidence for issue in issues) / len(issues), 2
            ),
            "requires_human_review": sum(1 for issue in issues if issue.requires_human_review),
        }


# Global detector instance
issue_detector = IssueDetector()
