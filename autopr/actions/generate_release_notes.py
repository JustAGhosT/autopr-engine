import subprocess

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    from_tag: str | None = None


class Outputs(pydantic.BaseModel):
    release_notes: str


class GenerateReleaseNotes(Action[Inputs, Outputs]):
    """
    Generates release notes by summarizing git commits since the last tag.
    Assumes a Conventional Commits-like message format (e.g., 'feat:', 'fix:').
    """

    id = "generate_release_notes"

    async def run(self, inputs: Inputs) -> Outputs:
        # Determine the commit range
        if inputs.from_tag:
            range_spec = f"{inputs.from_tag}..HEAD"
        else:
            try:
                # Get the latest tag
                latest_tag = subprocess.check_output(
                    ["git", "describe", "--tags", "--abbrev=0"], text=True
                ).strip()
                range_spec = f"{latest_tag}..HEAD"
            except subprocess.CalledProcessError:
                # No tags found, get all commits
                range_spec = "HEAD"

        # Get commit logs
        try:
            log_output = subprocess.check_output(
                ["git", "log", "--pretty=%s", range_spec], text=True
            ).strip()
            commits = log_output.split("\\n")
        except subprocess.CalledProcessError as e:
            return Outputs(release_notes=f"Error getting git log: {e}")

        # Categorize commits
        notes: dict[str, list[str]] = {
            "Features ✨": [],
            "Bug Fixes 🐛": [],
            "Documentation 📖": [],
            "Other Changes": [],
        }

        for commit in commits:
            if commit.lower().startswith("feat"):
                notes["Features ✨"].append(f"- {commit}")
            elif commit.lower().startswith("fix"):
                notes["Bug Fixes 🐛"].append(f"- {commit}")
            elif commit.lower().startswith("docs"):
                notes["Documentation 📖"].append(f"- {commit}")
            else:
                notes["Other Changes"].append(f"- {commit}")

        # Build the Markdown output
        markdown = "## What's New\\n\\n"
        for category, items in notes.items():
            if items:
                markdown += f"### {category}\\n"
                markdown += "\\n".join(items) + "\\n\\n"

        return Outputs(release_notes=markdown)


if __name__ == "__main__":
    import asyncio

    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=GenerateReleaseNotes,
            inputs=Inputs(),
        )
    )
