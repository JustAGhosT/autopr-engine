#!/usr/bin/env python3
"""
Volume Control Status Utility

Shows current status of both dev and commit volume knobs
"""

import sys
from pathlib import Path

# Ensure we can import from current directory
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import VolumeConfigLoader
from volume_knob import VolumeKnob


def main():
    print("AUTOPR VOLUME CONTROL STATUS")
    print("=" * 50)

    # Create knobs
    dev_knob = VolumeKnob("dev")
    commit_knob = VolumeKnob("commit")
    loader = VolumeConfigLoader()

    # Show current status
    print("CURRENT VOLUME SETTINGS:")
    print(f"  Dev Volume:    {dev_knob.get_volume()}/1000 - {dev_knob.get_volume_description()}")
    print(
        f"  Commit Volume: {commit_knob.get_volume()}/1000 - {commit_knob.get_volume_description()}"
    )

    print("\nACTIVE TOOLS:")
    dev_tools = loader.get_active_tools(dev_knob.get_volume())
    commit_tools = loader.get_active_tools(commit_knob.get_volume())

    print(f"  Dev Environment:   {', '.join(dev_tools) if dev_tools else 'None'}")
    print(f"  Commit Checks:     {', '.join(commit_tools) if commit_tools else 'None'}")

    print("\nCONFIGURATION FILES:")
    dev_config = Path("../../.volume-dev.json")
    commit_config = Path("../../.volume-commit.json")

    print(f"  Dev config:    {'YES' if dev_config.exists() else 'NO'} {dev_config}")
    print(f"  Commit config: {'YES' if commit_config.exists() else 'NO'} {commit_config}")

    print("\nVOLUME KNOB USAGE:")
    print("  Set dev volume:      python scripts/volume.py dev <0-1000>")
    print("  Set commit volume:   python scripts/volume.py commit <0-1000>")
    print("  Increase dev:        python scripts/volume.py dev up [steps]")
    print("  Increase commit:     python scripts/volume.py commit up [steps]")
    print("  Decrease dev:        python scripts/volume.py dev down [steps]")
    print("  Decrease commit:     python scripts/volume.py commit down [steps]")
    print("  Show status:         python scripts/volume-control/status.py")

    print("\nEXAMPLE SCENARIOS:")
    print("  Quiet coding:        dev=50, commit=200   (light IDE, basic commit checks)")
    print("  Development mode:    dev=200, commit=500  (basic IDE, standard commit checks)")
    print("  Production ready:    dev=500, commit=1000 (full IDE, maximum commit checks)")
    print("  Complete silence:    dev=0, commit=0     (no IDE noise, no commit checks)")


if __name__ == "__main__":
    main()
