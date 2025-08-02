import asyncio
import json
from typing import Any

from .tool_base import Tool


class PyTestTool(Tool):
    """
    A tool for running tests using the PyTest framework.
    """

    def __init__(self) -> None:
        super().__init__()
        self.default_timeout = 30.0  # Reduce timeout to 30 seconds for faster execution

    @property
    def name(self) -> str:
        return "pytest"

    @property
    def description(self) -> str:
        return "A tool for running tests using PyTest."

    async def run(self, files: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Run PyTest on the specified files or directories.
        Requires the `pytest-json-report` plugin to be installed.
        """
        target_paths = files if files else ["."]

        command = ["pytest", "--json-report", "--json-report-file=none", *target_paths]

        extra_args = config.get("args", [])
        command.extend(extra_args)

        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        # Handle different exit codes
        if process.returncode == 5:
            # No tests collected
            return []
        elif process.returncode not in [0, 1]:
            error_message = stderr.decode().strip()
            print(f"Error running pytest: {error_message}")
            return [{"error": f"PyTest execution failed: {error_message}"}]

        # Try to find JSON output in the stdout
        output_lines = stdout.decode().split("\n")
        json_output = None

        for line in output_lines:
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    json_output = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue

        if not json_output:
            # If no JSON found, check if tests passed
            if process.returncode == 0:
                return []  # All tests passed
            else:
                return [{"error": "PyTest produced no JSON output"}]

        return self._format_output(json_output)

    def _format_output(self, report: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Formats the pytest-json-report into a standardized list of issues.
        We only report failed tests.
        """
        issues = []
        if not report.get("tests"):
            return []

        for test in report["tests"]:
            if test.get("outcome") == "failed":
                filename = test.get("nodeid", "").split("::")[0]
                lineno = None
                if test.get("call", {}).get("traceback"):
                    last_trace = test["call"]["traceback"][-1]
                    filename = last_trace.get("path", filename)
                    lineno = last_trace.get("lineno")

                issues.append(
                    {
                        "filename": filename,
                        "line_number": lineno,
                        "code": "PYTEST_FAILURE",
                        "message": f"Test failed: {test.get('nodeid')}",
                        "details": {
                            "outcome": test.get("outcome"),
                            "long_report": test.get("longrepr", ""),
                        },
                    }
                )
        return issues
