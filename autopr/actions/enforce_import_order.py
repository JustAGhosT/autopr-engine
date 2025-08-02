import asyncio

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    pass


class Outputs(pydantic.BaseModel):
    success: bool
    log: str


class EnforceImportOrder(Action[Inputs, Outputs]):
    """
    Simulates running a linter to enforce import order conventions.
    In a real scenario, this would trigger 'pnpm lint --fix --rule "import-order-rule"' or similar.
    """

    id = "enforce_import_order"

    async def run(self, inputs: Inputs) -> Outputs:
        # This is a simulation. A real implementation would use a specific linter command.
        # Example: `npx eslint --fix --rule 'import/order: [\"error\", {\"newlines-between\": \"always\"}]' .`
        command = "echo 'Simulating import order linting... All good!'"

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        log_output = stdout.decode("utf-8") + stderr.decode("utf-8")
        success = process.returncode == 0

        return Outputs(success=success, log=log_output)


if __name__ == "__main__":
    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=EnforceImportOrder,
            inputs=Inputs(),
        )
    )
