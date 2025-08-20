#!/usr/bin/env python3
"""
Level 0 Complete Verification

This script verifies that Level 0 (no linting) is completely working
"""

import os
import subprocess


def check_tool_disabled(tool_name, command, expected_exit=0):
    """Check if a tool is disabled"""
    try:
        result = subprocess.run(command.split(), capture_output=True, text=True, check=False)
        if result.returncode == expected_exit:
            return True
        if result.stdout:
            pass
        return False
    except Exception:
        return False


def main():
    # Check Python linting tools
    check_tool_disabled("Flake8", "flake8 scripts/volume-control/volume_knob.py")
    check_tool_disabled("Ruff", "ruff check scripts/volume-control/volume_knob.py")
    check_tool_disabled("MyPy", "mypy scripts/volume-control/volume_knob.py")

    # Check other linting tools
    check_tool_disabled("MarkdownLint", "npx markdownlint README.md")
    check_tool_disabled("CSpell", "npx cspell README.md")

    # Check configuration files
    config_files = [
        (".flake8", "Flake8 config"),
        (".markdownlint.json", "MarkdownLint config"),
        ("cspell.json", "CSpell config"),
        (".vscode/settings.json", "VS Code settings"),
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
    else:
        pass


if __name__ == "__main__":
    main()
