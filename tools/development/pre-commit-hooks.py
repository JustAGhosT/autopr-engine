#!/usr/bin/env python3
"""
Custom pre-commit hook to handle unstaged changes after Prettier formatting.
Automatically adds unstaged changes to the commit.
"""

import logging
import subprocess
import sys


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_command(
    cmd: list[str], *, capture_output: bool = True
) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        return subprocess.run(
            cmd, capture_output=capture_output, text=True, check=False
        )
    except Exception as e:
        cmd_str = " ".join(cmd)
        logger.exception("Error running command %s: %s", cmd_str, e)
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr=str(e))


def get_unstaged_files() -> list[str]:
    """Get list of unstaged modified files."""
    result = run_command(["git", "diff", "--name-only"])
    if result.returncode != 0:
        return []

    return [f.strip() for f in result.stdout.split("\n") if f.strip()]


def add_files(files: list[str]) -> bool:
    """Add files to git staging area."""
    if not files:
        return True

    result = run_command(["git", "add", *files])
    return result.returncode == 0


def main() -> int:
    """Main function for pre-commit hook."""
    # Check if we're in a git repository
    if run_command(["git", "rev-parse", "--git-dir"]).returncode != 0:
        logger.error("Not in a git repository")
        return 1

    # Get unstaged files
    unstaged_files = get_unstaged_files()
    if not unstaged_files:
        logger.info("SUCCESS: No unstaged changes detected. Proceeding with commit...")
        return 0

    # Automatically add unstaged changes
    logger.info("INFO: Found %d unstaged modified file(s):", len(unstaged_files))
    for file in unstaged_files:
        logger.info("  - %s", file)

    logger.info("ACTION: Automatically adding unstaged changes to commit...")
    if add_files(unstaged_files):
        logger.info("SUCCESS: Successfully added unstaged changes")
        return 0
    logger.error("ERROR: Failed to add unstaged changes")
    return 1


if __name__ == "__main__":
    sys.exit(main())
