import asyncio
import logging
import os
from pathlib import Path
import re
from typing import Any

import pydantic

from autopr.actions.base.action import Action


logger = logging.getLogger(__name__)


class Inputs(pydantic.BaseModel):
    scan_path: str = "."
    exclude_paths: list[str] = ["node_modules", ".next", "tests"]
    exclude_files: list[str] = [".test.ts", ".spec.ts", ".test.tsx", ".spec.tsx"]


class Outputs(pydantic.BaseModel):
    found_logs: list[dict[str, Any]]


class AnalyzeConsoleLogs(Action[Inputs, Outputs]):
    """
    Scans the codebase for console.log statements, excluding specified paths and test files.
    """

    id = "analyze_console_logs"

    async def run(self, inputs: Inputs) -> Outputs:
        found_logs = []
        log_pattern = re.compile(r"console\.log\(")

        for root, dirs, files in os.walk(inputs.scan_path):
            # Exclude directories
            dirs[:] = [d for d in dirs if d not in inputs.exclude_paths]

            for file in files:
                # Exclude specific file patterns
                if any(file.endswith(pattern) for pattern in inputs.exclude_files):
                    continue

                filepath = str(Path(root) / file)

                try:
                    # Use thread to avoid blocking in async context
                    lines = await asyncio.to_thread(
                        Path(filepath).read_text, encoding="utf-8", errors="ignore"
                    )
                    for i, line in enumerate(lines.splitlines(), 1):
                        if log_pattern.search(line):
                            found_logs.append(
                                {"file": filepath, "line": i, "content": line.strip()}
                            )
                except Exception:
                    logger.exception("Failed reading file: %s", filepath)
                    continue

        return Outputs(found_logs=found_logs)


if __name__ == "__main__":
    from autopr.tests.utils import run_action_manually

    # Create a dummy file with a console.log for testing
    Path("dummy_log_file.ts").write_text("console.log('hello');", encoding="utf-8")
    Path("dummy_log_file.test.ts").write_text(
        "console.log('hello in test');", encoding="utf-8"
    )
    asyncio.run(
        run_action_manually(
            action=AnalyzeConsoleLogs,
            inputs=Inputs(),
        )
    )
