import asyncio
import json
import logging
from pathlib import Path
from typing import TypedDict

from autopr.actions.quality_engine.handlers.lint_issue import LintIssue
from autopr.actions.quality_engine.tools.registry import register_tool
from autopr.actions.quality_engine.tools.tool_base import Tool


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

    def is_available(self) -> bool:
        """Check if ESLint is available via npx."""
        # Check if npx is available
        if not self.check_command_availability("npx"):
            return False

        # Try to check if eslint is available via npx
        try:
            import subprocess

            result = subprocess.run(
                ["npx", "eslint", "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            return False

    def get_required_command(self) -> str | None:
        """Get the required command for this tool."""
        return "npx"

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
        except Exception:
            logging.exception("Error running ESLint")
            return [
                {
                    "filename": "",
                    "line_number": 0,
                    "column_number": 0,
                    "message": "ESLint execution failed due to an unexpected error",
                    "code": "eslint-error",
                    "level": "error",
                }
            ]
        else:
            # Check for execution errors
            if process.returncode not in (
                0,
                1,
            ):  # ESLint returns 1 if there are linting errors
                error_message = stderr.decode().strip()
                logging.error("Error running ESLint: %s", error_message)
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
                cwd = Path.cwd()
                if file_path.startswith(str(cwd)):
                    try:
                        file_path = str(Path(file_path).relative_to(cwd))
                    except ValueError:
                        file_path = str(Path(file_path))

                for message in result.get("messages", []):
                    ESLINT_SEVERITY_ERROR = 2
                    issue: LintIssue = {
                        "filename": file_path,
                        "line_number": message.get("line", 0),
                        "column_number": message.get("column", 0),
                        "message": message.get("message", "Unknown issue"),
                        "code": message.get("ruleId", "unknown"),
                        "level": (
                            "error"
                            if message.get("severity", 1) == ESLINT_SEVERITY_ERROR
                            else "warning"
                        ),
                    }
                    issues.append(issue)

            return issues

        except json.JSONDecodeError:
            logging.exception("Failed to parse ESLint output as JSON")
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
