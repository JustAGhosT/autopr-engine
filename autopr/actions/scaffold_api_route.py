import os

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    route_name: str
    http_methods: list[str] = ["GET"]


class Outputs(pydantic.BaseModel):
    created_file: str


# Template for the Next.js App Router API route
ROUTE_TEMPLATE = """// app/api/{route_name}/route.ts
{method_imports}

{method_handlers}
"""

METHOD_HANDLER_TEMPLATE = """export async function {method}(request: Request) {{
  // TODO: Implement {method} handler
  return new Response('{method} handler for {route_name} not implemented.', {{ status: 501 }});
}}
"""


class ScaffoldApiRoute(Action[Inputs, Outputs]):
    """
    Scaffolds a new Next.js App Router API route file in the app/api/ directory.
    """

    id = "scaffold_api_route"

    async def run(self, inputs: Inputs) -> Outputs:
        route_dir = f"app/api/{inputs.route_name}"
        filename = f"{route_dir}/route.ts"

        os.makedirs(route_dir, exist_ok=True)

        method_handlers = "\\n".join(
            METHOD_HANDLER_TEMPLATE.format(method=method.upper(), route_name=inputs.route_name)
            for method in inputs.http_methods
        )

        # In Next.js 13+, Response is used instead of NextRequest/NextResponse for simple cases
        # No specific imports are needed for the basic template.
        method_imports = ""

        content = ROUTE_TEMPLATE.format(
            route_name=inputs.route_name,
            method_imports=method_imports,
            method_handlers=method_handlers,
        )

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        return Outputs(created_file=filename)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=ScaffoldApiRoute,
            inputs=Inputs(route_name="my-new-route", http_methods=["GET", "POST"]),
        )
    )
