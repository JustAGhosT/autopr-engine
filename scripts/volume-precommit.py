#!/usr/bin/env python3
"""
Volume Control Pre-commit Hook

Runs the background fix queue with proper timeout and exit code handling.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run the background fix queue with timeout."""
    # Build the path to bg-fix-queue.py relative to this file
    script_dir = Path(__file__).parent
    bg_fix_queue_path = script_dir / "bg-fix-queue.py"

    try:
        # Run the background fix queue with timeout
        proc = subprocess.run(
            [sys.executable, str(bg_fix_queue_path)],
            timeout=120,
            capture_output=True,
            text=True,
        )

        # Propagate the exit code
        sys.exit(proc.returncode)

    except subprocess.TimeoutExpired:
        print("Background fix queue timed out after 120 seconds", file=sys.stderr)
        sys.exit(124)  # Conventional timeout exit code

    except Exception as e:
        print(f"Error running background fix queue: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
