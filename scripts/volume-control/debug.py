#!/usr/bin/env python3
"""
Debug script to show exactly what settings are applied at different volumes
"""

from pathlib import Path
import sys

# Add volume-control to path
volume_control_path = Path(__file__).parent / "volume-control"
sys.path.insert(0, str(volume_control_path))

from config_loader import VolumeConfigLoader


def main():

    loader = VolumeConfigLoader()

    volumes_to_test = [0, 50]

    for volume in volumes_to_test:

        settings = loader.get_settings_for_volume(volume)
        loader.get_active_tools(volume)


        # Show important settings
        important_settings = [
            "python.enabled",
            "python.languageServer",
            "git.enabled",
            "problems.decorations.enabled",
            "files.associations",
        ]

        for setting in important_settings:
            settings.get(setting, "NOT SET")

        for _key, _value in sorted(settings.items()):
            pass


if __name__ == "__main__":
    main()
