import os
import re

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    scan_path: str = "."
    exclude_paths: list[str] = ["node_modules", ".next", "autopr"]


class Outputs(pydantic.BaseModel):
    markdown_report: str
    todo_count: int


class GenerateTodoReport(Action[Inputs, Outputs]):
    """
    Scans the codebase for comments containing 'TODO:' and generates a Markdown report.
    """

    id = "generate_todo_report"

    async def run(self, inputs: Inputs) -> Outputs:
        todos = []
        todo_pattern = re.compile(r"//\s*TODO[:\s](.*)", re.IGNORECASE)

        for root, dirs, files in os.walk(inputs.scan_path):
            dirs[:] = [d for d in dirs if d not in inputs.exclude_paths]

            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            match = todo_pattern.search(line)
                            if match:
                                todos.append(
                                    {"file": filepath, "line": i, "task": match.group(1).strip()}
                                )
                except Exception:
                    continue

        if not todos:
            return Outputs(markdown_report="No TODOs found!", todo_count=0)

        report = "### 📝 TODO Report\\n\\n"
        report += "| File | Line | Task |\\n"
        report += "|------|------|------|\\n"
        for todo in todos:
            report += f"| `{todo['file']}` | {todo['line']} | {todo['task']} |\\n"

        return Outputs(markdown_report=report, todo_count=len(todos))


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    # Create a dummy file with a TODO for testing
    with open("dummy_todo_file.ts", "w", encoding="utf-8") as f:
        f.write("// TODO: Refactor this later")
    asyncio.run(
        run_action_manually(
            action=GenerateTodoReport,
            inputs=Inputs(),
        )
    )
