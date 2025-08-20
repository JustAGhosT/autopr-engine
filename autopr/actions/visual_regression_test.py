import os

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    urls: list[str] = ["/"]
    # In a real action, this would be a git ref to compare against
    base_branch: str = "main"


class Outputs(pydantic.BaseModel):
    success: bool
    report: str
    diff_images: list[str]


class VisualRegressionTest(Action[Inputs, Outputs]):
    """
    [Simulation] Runs a visual regression test by taking screenshots of specified pages
    and comparing them against a baseline.
    """

    id = "visual_regression_test"

    async def run(self, inputs: Inputs) -> Outputs:
        report_lines = ["[Simulation] Visual Regression Test Report"]
        diff_images = []
        success = True

        for url in inputs.urls:
            # 1. Take baseline screenshot (from base_branch)
            baseline_path = f"screenshots/baseline{url.replace('/', '_')}.png"
            report_lines.append(
                f"Simulating: Fetched baseline screenshot for '{url}' from '{inputs.base_branch}' -> {baseline_path}"
            )

            # 2. Take current screenshot (from current branch)
            current_path = f"screenshots/current{url.replace('/', '_')}.png"
            report_lines.append(
                f"Simulating: Took current screenshot for '{url}' -> {current_path}"
            )

            # 3. Compare images
            # In a real scenario, you'd use a library like pixelmatch
            are_different = "component" in url  # Simulate a difference for a specific url
            if are_different:
                success = False
                diff_path = f"screenshots/diff{url.replace('/', '_')}.png"
                diff_images.append(diff_path)
                report_lines.append(
                    f"❌ Difference found for '{url}'. Diff image generated at {diff_path}"
                )
            else:
                report_lines.append(f"✅ No difference found for '{url}'.")

        return Outputs(success=success, report="\\n".join(report_lines), diff_images=diff_images)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    os.makedirs("screenshots", exist_ok=True)  # Ensure dir exists for simulation
    asyncio.run(
        run_action_manually(
            action=VisualRegressionTest,
            inputs=Inputs(urls=["/", "/components/new"]),
        )
    )
