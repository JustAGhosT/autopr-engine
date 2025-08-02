import asyncio
import json
from typing import Any

from .tool_base import Tool


class RadonTool(Tool):
    """
    A tool for analyzing Python code complexity using Radon.
    """

    @property
    def name(self) -> str:
        return "radon"

    @property
    def description(self) -> str:
        return "A tool for analyzing Python code complexity."

    async def run(self, files: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Run Radon's cyclomatic complexity check on a list of files.
        """
        if not files:
            return []

        command = ["radon", "cc", "--json", *files]

        # Default max complexity to 10 (Rank C)
        max_complexity = config.get("max_complexity", 10)
        command.extend(["--max", str(max_complexity)])

        extra_args = config.get("args", [])
        command.extend(extra_args)

        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_message = stderr.decode().strip()
            print(f"Error running radon: {error_message}")
            return [{"error": f"Radon execution failed: {error_message}"}]

        if not stdout:
            return []

        try:
            # Radon's JSON output is a dictionary with file paths as keys.
            output = json.loads(stdout)
            return self._format_output(output, max_complexity)
        except json.JSONDecodeError:
            print(f"Failed to parse radon output: {stdout.decode()}")
            return [{"error": "Failed to parse radon JSON output"}]

    def _format_output(
        self, output: dict[str, list[dict[str, Any]]], threshold: int
    ) -> list[dict[str, Any]]:
        """
        Formats Radon's JSON output into a standardized list of issues.
        """
        issues = []
        for filename, results in output.items():
            for result in results:
                # Radon cc --max already filters, but we can double-check or just format.
                complexity = result.get("complexity", 0)
                issues.append(
                    {
                        "filename": filename,
                        "line_number": result.get("lineno"),
                        "column_number": result.get("col_offset"),
                        "code": "RADON_COMPLEXITY",
                        "message": f"Function '{result.get('name')}' has a cyclomatic complexity of {complexity}. Threshold is {threshold}.",
                        "details": result,
                    }
                )
        return issues
