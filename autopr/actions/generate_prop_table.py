import asyncio
import json

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    component_path: str


class Outputs(pydantic.BaseModel):
    markdown_table: str
    error: str | None = None


class GeneratePropTable(Action[Inputs, Outputs]):
    """
    Parses a component's TypeScript props and generates a Markdown table.
    This action relies on the 'react-docgen-typescript' package.
    """

    id = "generate_prop_table"

    async def run(self, inputs: Inputs) -> Outputs:
        command = f"npx -p react-docgen-typescript-loader@3.7.2 -p typescript@5 react-docgen-typescript {inputs.component_path} --compilerOptions '{{\"allowSyntheticDefaultImports\":true}}' --skipChildrenPropWithoutDoc"

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            return Outputs(markdown_table="", error=stderr.decode("utf-8"))

        try:
            docgen_output = json.loads(stdout)
            if not docgen_output:
                return Outputs(
                    markdown_table="No props found or component not exported correctly.", error=None
                )

            # Assuming single component per file for simplicity
            component_info = next(iter(docgen_output.values()))
            props = component_info.get("props", {})

            if not props:
                return Outputs(markdown_table="No props found for this component.", error=None)

            table = "| Prop | Type | Default | Description |\\n"
            table += "|------|------|---------|-------------|\\n"

            for prop_name, prop_details in props.items():
                prop_type = prop_details.get("type", {}).get("name", "n/a").replace("|", "\\|")
                default_value = prop_details.get("defaultValue", {}).get("value", "n/a")
                description = prop_details.get("description", "").replace("\\n", " ")
                table += f"| `{prop_name}` | `{prop_type}` | `{default_value}` | {description} |\\n"

            return Outputs(markdown_table=table, error=None)
        except (json.JSONDecodeError, IndexError) as e:
            return Outputs(markdown_table="", error=f"Failed to parse docgen output: {e}")


if __name__ == "__main__":
    from autopr.tests.utils import run_action_manually

    # Note: This test requires a valid component file to exist.
    # Create a dummy component for testing purposes.
    with open("dummy_component.tsx", "w", encoding="utf-8") as f:
        f.write(
            "import React from 'react';\\nexport const MyComponent = (props: {{ name: string }}) => <div>hello</div>;"
        )
    asyncio.run(
        run_action_manually(
            action=GeneratePropTable,
            inputs=Inputs(component_path="dummy_component.tsx"),
        )
    )
