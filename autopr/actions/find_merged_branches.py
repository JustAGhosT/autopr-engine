import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    remote: str = "origin"


class Outputs(pydantic.BaseModel):
    merged_branches: list[str]


class FindMergedBranches(Action[Inputs, Outputs]):
    """
    [Simulation] Finds local branches that have been merged into the main branch on the remote.
    """

    id = "find_merged_branches"

    async def run(self, inputs: Inputs) -> Outputs:
        # In a real implementation, you would run git commands to fetch, prune, and find merged branches
        # For simulation, return a fake list
        branches = ["feature/old-feature-1", "fix/old-bug-2"]
        return Outputs(merged_branches=branches)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=FindMergedBranches,
            inputs=Inputs(),
        )
    )
