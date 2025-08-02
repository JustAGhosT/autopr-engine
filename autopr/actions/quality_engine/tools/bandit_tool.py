import asyncio
import json
from typing import Any

from .tool_base import Tool


class BanditTool(Tool):
    """
    A tool for running Bandit, a security linter for Python.
    """

    def __init__(self) -> None:
        super().__init__()
        self.default_timeout = 20.0  # Reduce timeout to 20 seconds for faster execution

    @property
    def name(self) -> str:
        return "bandit"

    @property
    def description(self) -> str:
        return "A security linter for Python."

    async def run(self, files: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Run bandit on a list of files.
        """
        if not files:
            return []

        command = ["bandit", "-f", "json", *files]

        extra_args = config.get("args", [])
        command.extend(extra_args)

        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        # Bandit exits 0 for no issues, 1 for issues found. Other codes are errors.
        if process.returncode not in [0, 1]:
            error_message = stderr.decode().strip()
            print(f"Error running bandit: {error_message}")
            return [{"error": f"Bandit execution failed: {error_message}"}]

        if not stdout:
            return []

        try:
            # The JSON output contains a 'results' key.
            output = json.loads(stdout)
            results = output.get("results", [])
            return results
        except json.JSONDecodeError:
            print(f"Failed to parse bandit output: {stdout.decode()}")
            return [{"error": "Failed to parse bandit JSON output"}]
