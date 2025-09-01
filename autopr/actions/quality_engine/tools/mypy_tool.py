import asyncio
import logging
import re
from typing import TypedDict

from autopr.actions.quality_engine.handlers.lint_issue import LintIssue
from autopr.actions.quality_engine.tools.registry import register_tool
from autopr.actions.quality_engine.tools.tool_base import Tool


class MyPyConfig(TypedDict, total=False):
    args: list[str]


@register_tool
class MyPyTool(Tool[MyPyConfig, LintIssue]):
    """
    A tool for running MyPy, a static type checker for Python.
    """

    def __init__(self) -> None:
        super().__init__()
        self.default_timeout = 30.0  # Reduce timeout to 30 seconds for faster execution

    @property
    def name(self) -> str:
        return "mypy"

    @property
    def description(self) -> str:
        return "A static type checker for Python."

    @property
    def category(self) -> str:
        return "linting"  # Override with specific category

    def is_available(self) -> bool:
        """Check if mypy is available."""
        return self.check_command_availability("mypy")

    def get_required_command(self) -> str | None:
        """Get the required command for this tool."""
        return "mypy"

    async def run(self, files: list[str], config: MyPyConfig) -> list[LintIssue]:
        """
        Run mypy on a list of files.
        """
        if not files:
            return []

        # MyPy does not have a stable JSON output, so we parse the text output.
        # Try to use mypy from poetry environment if available
        import sys
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            # We're in a virtual environment, try python -m mypy
            command = [sys.executable, "-m", "mypy", "--show-column-numbers", "--no-error-summary", "--no-pretty"]
        else:
            # Fall back to system mypy
            command = ["mypy", "--show-column-numbers", "--no-error-summary", "--no-pretty"]

        # Add any configured arguments
        if "args" in config:
            command.extend(config["args"])

        # Add files to analyze
        command.extend(files)

        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        # mypy returns 1 if issues are found, 0 if everything is fine.
        # A non-zero/non-one return code indicates an actual error.
        if process.returncode not in [0, 1]:
            error_message = stderr.decode().strip()
            logging.error("Error running mypy: %s", error_message)
            return [
                {
                    "filename": "",
                    "line_number": 0,
                    "column_number": 0,
                    "message": f"MyPy execution failed: {error_message}",
                    "code": "mypy-error",
                    "level": "error",
                }
            ]

        if not stdout:
            return []

        return self._parse_output(stdout.decode())

    def _parse_output(self, output: str) -> list[LintIssue]:
        """
        Parses the text output of MyPy into a structured list of issues.
        Example line: main.py:5:12: error: Incompatible return value type (got "int", expected "str")  [return-value]
        """
        issues = []
        pattern = re.compile(
            r"^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+): (?P<level>\w+): (?P<message>.+?)(?:  \[(?P<code>.+)\])?$"
        )

        for line in output.strip().split("\n"):
            if not line:
                continue
            match = pattern.match(line)
            if match:
                issue_data = match.groupdict()
                issue: LintIssue = {
                    "filename": issue_data["file"],
                    "line_number": int(issue_data["line"]),
                    "column_number": int(issue_data["col"]),
                    "code": issue_data.get("code", "mypy"),
                    "message": issue_data["message"].strip(),
                    "level": issue_data["level"],
                }
                issues.append(issue)
        return issues
