#!/usr/bin/env python3
"""
Configuration loader for volume control system.
Loads tool configurations and applies appropriate settings based on volume level.
"""

import json
from pathlib import Path
from typing import Any


class VolumeConfigLoader:
    """Loads and applies tool configurations based on volume levels"""

    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(__file__).parent / config_dir
        self.tools = {}
        self.load_all_configs()

    def load_all_configs(self):
        """Load all tool configuration files"""
        if not self.config_dir.exists():
            print(f"Config directory {self.config_dir} not found")
            return

        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    tool_name = config.get("tool", config_file.stem)
                    self.tools[tool_name] = config
                    print(f"Loaded config for {tool_name}")
            except Exception as e:
                print(f"Error loading {config_file}: {e}")

    def get_settings_for_volume(self, volume: int) -> dict[str, Any]:
        """Get combined settings for all tools at the specified volume level"""
        combined_settings = {}

        for tool_name, config in self.tools.items():
            tool_settings = self.get_tool_settings_for_volume(tool_name, volume)
            combined_settings.update(tool_settings)

        return combined_settings

    def get_tool_settings_for_volume(
        self, tool_name: str, volume: int
    ) -> dict[str, Any]:
        """Get settings for a specific tool at the given volume level"""
        if tool_name not in self.tools:
            return {}

        config = self.tools[tool_name]
        activation_levels = config.get("activation_levels", {})

        # Find the highest activation level that is <= volume
        applicable_level = None
        for level_str in activation_levels.keys():
            level = int(level_str)
            if level <= volume:
                if applicable_level is None or level > applicable_level:
                    applicable_level = level

        if applicable_level is None:
            return {}

        level_config = activation_levels[str(applicable_level)]
        return level_config.get("settings", {})

    def get_active_tools(self, volume: int) -> list[str]:
        """Get list of tools that should be active at the given volume level"""
        active_tools = []

        for tool_name, config in self.tools.items():
            activation_levels = config.get("activation_levels", {})

            # Check if any level <= volume has enabled: true
            for level_str in activation_levels.keys():
                level = int(level_str)
                if level <= volume:
                    level_config = activation_levels[level_str]
                    if level_config.get("enabled", False):
                        active_tools.append(tool_name)
                        break

        return active_tools

    def get_activation_summary(self, volume: int) -> dict[str, Any]:
        """Get a summary of what's activated at the given volume level"""
        summary = {
            "volume": volume,
            "active_tools": self.get_active_tools(volume),
            "tool_details": {},
        }

        for tool_name in self.tools.keys():
            is_active = tool_name in summary["active_tools"]
            settings_count = len(self.get_tool_settings_for_volume(tool_name, volume))

            summary["tool_details"][tool_name] = {
                "active": is_active,
                "settings_applied": settings_count,
                "description": self.tools[tool_name].get(
                    "description", "No description"
                ),
            }

        return summary


def main():
    """Test the configuration loader"""
    loader = VolumeConfigLoader()

    # Test different volume levels
    test_volumes = [0, 50, 200, 500, 1000]

    for volume in test_volumes:
        print(f"\n=== VOLUME {volume} ===")
        summary = loader.get_activation_summary(volume)

        print(f"Active tools: {', '.join(summary['active_tools'])}")

        for tool, details in summary["tool_details"].items():
            status = "ACTIVE" if details["active"] else "inactive"
            print(f"  {tool}: {status} ({details['settings_applied']} settings)")


if __name__ == "__main__":
    main()
