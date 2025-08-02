import os
import pathlib

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    directory: str
    exclude_patterns: list[str] = ["*.test.ts", "*.spec.ts", "index.ts"]


class Outputs(pydantic.BaseModel):
    created_file: str
    exports_count: int


class GenerateBarrelFile(Action[Inputs, Outputs]):
    """
    Generates an 'index.ts' barrel file for a specified directory, exporting all modules within it.
    """

    id = "generate_barrel_file"

    async def run(self, inputs: Inputs) -> Outputs:
        if not pathlib.Path(inputs.directory).is_dir():
            return Outputs(created_file="", exports_count=0)

        exports = []
        for item in os.listdir(inputs.directory):
            item_path = os.path.join(inputs.directory, item)
            # Skip if it matches any exclude pattern
            if any(item.endswith(p) for p in inputs.exclude_patterns):
                continue

            if pathlib.Path(item_path).is_file() and (item.endswith((".ts", ".tsx"))):
                module_name = item.rsplit(".", 1)[0]
                exports.append(f"export * from './{module_name}';")

        index_path = os.path.join(inputs.directory, "index.ts")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(exports))

        return Outputs(created_file=index_path, exports_count=len(exports))


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    # Create dummy files for testing
    os.makedirs("components/ui", exist_ok=True)
    with open("components/ui/button.tsx", "w", encoding="utf-8") as f:
        f.write("export const Button = () => {};")
    with open("components/ui/card.tsx", "w", encoding="utf-8") as f:
        f.write("export const Card = () => {};")
    asyncio.run(
        run_action_manually(
            action=GenerateBarrelFile,
            inputs=Inputs(directory="components/ui"),
        )
    )
