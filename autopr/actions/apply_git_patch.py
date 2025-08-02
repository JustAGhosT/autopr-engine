import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    patch_content: str


class Outputs(pydantic.BaseModel):
    success: bool
    log: str


class ApplyGitPatch(Action[Inputs, Outputs]):
    """
    [Simulation] Applies a git patch to the current branch.
    """

    id = "apply_git_patch"

    async def run(self, inputs: Inputs) -> Outputs:
        # In a real implementation, you would write the patch to a file and run 'git apply'
        # For simulation, just print and return success
        if not inputs.patch_content.strip():
            return Outputs(success=False, log="Empty patch content")
        return Outputs(success=True, log="Patch applied (simulated)")


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=ApplyGitPatch,
            inputs=Inputs(patch_content="diff --git a/file.txt b/file.txt\n..."),
        )
    )
