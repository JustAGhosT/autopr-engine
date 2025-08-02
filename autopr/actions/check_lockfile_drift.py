import asyncio

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    pass


class Outputs(pydantic.BaseModel):
    is_synced: bool
    output: str


class CheckLockfileDrift(Action[Inputs, Outputs]):
    """
    Checks if pnpm-lock.yaml is in sync with package.json by running 'pnpm install --frozen-lockfile'.
    """

    id = "check_lockfile_drift"

    async def run(self, inputs: Inputs) -> Outputs:
        process = await asyncio.create_subprocess_shell(
            "pnpm install --frozen-lockfile",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode("utf-8") + stderr.decode("utf-8")
        is_synced = process.returncode == 0
        return Outputs(is_synced=is_synced, output=output)


if __name__ == "__main__":
    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=CheckLockfileDrift,
            inputs=Inputs(),
        )
    )
