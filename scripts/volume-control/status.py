#!/usr/bin/env python3
"""
Volume Control Status Utility

Shows current status of both dev and commit volume knobs
"""

from pathlib import Path
import sys

# Ensure we can import from current directory
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import VolumeConfigLoader
from volume_knob import VolumeKnob


def main():

    # Create knobs
    dev_knob = VolumeKnob("dev")
    commit_knob = VolumeKnob("commit")
    loader = VolumeConfigLoader()

    # Show current status

    loader.get_active_tools(dev_knob.get_volume())
    loader.get_active_tools(commit_knob.get_volume())


    Path("../../.volume-dev.json")
    Path("../../.volume-commit.json")





if __name__ == "__main__":
    main()
