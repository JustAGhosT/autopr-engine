import subprocess

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    pass


class Outputs(pydantic.BaseModel):
    summary: str


class SummarizePrWithAI(Action[Inputs, Outputs]):
    """
    Reads the git diff of a pull request and generates a human-readable summary.
    This is a SIMULATION and does not make a real AI API call.
    """

    id = "summarize_pr_with_ai"

    async def run(self, inputs: Inputs) -> Outputs:
        # Get the git diff
        try:
            diff_process = subprocess.run(
                ["git", "diff", "HEAD~1"], capture_output=True, text=True, check=True
            )
            diff = diff_process.stdout
        except subprocess.CalledProcessError as e:
            return Outputs(summary=f"Could not get git diff: {e.stderr}")

        # In a real scenario, you would send this 'diff' to an AI model.
        # For this simulation, we will return a hardcoded summary based on the diff content.
        summary = "### AI-Generated Summary 🤖\\n\\n"
        if "component" in diff.lower():
            summary += "- Modified or created a new UI component.\\n"
        if "action" in diff.lower():
            summary += "- Added or updated a workflow action.\\n"
        if "hook" in diff.lower():
            summary += "- Implemented changes to a React hook.\\n"

        if len(summary) < 50:  # if no keywords were found
            summary += "- General code improvements and refactoring."

        return Outputs(summary=summary)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=SummarizePrWithAI,
            inputs=Inputs(),
        )
    )
