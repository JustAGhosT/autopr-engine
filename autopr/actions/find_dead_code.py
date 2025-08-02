import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    scan_path: str = "."


class Outputs(pydantic.BaseModel):
    dead_code_report: str
    dead_exports: list[str]


class FindDeadCode(Action[Inputs, Outputs]):
    """
    [Simulation] Finds dead code using a tool like ts-prune or knip.
    """

    id = "find_dead_code"

    async def run(self, inputs: Inputs) -> Outputs:
        # In a real implementation, you would run 'npx ts-prune' or 'npx knip'
        # For simulation, return a fake report
        report = "Found 2 unused exports:\n- shared/utils.ts: unusedFunction\n- components/old/UnusedComponent.tsx: UnusedComponent"
        return Outputs(
            dead_code_report=report,
            dead_exports=[
                "shared/utils.ts:unusedFunction",
                "components/old/UnusedComponent.tsx:UnusedComponent",
            ],
        )


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=FindDeadCode,
            inputs=Inputs(),
        )
    )
