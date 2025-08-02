import asyncio

import pydantic

from autopr.actions.base.action import Action


# Define the inputs for our action
class Inputs(pydantic.BaseModel):
    # The command to run, e.g., "pnpm dup-check"
    command: str


# Define the outputs for our action
class Outputs(pydantic.BaseModel):
    # The standard output from the script
    stdout: str
    # The standard error from the script
    stderr: str


class RunScript(Action[Inputs, Outputs]):
    """
    Runs a shell command (e.g., a pnpm script) and returns its output.
    This is useful for triggering custom maintenance or build scripts from a workflow.
    """

    id = "run_script"

    async def run(self, inputs: Inputs) -> Outputs:
        # Log the command we are about to run

        # Create a subprocess to run the command
        process = await asyncio.create_subprocess_shell(
            inputs.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait for the command to complete and capture its output
        stdout, stderr = await process.communicate()

        # Return the decoded output
        return Outputs(
            stdout=stdout.decode("utf-8"),
            stderr=stderr.decode("utf-8"),
        )


# This allows you to test the action manually by running `python -m autopr.actions.run_script`
if __name__ == "__main__":
    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=RunScript,
            inputs=Inputs(command="pnpm --version"),  # Example command
        )
    )
