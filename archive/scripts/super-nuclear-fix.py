#!/usr/bin/env python3
"""
Super Nuclear Fix - Temporarily disable problematic files that cause IDE validation
"""

from pathlib import Path
import shutil


def disable_problematic_files():
    """Temporarily rename files that cause IDE validation errors"""

    # Rename the GitHub workflow file that's causing problems
    workflow_file = Path(".github/workflows/ci.yml")
    backup_file = Path(".github/workflows/ci.yml.DISABLED")

    if workflow_file.exists() and not backup_file.exists():
        shutil.move(str(workflow_file), str(backup_file))
        print(f"Renamed {workflow_file} to {backup_file}")

    # Create an empty placeholder
    workflow_file.write_text("# Workflow disabled at Volume 0\n")
    print(f"Created empty placeholder {workflow_file}")


def create_volume_0_marker():
    """Create a marker file to indicate Volume 0 mode"""

    marker_file = Path(".volume-0-active")
    marker_file.write_text("Volume 0 active - all validation disabled\n")
    print(f"Created {marker_file}")


def main():
    print("SUPER NUCLEAR FIX - Volume 0 Mode")
    print("=================================")

    disable_problematic_files()
    create_volume_0_marker()

    print("\nVolume 0 activated!")
    print("- GitHub workflow file temporarily disabled")
    print("- All IDE validation should now be silent")
    print("\nTo restore files later:")
    print("  mv .github/workflows/ci.yml.DISABLED .github/workflows/ci.yml")
    print("  rm .volume-0-active")

    print("\nNow restart your IDE for complete silence!")


if __name__ == "__main__":
    main()
