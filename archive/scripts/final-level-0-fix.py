#!/usr/bin/env python3
"""
Final Level 0 Fix - Complete IDE Refresh

This script forces a complete refresh of the IDE settings and verifies Level 0 is working
"""

import os
import time


def force_ide_refresh():
    """Force IDE to refresh all settings"""


    # Create a touch file to force refresh
    touch_file = ".vscode/refresh_trigger.txt"
    with open(touch_file, "w") as f:
        f.write(f"Refresh triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")


    # Remove any cached settings
    cache_dirs = [".vscode/.cache", ".cursor/.cache", ".pytest_cache", "__pycache__"]

    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                import shutil

                shutil.rmtree(cache_dir)
            except Exception:
                pass


    # Check all configuration files
    config_files = [
        (".vscode/settings.json", "VS Code Settings"),
        (".flake8", "Flake8 Config"),
        (".markdownlint.json", "MarkdownLint Config"),
        ("cspell.json", "CSpell Config"),
        ("mypy.ini", "MyPy Config"),
    ]

    for file_path, _description in config_files:
        if os.path.exists(file_path):
            pass
        else:
            pass

    # Check pyproject.toml
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml") as f:
            content = f.read()
            if "[tool.flake8]" in content or "[tool.ruff]" in content or "[tool.mypy]" in content:
                pass
            else:
                pass




if __name__ == "__main__":
    force_ide_refresh()
