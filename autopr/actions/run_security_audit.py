import asyncio
from typing import Any

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    pass


class Outputs(pydantic.BaseModel):
    success: bool
    report: str
    vulnerabilities: list[dict[str, Any]]


class RunSecurityAudit(Action[Inputs, Outputs]):
    """
    [Simulation] Runs a security audit on dependencies using 'pnpm audit'.
    """

    id = "run_security_audit"

    async def run(self, inputs: Inputs) -> Outputs:
        command = "pnpm audit --json"

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        output = stdout.decode("utf-8")

        # pnpm audit exits with non-zero code if vulnerabilities are found
        success = process.returncode == 0

        # In a real implementation, you would parse the JSON output
        # For simulation, we'll just return the raw output and a dummy list
        simulated_vulnerabilities = (
            [{"name": "some-package", "severity": "high"}] if not success else []
        )

        return Outputs(
            success=success,
            report=output or stderr.decode("utf-8"),
            vulnerabilities=simulated_vulnerabilities,
        )


if __name__ == "__main__":
    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=RunSecurityAudit,
            inputs=Inputs(),
        )
    )
