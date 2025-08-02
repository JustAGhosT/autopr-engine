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

        if process.returncode != 0 and process.returncode != 1:
            error_message = stderr.decode().strip()
            print(f"Error running ruff: {error_message}")
            return [{"error": f"Ruff execution failed: {error_message}"}]

        if not stdout:
            return []

        try:
            issues = json.loads(stdout)
            return list(issues) if isinstance(issues, list) else [issues]
        except json.JSONDecodeError:
            print(f"Failed to parse ruff output: {stdout.decode()}")
            return [{"error": "Failed to parse ruff JSON output"}]
