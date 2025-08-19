#!/usr/bin/env python3
"""
Ruff Issue Fixer Script

This script helps address the remaining 3,154 Ruff issues by categorizing them
and providing systematic fixes.
"""

from collections import defaultdict
import json
from pathlib import Path
import subprocess


class RuffIssueFixer:
    """Helper class to fix Ruff issues systematically"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.issues_by_category = defaultdict(list)
        self.issues_by_file = defaultdict(list)

    def run_ruff_check(self) -> str:
        """Run ruff check and return output"""
        try:
            result = subprocess.run(
                ["ruff", "check", "--output-format=json"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error running ruff: {e}")
            return ""

    def categorize_issues(self, ruff_output: str):
        """Categorize issues by type and file"""
        try:
            issues = json.loads(ruff_output)
            for issue in issues:
                rule_code = issue.get("code", "")
                file_path = issue.get("filename", "")
                line = issue.get("location", {}).get("row", 0)
                message = issue.get("message", "")

                # Categorize by rule type
                category = self._get_category(rule_code)
                self.issues_by_category[category].append({
                    "file": file_path,
                    "line": line,
                    "code": rule_code,
                    "message": message
                })

                # Group by file
                self.issues_by_file[file_path].append({
                    "line": line,
                    "code": rule_code,
                    "message": message
                })
        except json.JSONDecodeError:
            print("Failed to parse ruff output as JSON")

    def _get_category(self, rule_code: str) -> str:
        """Categorize rule codes into fixable categories"""
        if rule_code.startswith("T201"):  # print statements
            return "print_statements"
        elif rule_code.startswith("PTH"):  # pathlib issues
            return "pathlib_issues"
        elif rule_code.startswith("PLR"):  # complexity issues
            return "complexity_issues"
        elif rule_code.startswith("F"):  # pyflakes issues
            return "pyflakes_issues"
        elif rule_code.startswith("E"):  # pycodestyle issues
            return "pycodestyle_issues"
        elif rule_code.startswith("W"):  # pycodestyle warnings
            return "pycodestyle_warnings"
        elif rule_code.startswith("N"):  # pep8-naming
            return "naming_issues"
        elif rule_code.startswith("S"):  # bandit security
            return "security_issues"
        elif rule_code.startswith("B"):  # flake8-bugbear
            return "bugbear_issues"
        elif rule_code.startswith("SIM"):  # flake8-simplify
            return "simplify_issues"
        elif rule_code.startswith("ARG"):  # flake8-unused-arguments
            return "argument_issues"
        elif rule_code.startswith("TRY"):  # tryceratops
            return "try_except_issues"
        elif rule_code.startswith("ERA"):  # eradicate
            return "commented_code"
        elif rule_code.startswith("FIX"):  # ruff
            return "ruff_fixes"
        elif rule_code.startswith("INP"):  # isort
            return "import_issues"
        elif rule_code.startswith("PGH"):  # pygrep-hooks
            return "pygrep_issues"
        elif rule_code.startswith("PT"):  # flake8-pytest-style
            return "pytest_issues"
        elif rule_code.startswith("SLF"):  # flake8-self
            return "self_issues"
        elif rule_code.startswith("TID"):  # flake8-tidy-imports
            return "import_tidy_issues"
        elif rule_code.startswith("DTZ"):  # flake8-datetimez
            return "datetime_issues"
        elif rule_code.startswith("EM"):  # flake8-errmsg
            return "error_message_issues"
        elif rule_code.startswith("G"):  # flake8-logging-format
            return "logging_issues"
        else:
            return "other_issues"

    def generate_report(self):
        """Generate a report of issues by category"""
        print("=== Ruff Issues Report ===\n")

        total_issues = sum(len(issues) for issues in self.issues_by_category.values())
        print(f"Total Issues: {total_issues}\n")

        # Sort categories by number of issues
        sorted_categories = sorted(
            self.issues_by_category.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        for category, issues in sorted_categories:
            print(f"{category}: {len(issues)} issues")

        print("\n=== Top 10 Files with Most Issues ===\n")

        # Sort files by number of issues
        sorted_files = sorted(
            self.issues_by_file.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        for file_path, issues in sorted_files[:10]:
            print(f"{file_path}: {len(issues)} issues")

    def generate_fix_plan(self):
        """Generate a plan for fixing issues"""
        print("\n=== Fix Plan ===\n")

        # Priority 1: Easy auto-fixable issues
        easy_fixes = [
            "print_statements",
            "pathlib_issues",
            "pycodestyle_issues",
            "pycodestyle_warnings",
            "naming_issues",
            "simplify_issues"
        ]

        print("Priority 1 - Easy Auto-fixes:")
        for category in easy_fixes:
            if category in self.issues_by_category:
                count = len(self.issues_by_category[category])
                print(f"  - {category}: {count} issues")

        # Priority 2: Manual fixes needed
        manual_fixes = [
            "complexity_issues",
            "pyflakes_issues",
            "argument_issues",
            "try_except_issues",
            "import_issues"
        ]

        print("\nPriority 2 - Manual Fixes:")
        for category in manual_fixes:
            if category in self.issues_by_category:
                count = len(self.issues_by_category[category])
                print(f"  - {category}: {count} issues")

        # Priority 3: Security and critical issues
        critical_fixes = [
            "security_issues",
            "bugbear_issues"
        ]

        print("\nPriority 3 - Critical Issues:")
        for category in critical_fixes:
            if category in self.issues_by_category:
                count = len(self.issues_by_category[category])
                print(f"  - {category}: {count} issues")

    def run_auto_fixes(self):
        """Run ruff with auto-fix for fixable issues"""
        print("\n=== Running Auto-fixes ===\n")

        try:
            # Run ruff with --fix for auto-fixable issues
            result = subprocess.run(
                ["ruff", "check", "--fix"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode == 0:
                print("Auto-fixes applied successfully!")
                print(result.stdout)
            else:
                print("Some issues could not be auto-fixed:")
                print(result.stderr)

        except subprocess.CalledProcessError as e:
            print(f"Error running ruff auto-fix: {e}")


def main():
    """Main function"""
    fixer = RuffIssueFixer()

    print("Running Ruff check...")
    ruff_output = fixer.run_ruff_check()

    if ruff_output:
        fixer.categorize_issues(ruff_output)
        fixer.generate_report()
        fixer.generate_fix_plan()

        # Ask user if they want to run auto-fixes
        response = input("\nWould you like to run auto-fixes? (y/n): ")
        if response.lower() == 'y':
            fixer.run_auto_fixes()
    else:
        print("No issues found or error running ruff")


if __name__ == "__main__":
    main()
