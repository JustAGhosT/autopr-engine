import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    tag_name: str
    name: str
    body: str
    is_draft: bool = True
    is_prerelease: bool = False


class Outputs(pydantic.BaseModel):
    success: bool
    release_url: str


class CreateGithubRelease(Action[Inputs, Outputs]):
    """
    [Simulation] Creates a new draft release in GitHub.
    """

    id = "create_github_release"

    async def run(self, inputs: Inputs) -> Outputs:
        simulated_url = f"https://github.com/example/repo/releases/tag/{inputs.tag_name}"

        return Outputs(success=True, release_url=simulated_url)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=CreateGithubRelease,
            inputs=Inputs(tag_name="v1.0.0", name="Version 1.0.0", body="Initial release."),
        )
    )
