import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    branch_name: str


class Outputs(pydantic.BaseModel):
    success: bool
    log: str


class DeleteBranch(Action[Inputs, Outputs]):
    """
    [Simulation] Deletes a local and remote git branch.
    """

    id = "delete_branch"

    async def run(self, inputs: Inputs) -> Outputs:
        # In a real implementation, you would run 'git branch -d' and 'git push origin --delete'
        # For simulation, just print and return success
        return Outputs(
            success=True,
            log=f"Deleted branch {inputs.branch_name} locally and remotely (simulated)",
        )


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=DeleteBranch,
            inputs=Inputs(branch_name="feature/old-feature-1"),
        )
    )
