#!/usr/bin/env python3
"""
Main Volume Control for AutoPR Engine

HiFi-style volume control with 0-1000 scale in ticks of 5.
"""

import os
from pathlib import Path
import sys


# Add the volume-control directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from volume_knob import CommitVolumeKnob, DevVolumeKnob


def show_help():
    """Show help information"""
    print("🎛️ AUTOPR VOLUME CONTROL SYSTEM")
    print("=" * 60)
    print("HiFi-style volume control with 0-1000 scale in ticks of 5")
    print("=" * 60)
    print()
    print("🎯 TWO VOLUME KNOBS:")
    print("  dev     - Development Environment Volume (IDE linting)")
    print("  commit  - Commit Volume (pre-commit checks)")
    print()
    print("🎛️ VOLUME LEVELS:")
    print("  0       - OFF (no linting)")
    print("  5-50    - ULTRA QUIET (only critical errors)")
    print("  55-100  - QUIET (basic syntax only)")
    print("  105-200 - LOW (basic formatting)")
    print("  205-300 - MEDIUM-LOW (standard formatting)")
    print("  305-400 - MEDIUM (standard + imports)")
    print("  405-500 - MEDIUM-HIGH (enhanced checks)")
    print("  505-600 - HIGH (strict mode)")
    print("  605-700 - VERY HIGH (very strict)")
    print("  705-800 - LOUD (extreme checks)")
    print("  805-900 - VERY LOUD (maximum strictness)")
    print("  905-1000- MAXIMUM (nuclear mode)")
    print()
    print("🔧 COMMANDS:")
    print("  python main.py dev <0-1000>     - Set dev volume")
    print("  python main.py commit <0-1000>  - Set commit volume")
    print("  python main.py dev up [steps]   - Turn dev volume up")
    print("  python main.py dev down [steps] - Turn dev volume down")
    print("  python main.py commit up [steps]   - Turn commit volume up")
    print("  python main.py commit down [steps] - Turn commit volume down")
    print("  python main.py status           - Show current volumes")
    print("  python main.py autofix          - Autofix current level")
    print("  python main.py help             - Show this help")
    print()
    print("💡 EXAMPLES:")
    print("  python main.py dev 0            - Turn off dev linting")
    print("  python main.py dev 50           - Ultra quiet dev")
    print("  python main.py dev up 2         - Turn dev up 2 steps (10)")
    print("  python main.py commit 0         - Turn off commit checks")
    print("  python main.py commit 100       - Quiet commit checks")
    print("  python main.py autofix          - Fix issues at current level")
    print()
    print("🎯 VOLUME MUST BE MULTIPLE OF 5 (0, 5, 10, 15, ..., 1000)")


def show_status():
    """Show current volume status"""
    dev_knob = DevVolumeKnob()
    commit_knob = CommitVolumeKnob()

    print("🎛️ CURRENT VOLUME STATUS")
    print("=" * 60)
    print(f"Dev Environment Volume: {dev_knob.get_volume()}/1000")
    print(f"  Level: {dev_knob.get_volume_level()}")
    print(f"  Description: {dev_knob.get_volume_description()}")
    print()
    print(f"Commit Volume: {commit_knob.get_volume()}/1000")
    print(f"  Level: {commit_knob.get_volume_level()}")
    print(f"  Description: {commit_knob.get_volume_description()}")
    print()

    # Show recommendations
    if dev_knob.get_volume() == 0:
        print("💡 Dev Volume is OFF - no linting in IDE")
        print("   To start: python main.py dev 50")
    elif dev_knob.get_volume() <= 100:
        print("💡 Dev Volume is QUIET - good for development")
        print("   To increase: python main.py dev up 1")
    elif dev_knob.get_volume() <= 300:
        print("💡 Dev Volume is MEDIUM - balanced linting")
        print("   To adjust: python main.py dev up 1 or down 1")
    else:
        print("💡 Dev Volume is HIGH - strict linting")
        print("   To decrease: python main.py dev down 1")

    if commit_knob.get_volume() == 0:
        print("💡 Commit Volume is OFF - no commit checks")
        print("   To start: python main.py commit 50")
    elif commit_knob.get_volume() <= 100:
        print("💡 Commit Volume is QUIET - minimal commit checks")
        print("   To increase: python main.py commit up 1")
    else:
        print("💡 Commit Volume is ACTIVE - commit checks enabled")
        print("   To adjust: python main.py commit up 1 or down 1")


def autofix_current():
    """Autofix issues at current volume levels"""
    dev_knob = DevVolumeKnob()
    commit_knob = CommitVolumeKnob()

    print("🔧 AUTOFIXING CURRENT VOLUME LEVELS")
    print("=" * 60)

    # Autofix dev volume
    if dev_knob.get_volume() > 0:
        print(f"🔧 Autofixing Dev Volume {dev_knob.get_volume()}/1000")
        print(f"   Level: {dev_knob.get_volume_level()}")
        print(f"   Description: {dev_knob.get_volume_description()}")

        # Run appropriate autofix commands based on level
        level = dev_knob.get_volume_level()
        if level in ["ULTRA_QUIET", "QUIET", "LOW"]:
            print("   Running: ruff check . --fix")
            os.system("ruff check . --fix")
        elif level in ["MEDIUM_LOW", "MEDIUM", "MEDIUM_HIGH"]:
            print("   Running: ruff check . --fix && black .")
            os.system("ruff check . --fix")
            os.system("black .")
        else:
            print("   Running: ruff check . --fix && black .")
            os.system("ruff check . --fix")
            os.system("black .")

    # Autofix commit volume
    if commit_knob.get_volume() > 0:
        print(f"🔧 Autofixing Commit Volume {commit_knob.get_volume()}/1000")
        print(f"   Level: {commit_knob.get_volume_level()}")
        print(f"   Description: {commit_knob.get_volume_description()}")

        # Run pre-commit autofix
        print("   Running: pre-commit run --all-files")
        os.system("pre-commit run --all-files")

    print("✅ Autofix complete!")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_status()
        return

    command = sys.argv[1].lower()

    if command == "help":
        show_help()
        return

    if command == "status":
        show_status()
        return

    if command == "autofix":
        autofix_current()
        return

    if command in ["dev", "commit"]:
        knob_type = command
        knob = DevVolumeKnob() if knob_type == "dev" else CommitVolumeKnob()

        if len(sys.argv) < 3:
            print(f"❌ Missing volume for {knob_type}")
            print(f"Usage: python main.py {knob_type} <0-1000>")
            return

        subcommand = sys.argv[2].lower()

        if subcommand == "up":
            steps = int(sys.argv[3]) if len(sys.argv) >= 4 else 1
            knob.volume_up(steps)
        elif subcommand == "down":
            steps = int(sys.argv[3]) if len(sys.argv) >= 4 else 1
            knob.volume_down(steps)
        else:
            try:
                volume = int(subcommand)
                knob.set_volume(volume)
            except ValueError:
                print(f"❌ Invalid volume: {subcommand}")
                print("Volume must be a number between 0 and 1000 (multiple of 5)")
                return

        # Apply the settings
        knob.apply_volume_settings()

        print(f"\n🎛️ {knob_type.upper()} VOLUME: {knob.get_volume()}/1000")
        print(f"📝 Description: {knob.get_volume_description()}")

        # Show next steps
        if knob.get_volume() > 0:
            print("\n💡 To autofix this level: python main.py autofix")
            print(f"💡 To adjust: python main.py {knob_type} up 1 or down 1")

    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python main.py help' for usage information")


if __name__ == "__main__":
    main()
