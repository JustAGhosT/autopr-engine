"""
Semgrep Tool - Cross-platform static analysis for security and code quality.
"""

import asyncio
import json
from typing import Any

from .tool_base import Tool


class SemgrepTool(Tool):
    """
    Semgrep static analysis tool for comprehensive security and code quality scanning.
    Cross-platform and works well on Windows, Linux, and macOS.
    """

    def __init__(self) -> None:
        super().__init__()
        self.default_timeout = 45.0  # Reduce timeout to 45 seconds for faster execution
        self.max_files_per_run = 200  # Higher limit for static analysis

    @property
    def name(self) -> str:
        return "semgrep"

    @property
    def description(self) -> str:
        return "Cross-platform static analysis for security vulnerabilities and code quality issues"

    @property
    def category(self) -> str:
        return "security"

    async def run(self, files: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Run Semgrep analysis on the provided files.
        """
        if not files:
            return []

        try:
            # Build semgrep command
            command = ["semgrep", "scan", "--json", "--quiet"]

            # Add configuration options
            rules = config.get("rules", "auto")
            if rules != "auto":
                command.extend(["--config", rules])

            # Add severity filtering
            severity = config.get("severity", ["INFO", "WARNING", "ERROR"])
            if severity:
                if isinstance(severity, str):
                    # Handle comma-separated string
                    severity = [s.strip() for s in severity.split(",")]
                for sev in severity:
                    command.extend(["--severity", sev])

            # Add additional flags
            if config.get("strict", False):
                command.append("--strict")

            if config.get("verbose", False):
                command.append("--verbose")

            # Add files/directories to scan
            command.extend(files)

            # Run semgrep
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            # Handle different exit codes
            if process.returncode not in [0, 1]:
                error_message = stderr.decode().strip()
                return [{"error": f"Semgrep execution failed: {error_message}"}]

            if not stdout:
                return []

            try:
                output = json.loads(stdout)
                return self._parse_semgrep_output(output)
            except json.JSONDecodeError:
                return [{"error": "Failed to parse Semgrep JSON output"}]

        except Exception as e:
            return [{"error": f"Semgrep execution error: {e!s}"}]

    def _parse_semgrep_output(self, output: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Parse Semgrep JSON output and convert to standard issue format.
        """
        issues = []

        # Handle results array
        results = output.get("results", [])

        for result in results:
            # Extract location information
            path = result.get("path", "unknown")
            start_line = result.get("start", {}).get("line")
            end_line = result.get("end", {}).get("line")
            start_col = result.get("start", {}).get("col")
            end_col = result.get("end", {}).get("col")

            # Extract message and rule information
            message = result.get("message", "Semgrep issue found")
            rule_id = result.get("check_id", "unknown")
            severity = result.get("extra", {}).get("severity", "medium")

            # Extract additional details
            extra = result.get("extra", {})
            metadata = extra.get("metadata", {})

            # Determine issue category based on rule ID
            category = self._determine_category(rule_id, metadata)

            issues.append(
                {
                    "filename": path,
                    "line_number": start_line,
                    "end_line": end_line,
                    "column_number": start_col,
                    "end_column": end_col,
                    "code": rule_id,
                    "message": message,
                    "severity": severity.lower(),
                    "details": {
                        "rule_id": rule_id,
                        "rule_name": extra.get("rule_name", "Unknown"),
                        "category": category,
                        "confidence": extra.get("confidence", "medium"),
                        "impact": metadata.get("impact", ""),
                        "cwe": metadata.get("cwe", []),
                        "owasp": metadata.get("owasp", []),
                        "references": metadata.get("references", []),
                        "fix": extra.get("fix", ""),
                        "fix_regex": extra.get("fix_regex", {}),
                    },
                }
            )

        return issues

    def _determine_category(self, rule_id: str, metadata: dict[str, Any]) -> str:
        """
        Determine the category of an issue based on rule ID and metadata.
        """
        # Check metadata first
        if metadata.get("category"):
            return metadata["category"]

        # Check for security-related patterns
        security_keywords = [
            "security",
            "vulnerability",
            "injection",
            "xss",
            "sqli",
            "rce",
            "authentication",
            "authorization",
            "crypto",
            "encryption",
        ]

        if any(keyword in rule_id.lower() for keyword in security_keywords):
            return "security"

        # Check for performance patterns
        performance_keywords = ["performance", "efficiency", "complexity", "memory", "cpu"]

        if any(keyword in rule_id.lower() for keyword in performance_keywords):
            return "performance"

        # Check for maintainability patterns
        maintainability_keywords = [
            "maintainability",
            "readability",
            "style",
            "convention",
            "best-practice",
        ]

        if any(keyword in rule_id.lower() for keyword in maintainability_keywords):
            return "maintainability"

        # Check for bug patterns
        bug_keywords = ["bug", "error", "exception", "null", "undefined", "type"]

        if any(keyword in rule_id.lower() for keyword in bug_keywords):
            return "bug"

        # Default category
        return "general"

    def get_default_config(self) -> dict[str, Any]:
        """
        Get default configuration for Semgrep.
        """
        return {
            "rules": "auto",  # Use Semgrep's auto-detection
            "severity": "INFO,WARNING,ERROR",
            "strict": False,
            "verbose": False,
            "categories": ["security", "performance", "maintainability", "bug"],
        }

    def get_supported_languages(self) -> list[str]:
        """
        Get list of languages supported by Semgrep.
        """
        return [
            "python",
            "javascript",
            "typescript",
            "java",
            "go",
            "ruby",
            "php",
            "c",
            "cpp",
            "csharp",
            "rust",
            "kotlin",
            "scala",
            "swift",
            "yaml",
            "json",
            "docker",
            "terraform",
            "bash",
            "powershell",
        ]

    def get_rule_categories(self) -> dict[str, list[str]]:
        """
        Get available rule categories and their descriptions.
        """
        return {
            "security": [
                "OWASP Top 10 vulnerabilities",
                "Common security anti-patterns",
                "Authentication and authorization issues",
                "Input validation problems",
                "Cryptographic vulnerabilities",
            ],
            "performance": [
                "Performance anti-patterns",
                "Memory leaks and inefficiencies",
                "Algorithm complexity issues",
                "Resource management problems",
            ],
            "maintainability": [
                "Code style and conventions",
                "Best practices violations",
                "Code complexity issues",
                "Documentation problems",
            ],
            "bug": [
                "Common programming errors",
                "Type safety issues",
                "Exception handling problems",
                "Logic errors",
            ],
        }
