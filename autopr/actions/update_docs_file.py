import re

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    filepath: str
    content: str
    # A unique start/end marker to replace content between
    start_marker: str = "<!-- DOCS:START -->"
    end_marker: str = "<!-- DOCS:END -->"


class Outputs(pydantic.BaseModel):
    success: bool
    error: str | None = None


class UpdateDocsFile(Action[Inputs, Outputs]):
    """
    Updates a documentation file by replacing content between specific markers.
    """

    id = "update_docs_file"

    async def run(self, inputs: Inputs) -> Outputs:
        try:
            with open(inputs.filepath, encoding="utf-8") as f:
                original_content = f.read()

            # Use regex to find and replace content between markers
            pattern = re.compile(
                f"({re.escape(inputs.start_marker)}\\n)(.*?)(\\n{re.escape(inputs.end_marker)})",
                re.DOTALL,
            )

            replacement = f"\\1{inputs.content}\\3"

            new_content, num_replacements = re.subn(pattern, replacement, original_content)

            if num_replacements == 0:
                return Outputs(success=False, error=f"Markers not found in file: {inputs.filepath}")

            with open(inputs.filepath, "w", encoding="utf-8") as f:
                f.write(new_content)

            return Outputs(success=True)

        except FileNotFoundError:
            return Outputs(success=False, error=f"File not found: {inputs.filepath}")
        except Exception as e:
            return Outputs(success=False, error=str(e))


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    # Create a dummy docs file for testing
    with open("dummy_docs.md", "w", encoding="utf-8") as f:
        f.write(
            "Some text before.\\n<!-- DOCS:START -->\\nOld content.\\n<!-- DOCS:END -->\\nSome text after."
        )
    asyncio.run(
        run_action_manually(
            action=UpdateDocsFile,
            inputs=Inputs(filepath="dummy_docs.md", content="This is the new content."),
        )
    )
