"""YAML linter and auto-fixer package.

A comprehensive YAML linter with intelligent auto-fixing capabilities
for formatting, style, and common issues.

Example usage:
    try:
    from .yaml_lint import YAMLLinter
except ImportError:
    from yaml_lint import YAMLLinter

    linter = YAMLLinter()
    reports = linter.check_file("config.yml")

    # Apply fixes
    fixed_count = linter.fix_files()
"""

from .linter import YAMLLinter
from .models import FileReport, IssueSeverity, LintIssue

__version__ = "0.1.0"
__all__ = ["FileReport", "IssueSeverity", "LintIssue", "YAMLLinter"]
