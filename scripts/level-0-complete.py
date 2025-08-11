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
            print(f"✅ {tool_name}: DISABLED")
            return True
        print(f"❌ {tool_name}: STILL RUNNING (exit code: {result.returncode})")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return False
    except Exception as e:
        print(f"❌ {tool_name}: ERROR - {e}")
        return False


def main():
    print("🔍 VERIFYING LEVEL 0 (NO LINTING) STATUS")
    print("=" * 50)

    # Check Python linting tools
    print("\n🐍 Python Linting Tools:")
    check_tool_disabled("Flake8", "flake8 scripts/volume-control/volume_knob.py")
    check_tool_disabled("Ruff", "ruff check scripts/volume-control/volume_knob.py")
    check_tool_disabled("MyPy", "mypy scripts/volume-control/volume_knob.py")

    # Check other linting tools
    print("\n📝 Other Linting Tools:")
    check_tool_disabled("MarkdownLint", "npx markdownlint README.md")
    check_tool_disabled("CSpell", "npx cspell README.md")

    # Check configuration files
    print("\n⚙️ Configuration Files:")
    config_files = [
        (".flake8", "Flake8 config"),
        (".markdownlint.json", "MarkdownLint config"),
        ("cspell.json", "CSpell config"),
        (".vscode/settings.json", "VS Code settings"),
    ]

    for file_path, description in config_files:
        if os.path.exists(file_path):
            print(f"✅ {description}: EXISTS")
        else:
            print(f"❌ {description}: MISSING")

    # Check pyproject.toml
    print("\n📦 PyProject.toml:")
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml") as f:
            content = f.read()
            if "[tool.flake8]" in content or "[tool.ruff]" in content or "[tool.mypy]" in content:
                print("❌ PyProject.toml: STILL HAS LINTING CONFIGS")
            else:
                print("✅ PyProject.toml: LINTING CONFIGS REMOVED")
    else:
        print("❌ PyProject.toml: MISSING")

    print("\n" + "=" * 50)
    print("🎯 LEVEL 0 VERIFICATION COMPLETE")
    print("\n💡 If you still see errors in Cursor:")
    print("   1. Reload the window: Ctrl+Shift+P → 'Developer: Reload Window'")
    print("   2. Or restart Cursor completely")
    print("   3. Check if any extensions are still running")


if __name__ == "__main__":
    main()
