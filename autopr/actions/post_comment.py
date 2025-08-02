import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    pull_request_number: int
    comment: str


class Outputs(pydantic.BaseModel):
    success: bool
    comment_url: str


class PostComment(Action[Inputs, Outputs]):
    """
    [Simulation] Posts a comment to a GitHub pull request.
    In a real scenario, this would use a GitHub API client.
    """

    id = "post_comment"

    async def run(self, inputs: Inputs) -> Outputs:
        # Simulate API call
        simulated_url = f"https://github.com/example/repo/issues/{inputs.pull_request_number}#issuecomment-12345"

        return Outputs(success=True, comment_url=simulated_url)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=PostComment,
            inputs=Inputs(pull_request_number=101, comment="This is a test comment."),
        )
    )
