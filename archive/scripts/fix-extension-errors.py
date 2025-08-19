#!/usr/bin/env python3
"""
Fix Extension Errors - Clear caches and restart IDE to resolve file access errors
"""

import contextlib
import os
from pathlib import Path
import platform
import shutil
import subprocess


def main():

    # Clear VS Code/Cursor caches

    # Get user home directory
    home = Path.home()

    # Clear VS Code caches
    vscode_cache = home / ".vscode" / "extensions"
    if vscode_cache.exists():
        try:
            # Remove problematic extension caches
            for ext_dir in vscode_cache.iterdir():
                if ext_dir.is_dir():
                    ext_name = ext_dir.name.lower()
                    if any(name in ext_name for name in ["continue", "monica", "tabnine"]):
                        shutil.rmtree(ext_dir, ignore_errors=True)
        except Exception:
            pass

    # Clear Cursor caches
    cursor_cache = home / ".cursor" / "extensions"
    if cursor_cache.exists():
        try:
            # Remove problematic extension caches
            for ext_dir in cursor_cache.iterdir():
                if ext_dir.is_dir():
                    ext_name = ext_dir.name.lower()
                    if any(name in ext_name for name in ["continue", "monica", "tabnine"]):
                        shutil.rmtree(ext_dir, ignore_errors=True)
        except Exception:
            pass

    # Clear workspace caches
    workspace_cache = Path(".vscode") / "extensions"
    if workspace_cache.exists():
        with contextlib.suppress(Exception):
            shutil.rmtree(workspace_cache, ignore_errors=True)

    # Clear Python cache
    try:
        # Remove __pycache__ directories
        for pycache in Path().rglob("__pycache__"):
            shutil.rmtree(pycache, ignore_errors=True)

        # Remove .pyc files
        for pyc_file in Path().rglob("*.pyc"):
            pyc_file.unlink(missing_ok=True)
    except Exception:
        pass

    # Create a touch file to force IDE refresh
    touch_file = ".extension-refresh"
    with open(touch_file, "w") as f:
        f.write(f"Extension refresh triggered at {__import__('datetime').datetime.now()}")

    # Try to reload the IDE window
    try:
        if platform.system() == "Windows":
            subprocess.run(
                ["code", "--command", "workbench.action.reloadWindow"],
                capture_output=True,
                timeout=5,
                check=False,
            )
        else:
            subprocess.run(
                ["code", "--command", "workbench.action.reloadWindow"],
                capture_output=True,
                timeout=5,
                check=False,
            )
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass

    # Clean up touch file
    import time

    time.sleep(0.1)
    if os.path.exists(touch_file):
        os.remove(touch_file)


if __name__ == "__main__":
    main()
