#!/usr/bin/env python3
"""
Debug script to show exactly what settings are applied at different volumes
"""

import sys
from pathlib import Path

# Add volume-control to path
volume_control_path = Path(__file__).parent / "volume-control"
sys.path.insert(0, str(volume_control_path))

from config_loader import VolumeConfigLoader


def main():
    print("VOLUME SETTINGS DEBUG")
    print("=" * 50)

    loader = VolumeConfigLoader()

    volumes_to_test = [0, 50]

    for volume in volumes_to_test:
        print(f"\n=== VOLUME {volume} SETTINGS ===")

        settings = loader.get_settings_for_volume(volume)
        active_tools = loader.get_active_tools(volume)

        print(f"Active tools: {', '.join(active_tools) if active_tools else 'None'}")
        print(f"Total settings: {len(settings)}")

        # Show important settings
        important_settings = [
            "python.enabled",
            "python.languageServer",
            "git.enabled",
            "problems.decorations.enabled",
            "files.associations",
        ]

        for setting in important_settings:
            value = settings.get(setting, "NOT SET")
            print(f"  {setting}: {value}")

        print("\nAll settings:")
        for key, value in sorted(settings.items()):
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
