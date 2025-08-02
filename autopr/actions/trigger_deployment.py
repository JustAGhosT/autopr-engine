import httpx
import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    webhook_url: str
    client_payload: dict = {}


class Outputs(pydantic.BaseModel):
    success: bool
    status_code: int
    text: str


class TriggerDeployment(Action[Inputs, Outputs]):
    """
    Triggers a deployment by sending a POST request to a specified deployment hook URL.
    """

    id = "trigger_deployment"

    async def run(self, inputs: Inputs) -> Outputs:
        headers = {"Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    inputs.webhook_url, json=inputs.client_payload, headers=headers
                )
            return Outputs(
                success=response.is_success, status_code=response.status_code, text=response.text
            )
        except httpx.RequestError as e:
            return Outputs(success=False, status_code=0, text=str(e))


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    # This action makes a real HTTP request, so use a mock server for real tests.
    # For this example, we'll point to a test service.
    asyncio.run(
        run_action_manually(
            action=TriggerDeployment,
            inputs=Inputs(webhook_url="https://httpbin.org/post", client_payload={"ref": "main"}),
        )
    )
