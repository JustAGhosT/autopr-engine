import asyncio
from typing import Any

from .tool_base import Tool


class PyTestTool(Tool):
    """
    A tool for running tests using the PyTest framework.
    """

    def __init__(self) -> None:
        super().__init__()
        self.default_timeout = 60.0  # Increase timeout to 60 seconds for comprehensive mode

    @property
    def name(self) -> str:
        return "pytest"

    @property
    def description(self) -> str:
        return "A tool for running tests using PyTest."

    def is_available(self) -> bool:
        """Check if pytest is available."""
        return self.check_command_availability("pytest")

    def get_required_command(self) -> str | None:
        """Get the required command for this tool."""
        return "pytest"

    async def run(self, files: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Run PyTest on the specified files or directories.
        """
        target_paths = files if files else ["."]

        # Use a more efficient command without unsupported arguments
        command = ["pytest", "--tb=short", "--maxfail=10", *target_paths]

        extra_args = config.get("args", [])
        command.extend(extra_args)

        try:
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            # Handle different exit codes
            if process.returncode == 5:
                # No tests collected
                return []
            if process.returncode not in [0, 1]:
                error_message = stderr.decode().strip()
                print(f"Error running pytest: {error_message}")
                return [{"error": f"PyTest execution failed: {error_message}"}]

            # For now, just check if tests passed or failed
            if process.returncode == 0:
                return []  # All tests passed

            # If tests failed, return a generic error
            return [{"error": "PyTest found test failures"}]
        except TimeoutError:
            return [{"error": "PyTest execution timed out"}]
        except Exception as e:
            return [{"error": f"PyTest execution error: {e!s}"}]
