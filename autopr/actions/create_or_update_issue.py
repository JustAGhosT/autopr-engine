import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    title: str
    body: str
    # If an issue with this label and title exists, it will be updated.
    # Otherwise, a new one is created.
    find_label: str | None = None


class Outputs(pydantic.BaseModel):
    success: bool
    issue_url: str


class CreateOrUpdateIssue(Action[Inputs, Outputs]):
    """
    [Simulation] Creates a new GitHub issue, or updates an existing one
    found by a specific title and label.
    """

    id = "create_or_update_issue"

    async def run(self, inputs: Inputs) -> Outputs:
        if inputs.find_label:
            # Simulate finding an existing issue
            pass

        simulated_url = "https://github.com/example/repo/issues/102"

        return Outputs(success=True, issue_url=simulated_url)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=CreateOrUpdateIssue,
            inputs=Inputs(
                title="Weekly Tech Debt Report",
                body="Here is the list of TODOs for this week.",
                find_label="tech-debt-report",
            ),
        )
    )
