import asyncio
import os
import re
from typing import Any

from .tool_base import Tool


class InterrogateTool(Tool):
    """
    A tool for checking Python docstring coverage using Interrogate.
    """

    def __init__(self) -> None:
        super().__init__()
        self.default_timeout = 15.0  # Reduce timeout to 15 seconds for faster execution

    @property
    def name(self) -> str:
        return "interrogate"

    @property
    def description(self) -> str:
        return "A tool for checking Python docstring coverage."

    async def run(self, files: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Run Interrogate on a list of files.
        """
        if not files:
            return []

        # Interrogate is best run on directories. We'll find the unique directories
        # from the file list and run Interrogate on them.
        directories = sorted(list(set(os.path.dirname(f) for f in files if os.path.dirname(f))))
        if not directories:
            # Handle case where all files are in the root directory
            if any(os.path.dirname(f) == "" for f in files):
                directories = ["."]
            else:
                return []

        command = ["interrogate", *directories]

        fail_under = config.get("fail_under", 80)
        command.extend(["--fail-under", str(fail_under)])

        extra_args = config.get("args", [])
        command.extend(extra_args)

        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        # Interrogate returns 0 for success, 2 for coverage below threshold
        if process.returncode not in [0, 2]:
            error_message = stderr.decode().strip()
            if not error_message and stdout:
                error_message = stdout.decode().strip()
            print(f"Error running interrogate: {error_message}")
            return [{"error": f"Interrogate execution failed: {error_message}"}]

        if not stdout:
            return []

        output = stdout.decode()
        return self._parse_output(output, files, fail_under)

    def _parse_output(
        self, output: str, files_to_check: list[str], fail_under: int
    ) -> list[dict[str, Any]]:
        """
        Parses the output of Interrogate to check coverage and find issues.
        """
        issues = []

        # Check if coverage is below threshold
        coverage_match = re.search(r"TOTAL\s+\d+\s+\d+\s+\d+\s+(\d+\.?\d*)%", output)
        if coverage_match:
            coverage_percentage = float(coverage_match.group(1))
            if coverage_percentage < fail_under:
                issues.append(
                    {
                        "filename": "overall",
                        "line_number": None,
                        "code": "COVERAGE_BELOW_THRESHOLD",
                        "message": f"Docstring coverage {coverage_percentage}% is below threshold of {fail_under}%",
                        "details": {
                            "coverage_percentage": coverage_percentage,
                            "threshold": fail_under,
                        },
                    }
                )

        # Look for specific file issues in verbose output
        pattern = re.compile(
            r"^FAILED: (?P<file>[^:]+):(?P<line>\d+) - (?P<code>\w+) - (?P<message>.+)$"
        )

        for line in output.strip().split("\n"):
            match = pattern.match(line.strip())
            if match:
                issue_data = match.groupdict()
                # Only report issues for the files we were asked to check
                if issue_data["file"] in files_to_check:
                    issues.append(
                        {
                            "filename": issue_data["file"],
                            "line_number": int(issue_data["line"]),
                            "code": issue_data["code"],
                            "message": issue_data["message"].strip(),
                        }
                    )

        return issues
