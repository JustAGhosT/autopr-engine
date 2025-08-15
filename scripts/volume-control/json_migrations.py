#!/usr/bin/env python3
"""
JSON-Based Volume Control Migrations

Migration system using JSON configuration files for each tool.
"""

import json
from pathlib import Path
from typing import Any


class JSONMigrations:
    """JSON-based migration system for volume levels"""

    def __init__(self):
        self.config_dir = Path(__file__).parent / "configs"
        self.configs = self._load_configs()

    def _load_configs(self) -> dict[str, dict]:
        """Load all JSON configuration files"""
        configs = {}

        for config_file in self.config_dir.glob("*.json"):
            tool_name = config_file.stem
            with open(config_file) as f:
                configs[tool_name] = json.load(f)

        return configs

    def get_level_config(self, tool: str, volume: int) -> dict[str, Any] | None:
        """Get configuration for a specific tool and volume level"""
        if tool not in self.configs:
            return None

        tool_configs = self.configs[tool]

        # Find the closest level
        if str(volume) in tool_configs:
            return tool_configs[str(volume)]

        # For volumes between defined levels, find the closest one
        defined_levels = [int(level) for level in tool_configs]
        defined_levels.sort()

        if volume <= defined_levels[0]:
            return tool_configs[str(defined_levels[0])]
        if volume >= defined_levels[-1]:
            return tool_configs[str(defined_levels[-1])]
        # Find the closest level
        closest_level = min(defined_levels, key=lambda x: abs(x - volume))
        return tool_configs[str(closest_level)]

    def migrate_to_level(self, volume: int, knob_type: str) -> dict[str, Any]:
        """Migrate to a specific volume level"""
        result = {"volume": volume, "checks": [], "configs": {}}

        if knob_type == "dev":
            # Load dev-specific configurations
            vscode_config = self.get_level_config("vscode", volume)
            ruff_config = self.get_level_config("ruff", volume)
            pyright_config = self.get_level_config("pyright", volume)

            result["configs"]["vscode"] = vscode_config
            result["configs"]["ruff"] = ruff_config
            result["configs"]["pyright"] = pyright_config

            # Build checks list
            if ruff_config and ruff_config.get("enabled", False):
                result["checks"].append("syntax_errors")
            if pyright_config and pyright_config.get("enabled", False):
                result["checks"].append("type_checking")

        elif knob_type == "commit":
            # Load commit-specific configurations
            pre_commit_config = self.get_level_config("pre_commit", volume)
            result["configs"]["pre_commit"] = pre_commit_config

            # Build checks list
            if pre_commit_config and pre_commit_config.get("enabled", False):
                hooks = pre_commit_config.get("hooks", {})
                for hook_name in hooks:
                    if hook_name not in ["all_stages", "other_tools", "description"]:
                        result["checks"].append(f"{hook_name}_check")

        return result

    def get_vscode_settings(self, volume: int) -> dict[str, Any]:
        """Get VS Code settings for a volume level"""
        config = self.get_level_config("vscode", volume)
        return config.get("settings", {}) if config else {}

    def get_ruff_config(self, volume: int) -> str | None:
        """Get Ruff TOML configuration for a volume level"""
        config = self.get_level_config("ruff", volume)
        if not config or not config.get("enabled", False):
            return None

        ruff_config = config.get("config", {})
        if not ruff_config:
            return None

        # Convert JSON config to TOML format
        toml_lines = [f"# {config['name']} MODE - Volume {volume}/1000"]
        toml_lines.append("[tool.ruff]")

        if "select" in ruff_config:
            toml_lines.append(f"select = {ruff_config['select']}")
        if "ignore" in ruff_config:
            toml_lines.append(f"ignore = {ruff_config['ignore']}")
        if "line_length" in ruff_config:
            toml_lines.append(f"line-length = {ruff_config['line_length']}")
        if "max_errors" in ruff_config:
            toml_lines.append(f"max-errors = {ruff_config['max_errors']}")

        if "format" in ruff_config:
            toml_lines.append("")
            toml_lines.append("[tool.ruff.format]")
            format_config = ruff_config["format"]
            if "quote_style" in format_config:
                toml_lines.append(f'quote-style = "{format_config['quote_style']}"')
            if "indent_style" in format_config:
                toml_lines.append(f'indent-style = "{format_config['indent_style']}"')
            if "line_ending" in format_config:
                toml_lines.append(f'line-ending = "{format_config['line_ending']}"')

        return "\n".join(toml_lines)

    def get_pyright_config(self, volume: int) -> str | None:
        """Get Pyright JSON configuration for a volume level"""
        config = self.get_level_config("pyright", volume)
        if not config or not config.get("enabled", False):
            return None

        pyright_config = config.get("config", {})
        if not pyright_config:
            return None

        return json.dumps(pyright_config, indent=4)

    def get_pre_commit_config(self, volume: int) -> dict[str, Any]:
        """Get pre-commit configuration for a volume level"""
        config = self.get_level_config("pre_commit", volume)
        return config.get("hooks", {}) if config else {}


# Global instance
json_migrations = JSONMigrations()
