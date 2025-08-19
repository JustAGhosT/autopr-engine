import re

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    step_number: int
    status: str  # e.g., "[x]", "[~]", "[ ]"
    text: str | None = None  # Optional: new text for the line


class Outputs(pydantic.BaseModel):
    success: bool
    updated_line: str | None = None


class UpdateMigrationPlan(Action[Inputs, Outputs]):
    """
    Updates a specific step in the MIGRATION_PLAN.md file.
    """

    id = "update_migration_plan"

    async def run(self, inputs: Inputs) -> Outputs:
        plan_path = "MIGRATION_PLAN.md"
        try:
            with open(plan_path, encoding="utf-8") as f:
                lines = f.readlines()

            updated = False
            for i, line in enumerate(lines):
                # Match lines like "- [ ] 1. Some text"
                match = re.match(r"^\s*-\s*\[.\]\s*(\d+)\.", line)
                if match and int(match.group(1)) == inputs.step_number:
                    # Replace status
                    new_line = re.sub(r"\[.\]", inputs.status, line, count=1)
                    # Replace text if provided
                    if inputs.text:
                        new_line = re.sub(r"(\d+\.\s*)(.*)", f"\\1{inputs.text}", new_line)

                    lines[i] = new_line
                    updated = True
                    break

            if not updated:
                return Outputs(success=False)

            with open(plan_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            return Outputs(success=True, updated_line=lines[i].strip() if updated else None)

        except FileNotFoundError:
            return Outputs(success=False)
        except Exception:
            return Outputs(success=False)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    # Ensure a dummy plan exists for testing
    with open("MIGRATION_PLAN.md", "w", encoding="utf-8") as f:
        f.write("- [ ] 1. First step\\n- [ ] 2. Second step\\n")
    asyncio.run(
        run_action_manually(
            action=UpdateMigrationPlan,
            inputs=Inputs(step_number=1, status="[x]", text="First step completed!"),
        )
    )
