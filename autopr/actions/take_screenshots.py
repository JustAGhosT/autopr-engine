import os

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    urls: list[str] = ["/"]
    output_dir: str = "screenshots/gallery"


class Outputs(pydantic.BaseModel):
    success: bool
    screenshot_paths: list[str]


class TakeScreenshots(Action[Inputs, Outputs]):
    """
    [Simulation] Takes screenshots of key pages for a documentation gallery.
    """

    id = "take_screenshots"

    async def run(self, inputs: Inputs) -> Outputs:
        os.makedirs(inputs.output_dir, exist_ok=True)
        paths = []
        for url in inputs.urls:
            filename = f"{inputs.output_dir}/{url.replace('/', '_')}.png"
            paths.append(filename)

        return Outputs(success=True, screenshot_paths=paths)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=TakeScreenshots,
            inputs=Inputs(urls=["/", "/about"]),
        )
    )
