#!/usr/bin/env python3
"""
Final Level 0 Fix - Complete IDE Refresh

This script forces a complete refresh of the IDE settings and verifies Level 0 is working
"""

import os
import time


def force_ide_refresh():
    """Force IDE to refresh all settings"""

    print("🔄 FORCING COMPLETE IDE REFRESH")
    print("=" * 50)

    # Create a touch file to force refresh
    touch_file = ".vscode/refresh_trigger.txt"
    with open(touch_file, "w") as f:
        f.write(f"Refresh triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    print("✅ Created refresh trigger file")

    # Remove any cached settings
    cache_dirs = [".vscode/.cache", ".cursor/.cache", ".pytest_cache", "__pycache__"]

    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                import shutil

                shutil.rmtree(cache_dir)
                print(f"✅ Removed cache: {cache_dir}")
            except Exception as e:
                print(f"⚠️ Could not remove {cache_dir}: {e}")

    print("\n🎯 LEVEL 0 CONFIGURATION SUMMARY")
    print("=" * 50)

    # Check all configuration files
    config_files = [
        (".vscode/settings.json", "VS Code Settings"),
        (".flake8", "Flake8 Config"),
        (".markdownlint.json", "MarkdownLint Config"),
        ("cspell.json", "CSpell Config"),
        ("mypy.ini", "MyPy Config"),
    ]

    for file_path, description in config_files:
        if os.path.exists(file_path):
            print(f"✅ {description}: EXISTS")
        else:
            print(f"❌ {description}: MISSING")

    # Check pyproject.toml
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml") as f:
            content = f.read()
            if "[tool.flake8]" in content or "[tool.ruff]" in content or "[tool.mypy]" in content:
                print("❌ PyProject.toml: STILL HAS LINTING CONFIGS")
            else:
                print("✅ PyProject.toml: LINTING CONFIGS REMOVED")

    print("\n🚀 FINAL INSTRUCTIONS")
    print("=" * 50)
    print("1. CLOSE Cursor completely")
    print("2. Delete any remaining cache folders:")
    print("   - .vscode/.cache")
    print("   - .cursor/.cache")
    print("   - __pycache__ folders")
    print("3. RESTART Cursor")
    print("4. Open the project")
    print("5. Check the Problems panel - should show 0 Python linting errors")
    print("\n💡 If you still see errors:")
    print("   - Press Ctrl+Shift+P")
    print("   - Type 'Developer: Reload Window'")
    print("   - Or try 'Python: Restart Language Server'")

    print(f"\n⏰ Refresh triggered at: {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    force_ide_refresh()
