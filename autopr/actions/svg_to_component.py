import os
import re

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    svg_code: str
    component_name: str


class Outputs(pydantic.BaseModel):
    created_file: str


SVG_COMPONENT_TEMPLATE = """import React from 'react';

export function {component_name}(props: React.SVGProps<SVGSVGElement>) {{
  return (
    {svg_code}
  );
}}
"""


class SvgToComponent(Action[Inputs, Outputs]):
    """
    Converts raw SVG code into a reusable React component.
    """

    id = "svg_to_component"

    def _clean_svg(self, svg_code: str) -> str:
        # Add props to the svg tag
        svg_code = svg_code.replace("<svg", "<svg {{...props}}")
        # Naive camelCase conversion for attributes like 'stroke-width'
        return re.sub(
            r"(\w+)-(\w+)=", lambda m: f"{m.group(1)}{m.group(2).capitalize()}=", svg_code
        )

    async def run(self, inputs: Inputs) -> Outputs:
        icons_dir = "components/ui/icons"
        filename = f"{icons_dir}/{inputs.component_name}.tsx"

        os.makedirs(icons_dir, exist_ok=True)

        cleaned_svg = self._clean_svg(inputs.svg_code)

        content = SVG_COMPONENT_TEMPLATE.format(
            component_name=inputs.component_name, svg_code=cleaned_svg
        )

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        return Outputs(created_file=filename)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    SVG_EXAMPLE = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7l10 5 10-5-10-5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    asyncio.run(
        run_action_manually(
            action=SvgToComponent,
            inputs=Inputs(svg_code=SVG_EXAMPLE, component_name="MyIcon"),
        )
    )
