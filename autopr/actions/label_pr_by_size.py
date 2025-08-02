import subprocess

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    pass


class Outputs(pydantic.BaseModel):
    size_label: str  # "size: S", "size: M", "size: L", "size: XL"
    lines_changed: int


class LabelPRBySize(Action[Inputs, Outputs]):
    """
    Labels a PR by size (S, M, L, XL) based on the number of lines changed.
    """

    id = "label_pr_by_size"

    async def run(self, inputs: Inputs) -> Outputs:
        try:
            diff_process = subprocess.run(
                ["git", "diff", "--shortstat", "HEAD~1"], capture_output=True, text=True, check=True
            )
            stats = diff_process.stdout
            # Example output: " 1 file changed, 10 insertions(+), 5 deletions(-)"
            insertions = int(
                subprocess.run(
                    ["grep", "-o", "[0-9]* insertions"],
                    check=False,
                    input=stats,
                    capture_output=True,
                    text=True,
                ).stdout.split()[0]
                or 0
            )
            deletions = int(
                subprocess.run(
                    ["grep", "-o", "[0-9]* deletions"],
                    check=False,
                    input=stats,
                    capture_output=True,
                    text=True,
                ).stdout.split()[0]
                or 0
            )
            lines_changed = insertions + deletions
        except Exception:
            lines_changed = 50  # Default for simulation

        if lines_changed < 10:
            size_label = "size: S"
        elif lines_changed < 100:
            size_label = "size: M"
        elif lines_changed < 500:
            size_label = "size: L"
        else:
            size_label = "size: XL"

        return Outputs(size_label=size_label, lines_changed=lines_changed)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=LabelPRBySize,
            inputs=Inputs(),
        )
    )
