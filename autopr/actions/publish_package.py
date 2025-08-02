import asyncio

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    version_increment: str = "patch"  # patch, minor, major
    dry_run: bool = True


class Outputs(pydantic.BaseModel):
    success: bool
    log: str
    new_version: str | None = None


class PublishPackage(Action[Inputs, Outputs]):
    """
    Increments the version in package.json, builds, and publishes the package.
    Simulates using 'pnpm version' and 'pnpm publish'.
    """

    id = "publish_package"

    async def run(self, inputs: Inputs) -> Outputs:
        logs = []

        # 1. Version increment
        version_command = f"pnpm version {inputs.version_increment}"
        logs.append(f"Running: {version_command}")
        # In a real scenario, we'd capture the new version from stdout
        # For simulation, we'll just note it.
        logs.append("Simulated version increment to a new version.")

        # 2. Publish command
        publish_command = "pnpm publish"
        if inputs.dry_run:
            publish_command += " --dry-run"

        logs.append(f"Running: {publish_command}")
        process = await asyncio.create_subprocess_shell(
            publish_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        log_output = stdout.decode("utf-8") + stderr.decode("utf-8")
        logs.append(log_output)

        success = process.returncode == 0
        if not success:
            logs.append("--- FAILED ---")

        return Outputs(
            success=success,
            log="\\n".join(logs),
            new_version="simulated_new_version" if success else None,
        )


if __name__ == "__main__":
    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=PublishPackage,
            inputs=Inputs(dry_run=True),
        )
    )
