import os

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    component_name: str
    directory: str = "components"


class Outputs(pydantic.BaseModel):
    created_file: str


COMPONENT_TEMPLATE = """import React from 'react';

export function {name}() {{
  return <div>{name} component</div>;
}}
"""


class ScaffoldComponent(Action[Inputs, Outputs]):
    """
    Scaffolds a new React component file in the specified directory.
    """

    id = "scaffold_component"

    async def run(self, inputs: Inputs) -> Outputs:
        filename = f"{inputs.directory}/{inputs.component_name}.tsx"
        os.makedirs(inputs.directory, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(COMPONENT_TEMPLATE.format(name=inputs.component_name))
        return Outputs(created_file=filename)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=ScaffoldComponent,
            inputs=Inputs(component_name="MyNewComponent"),
        )
    )
