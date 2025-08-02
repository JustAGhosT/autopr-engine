import subprocess

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    pass


class Outputs(pydantic.BaseModel):
    labels_to_add: list[str]


class LabelPR(Action[Inputs, Outputs]):
    """
    Determines labels to add to a PR based on the paths of changed files.
    This action only determines the labels; a separate workflow step is needed to apply them.
    """

    id = "label_pr"

    async def run(self, inputs: Inputs) -> Outputs:
        # Get list of changed files from git against the main/master branch
        try:
            # Fetch the base branch to ensure we can diff against it
            subprocess.run(["git", "fetch", "origin", "main"], check=True)

            changed_files_process = subprocess.run(
                ["git", "diff", "--name-only", "origin/main...HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            changed_files = changed_files_process.stdout.strip().split("\\n")
        except subprocess.CalledProcessError:
            # Fallback for local testing where origin/main might not be set up
            changed_files_process = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                check=False,
                capture_output=True,
                text=True,
            )
            changed_files = changed_files_process.stdout.strip().split("\\n")

        labels = set()
        for filepath in changed_files:
            if filepath.startswith("backend/"):
                labels.add("backend")
            if filepath.startswith(("components/", "app/", "styles/")):
                labels.add("frontend")
            if filepath.startswith("shared/"):
                labels.add("shared")
            if filepath.startswith("tests/"):
                labels.add("tests")
            if filepath.startswith("docs/") or filepath.endswith(".md"):
                labels.add("documentation")
            if filepath.startswith(".github/workflows/"):
                labels.add("ci/cd")

        return Outputs(labels_to_add=list(labels))


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=LabelPR,
            inputs=Inputs(),
        )
    )
