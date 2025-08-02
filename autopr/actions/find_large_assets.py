import os
import pathlib

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    size_threshold_mb: float = 0.5
    directory: str = "public"


class Outputs(pydantic.BaseModel):
    large_files: list


class FindLargeAssets(Action[Inputs, Outputs]):
    """
    Scans the specified directory for files larger than the given size threshold (in MB).
    """

    id = "find_large_assets"

    async def run(self, inputs: Inputs) -> Outputs:
        threshold_bytes = inputs.size_threshold_mb * 1024 * 1024
        large_files = []
        for root, _, files in os.walk(inputs.directory):
            for file in files:
                path = os.path.join(root, file)
                try:
                    size = pathlib.Path(path).stat().st_size
                    if size > threshold_bytes:
                        large_files.append(
                            {"file": path, "size_mb": round(size / (1024 * 1024), 2)}
                        )
                except Exception:
                    continue
        return Outputs(large_files=large_files)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=FindLargeAssets,
            inputs=Inputs(size_threshold_mb=0.5),
        )
    )
