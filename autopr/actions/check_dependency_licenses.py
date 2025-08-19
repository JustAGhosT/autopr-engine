import asyncio
import json

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    allowed_licenses: list[str] = [
        "MIT",
        "ISC",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
    ]


class Outputs(pydantic.BaseModel):
    success: bool
    forbidden_packages: list[dict]
    log: str


class CheckDependencyLicenses(Action[Inputs, Outputs]):
    """
    Checks dependency licenses against an allowed list using 'license-checker'.
    """

    id = "check_dependency_licenses"

    async def run(self, inputs: Inputs) -> Outputs:
        command = "npx license-checker --json"

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            return Outputs(success=False, forbidden_packages=[], log=stderr.decode("utf-8"))

        try:
            licenses = json.loads(stdout)
            forbidden_packages = []
            allowed_set = set(inputs.allowed_licenses)

            for package, details in licenses.items():
                license_str = details.get("licenses", "UNKNOWN")
                # Handle license strings like "(MIT OR Apache-2.0)"
                package_licenses = re.split(
                    r" OR | AND ", license_str.replace("(", "").replace(")", "")
                )

                if not any(l in allowed_set for l in package_licenses):
                    forbidden_packages.append(
                        {
                            "package": package,
                            "version": details.get("version"),
                            "licenses": license_str,
                            "repository": details.get("repository"),
                        }
                    )

            return Outputs(
                success=not forbidden_packages,
                forbidden_packages=forbidden_packages,
                log=f"Found {len(forbidden_packages)} packages with non-allowed licenses.",
            )

        except json.JSONDecodeError as e:
            return Outputs(
                success=False,
                forbidden_packages=[],
                log=f"Failed to parse license-checker output: {e}",
            )


if __name__ == "__main__":
    import re

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=CheckDependencyLicenses,
            inputs=Inputs(),
        )
    )
