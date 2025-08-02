import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    package_name: str


class Outputs(pydantic.BaseModel):
    success: bool
    log: str
    new_version: str | None = None


class UpdateDependency(Action[Inputs, Outputs]):
    """
    [Simulation] Updates a dependency to the latest version and creates a new branch.
    """

    id = "update_dependency"

    async def run(self, inputs: Inputs) -> Outputs:
        # In a real implementation, you would run 'pnpm add <package>@latest' and create a branch
        # For simulation, just print and return success
        return Outputs(
            success=True,
            log=f"Updated {inputs.package_name} to latest (simulated)",
            new_version="1.2.3",
        )


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=UpdateDependency,
            inputs=Inputs(package_name="react"),
        )
    )
