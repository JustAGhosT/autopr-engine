import asyncio
import json
from typing import Any

from .tool_base import Tool


class RuffTool(Tool):
    """
    A tool for running Ruff, a Python linter.
    """

    @property
    def name(self) -> str:
        return "ruff"

    @property
    def description(self) -> str:
        return "A Python linter."

    def is_available(self) -> bool:
        """Check if ruff is available."""
        return self.check_command_availability("ruff")

    def get_required_command(self) -> str | None:
        """Get the required command for this tool."""
        return "ruff"

    async def run(self, files: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Run ruff on a list of files.
        """
        if not files:
            return []

        command = ["ruff", "check", "--output-format", "json", *files]

        extra_args = config.get("args", [])
        command.extend(extra_args)

        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode not in {0, 1}:
            error_message = stderr.decode().strip()
            return [{"error": f"Ruff execution failed: {error_message}"}]

        if not stdout:
            return []

        try:
            issues = json.loads(stdout)
            return list(issues) if isinstance(issues, list) else [issues]
        except json.JSONDecodeError:
            return [{"error": "Failed to parse ruff JSON output"}]
