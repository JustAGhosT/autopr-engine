import asyncio
import subprocess

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    pass


class Outputs(pydantic.BaseModel):
    test_results: str
    passed: bool


class RunChangedTests(Action[Inputs, Outputs]):
    """
    Intelligently runs only the tests relevant to the files changed in the current git state.
    Requires 'vitest' to be installed.
    """

    id = "run_changed_tests"

    async def run(self, inputs: Inputs) -> Outputs:
        # Get list of changed files from git
        try:
            changed_files_process = subprocess.run(
                ["git", "diff", "--name-only", "HEAD^", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            changed_files = changed_files_process.stdout.strip().split("\\n")
        except subprocess.CalledProcessError as e:
            return Outputs(test_results=f"Failed to get changed files: {e.stderr}", passed=False)

        if not any(f.endswith((".ts", ".tsx", ".js", ".jsx")) for f in changed_files):
            return Outputs(
                test_results="No relevant source files changed. Skipping tests.", passed=True
            )

        command = "pnpm vitest run --changed"

        # Run vitest with the --changed flag
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        output = stdout.decode("utf-8") + stderr.decode("utf-8")

        return Outputs(test_results=output, passed=process.returncode == 0)


if __name__ == "__main__":
    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=RunChangedTests,
            inputs=Inputs(),
        )
    )
