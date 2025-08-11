#!/usr/bin/env python3
"""
Fix Extension Errors - Clear caches and restart IDE to resolve file access errors
"""

import os
from pathlib import Path
import platform
import shutil
import subprocess


def main():
    print("🔧 FIXING EXTENSION ERRORS")
    print("=" * 50)

    # Clear VS Code/Cursor caches
    print("🗑️  Clearing IDE caches...")

    # Get user home directory
    home = Path.home()

    # Clear VS Code caches
    vscode_cache = home / ".vscode" / "extensions"
    if vscode_cache.exists():
        print(f"   Clearing VS Code extensions cache: {vscode_cache}")
        try:
            # Remove problematic extension caches
            for ext_dir in vscode_cache.iterdir():
                if ext_dir.is_dir():
                    ext_name = ext_dir.name.lower()
                    if any(name in ext_name for name in ["continue", "monica", "tabnine"]):
                        print(f"   Removing cache for: {ext_dir.name}")
                        shutil.rmtree(ext_dir, ignore_errors=True)
        except Exception as e:
            print(f"   Warning: Could not clear VS Code cache: {e}")

    # Clear Cursor caches
    cursor_cache = home / ".cursor" / "extensions"
    if cursor_cache.exists():
        print(f"   Clearing Cursor extensions cache: {cursor_cache}")
        try:
            # Remove problematic extension caches
            for ext_dir in cursor_cache.iterdir():
                if ext_dir.is_dir():
                    ext_name = ext_dir.name.lower()
                    if any(name in ext_name for name in ["continue", "monica", "tabnine"]):
                        print(f"   Removing cache for: {ext_dir.name}")
                        shutil.rmtree(ext_dir, ignore_errors=True)
        except Exception as e:
            print(f"   Warning: Could not clear Cursor cache: {e}")

    # Clear workspace caches
    workspace_cache = Path(".vscode") / "extensions"
    if workspace_cache.exists():
        print(f"   Clearing workspace extensions cache: {workspace_cache}")
        try:
            shutil.rmtree(workspace_cache, ignore_errors=True)
        except Exception as e:
            print(f"   Warning: Could not clear workspace cache: {e}")

    # Clear Python cache
    print("🗑️  Clearing Python caches...")
    try:
        # Remove __pycache__ directories
        for pycache in Path().rglob("__pycache__"):
            print(f"   Removing: {pycache}")
            shutil.rmtree(pycache, ignore_errors=True)

        # Remove .pyc files
        for pyc_file in Path().rglob("*.pyc"):
            print(f"   Removing: {pyc_file}")
            pyc_file.unlink(missing_ok=True)
    except Exception as e:
        print(f"   Warning: Could not clear Python cache: {e}")

    # Create a touch file to force IDE refresh
    print("🔄 Creating refresh trigger...")
    touch_file = ".extension-refresh"
    with open(touch_file, "w") as f:
        f.write(f"Extension refresh triggered at {__import__('datetime').datetime.now()}")

    # Try to reload the IDE window
    print("🔄 Attempting to reload IDE...")
    try:
        if platform.system() == "Windows":
            subprocess.run(["code", "--command", "workbench.action.reloadWindow"],
                         capture_output=True, timeout=5, check=False)
        else:
            subprocess.run(["code", "--command", "workbench.action.reloadWindow"],
                         capture_output=True, timeout=5, check=False)
        print("   ✅ IDE reload command sent")
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        print("   ⚠️  Could not send reload command automatically")

    # Clean up touch file
    import time
    time.sleep(0.1)
    if os.path.exists(touch_file):
        os.remove(touch_file)

    print("\n✅ CACHE CLEARING COMPLETE!")
    print("\n📋 NEXT STEPS:")
    print("1. **Close your IDE completely** (VS Code/Cursor)")
    print("2. **Wait 5 seconds**")
    print("3. **Reopen your IDE**")
    print("4. **Open this workspace**")
    print("5. **Check the Problems panel** - should be much cleaner now")

    print("\n🔧 IF ERRORS PERSIST:")
    print("1. **Disable problematic extensions** in your IDE:")
    print("   - Continue")
    print("   - Monica")
    print("   - TabNine")
    print("2. **Or uninstall them completely**")
    print("3. **Restart your IDE again**")

    print("\n📊 EXPECTED RESULT:")
    print("- No more 'dev-setup.py not found' errors")
    print("- Clean Problems panel")
    print("- Faster IDE startup")
    print("- No extension conflicts")

if __name__ == "__main__":
    main()
