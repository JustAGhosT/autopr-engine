import asyncio
import json
import os
from typing import TypedDict

from ..handlers.lint_issue import LintIssue
from .registry import register_tool
from .tool_base import Tool


class ESLintConfig(TypedDict, total=False):
    """Configuration options for ESLint."""

    config: str  # Path to .eslintrc file
    fix: bool  # Whether to auto-fix issues
    extensions: list[str]  # File extensions to lint
    ignore_pattern: list[str]  # Patterns to ignore
    args: list[str]  # Additional arguments to pass to ESLint


@register_tool
class ESLintTool(Tool[ESLintConfig, LintIssue]):
    """
    A tool for running ESLint on JavaScript/TypeScript code.
    """

    @property
    def name(self) -> str:
        return "eslint"

    @property
    def description(self) -> str:
        return "A static code analyzer for JavaScript and TypeScript."

    @property
    def category(self) -> str:
        return "linting"

    async def run(self, files: list[str], config: ESLintConfig) -> list[LintIssue]:
        """
        Run ESLint on a list of JavaScript/TypeScript files.

        Args:
            files: The files to lint
            config: ESLint configuration options

        Returns:
            A list of lint issues found
        """
        if not files:
            return []

        # Basic ESLint command
        command = ["npx", "eslint", "--format", "json"]

        # Add config file if specified
        if config.get("config"):
            command.extend(["--config", config["config"]])

        # Add fix flag if specified
        if config.get("fix"):
            command.append("--fix")

        # Add extension filters
        if config.get("extensions"):
            for ext in config["extensions"]:
                command.extend(["--ext", ext])

        # Add ignore patterns
        if config.get("ignore_pattern"):
            for pattern in config["ignore_pattern"]:
                command.extend(["--ignore-pattern", pattern])

        # Add additional arguments
        if config.get("args"):
            command.extend(config["args"])

        # Add files to analyze
        command.extend(files)

        # Run ESLint
        try:
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            # Check for execution errors
            if process.returncode not in [0, 1]:  # ESLint returns 1 if there are linting errors
                error_message = stderr.decode().strip()
                print(f"Error running ESLint: {error_message}")
                return [
                    {
                        "filename": "",
                        "line_number": 0,
                        "column_number": 0,
                        "message": f"ESLint execution failed: {error_message}",
                        "code": "eslint-error",
                        "level": "error",
                    }
                ]

            # Parse ESLint JSON output
            return self._parse_eslint_output(stdout.decode())

        except Exception as e:
            print(f"Error running ESLint: {e!s}")
            return [
                {
                    "filename": "",
                    "line_number": 0,
                    "column_number": 0,
                    "message": f"ESLint execution failed: {e!s}",
                    "code": "eslint-error",
                    "level": "error",
                }
            ]

    def _parse_eslint_output(self, output: str) -> list[LintIssue]:
        """
        Parse ESLint JSON output into LintIssue objects.

        Args:
            output: The JSON output from ESLint

        Returns:
            A list of lint issues
        """
        if not output.strip():
            return []

        try:
            eslint_results = json.loads(output)
            issues = []

            for result in eslint_results:
                file_path = result.get("filePath", "")

                # Convert to relative path if possible
                cwd = os.getcwd()
                if file_path.startswith(cwd):
                    file_path = os.path.relpath(file_path, cwd)

                for message in result.get("messages", []):
                    issue: LintIssue = {
                        "filename": file_path,
                        "line_number": message.get("line", 0),
                        "column_number": message.get("column", 0),
                        "message": message.get("message", "Unknown issue"),
                        "code": message.get("ruleId", "unknown"),
                        "level": message.get("severity", 1) == 2 and "error" or "warning",
                    }
                    issues.append(issue)

            return issues

        except json.JSONDecodeError:
            print("Failed to parse ESLint output as JSON")
            return [
                {
                    "filename": "",
                    "line_number": 0,
                    "column_number": 0,
                    "message": "Failed to parse ESLint output as JSON",
                    "code": "eslint-error",
                    "level": "error",
                }
            ]
