#!/usr/bin/env python3
"""
Enhanced Markdown Linter Pre-commit Hook (Python)
Automatically fixes markdown issues and re-stages files
"""

import hashlib
from pathlib import Path
import subprocess
import sys


def get_file_hash(file_path):
    """Get MD5 hash of a file."""
    try:
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read(), usedforsecurity=False).hexdigest()
    except OSError:
        return None


def main():
    """Main entry point for the pre-commit hook."""
    if len(sys.argv) < 2:
        return 0

    files = sys.argv[1:]
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent

    # Change to markdown linter directory
    original_cwd = Path.cwd()
    linter_dir = script_dir

    modified_files = []
    files_processed = 0

    for file_path in files:
        # Resolve the full path relative to repo root
        full_path = Path(file_path) if Path(file_path).is_absolute() else repo_root / file_path

        if not full_path.exists():
            continue

        # Get file hash before processing
        before_hash = get_file_hash(full_path)
        if before_hash is None:
            continue

        # Run markdown linter with --fix
        try:
            # Change to linter directory and run the linter
            import os

            os.chdir(linter_dir)

            result = subprocess.run(
                [sys.executable, "__main__.py", str(full_path), "--fix"],
                check=False,
                capture_output=True,
                text=True,
            )

            # Change back to original directory
            os.chdir(original_cwd)

            if result.returncode == 0:
                # Get file hash after processing
                after_hash = get_file_hash(full_path)

                # Check if file was actually modified
                if before_hash != after_hash:
                    # Store the original relative path for git add
                    modified_files.append(file_path)

        except Exception:
            pass

        files_processed += 1

    # Re-stage modified files if any
    if modified_files:
        for file_path in modified_files:
            try:
                result = subprocess.run(
                    ["git", "add", file_path],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=repo_root,
                )

                if result.returncode != 0:
                    pass

            except Exception:
                pass

    # Always return success so commit proceeds
    return 0


if __name__ == "__main__":
    sys.exit(main())
