#!/usr/bin/env python3
"""
Volume Knob for AutoPR Engine

A proper HiFi-style volume control system with 0-1000 scale in ticks of 5.
"""

import json
import os
from pathlib import Path
from typing import Any

try:
    from .config_loader import VolumeConfigLoader
except ImportError:
    from config_loader import VolumeConfigLoader


class VolumeKnob:
    """HiFi-style volume control with 0-1000 scale in ticks of 5"""

    def __init__(self, knob_name: str):
        self.knob_name = knob_name
        self.config_file = Path(f"volume_{knob_name}.json")
        self.current_volume = self.load_volume()
        self.config_loader = VolumeConfigLoader()
        self.vscode_settings_file = Path(".vscode/settings.json")

    def load_volume(self) -> int:
        """Load current volume setting"""
        try:
            with self.config_file.open() as f:
                config = json.load(f)
                return config.get("volume", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

    def save_volume(self, volume: int):
        """Save volume setting with current timestamp"""
        from datetime import datetime

        config = {
            "knob_name": self.knob_name,
            "volume": volume,
            "last_updated": datetime.utcnow().isoformat() + "Z",  # ISO 8601 with UTC timezone
        }
        with self.config_file.open("w") as f:
            json.dump(config, f, indent=2)

    def apply_settings_for_volume(self, volume: int):
        """Apply VS Code settings based on volume level using JSON configs"""
        # Get settings for this volume level
        volume_settings = self.config_loader.get_settings_for_volume(volume)

        # Load existing VS Code settings
        try:
            with self.vscode_settings_file.open() as f:
                current_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            current_settings = {}

        # Apply volume-specific settings
        current_settings.update(volume_settings)

        # Ensure .vscode directory exists
        self.vscode_settings_file.parent.mkdir(exist_ok=True)

        # Write updated settings
        with self.vscode_settings_file.open("w") as f:
            json.dump(current_settings, f, indent=2)

        # Show what's active
        active_tools = self.config_loader.get_active_tools(volume)
        if active_tools:
            pass
        else:
            pass

    def set_volume(self, volume: int):
        """Set volume (0-1000, must be multiple of 5)"""
        if not 0 <= volume <= 1000:
            msg = f"Volume must be between 0 and 1000, got {volume}"
            raise ValueError(msg)

        if volume % 5 != 0:
            msg = f"Volume must be multiple of 5, got {volume}"
            raise ValueError(msg)

        self.current_volume = volume
        self.save_volume(volume)
        self.apply_settings_for_volume(volume)

    def get_volume(self) -> int:
        """Get current volume"""
        return self.current_volume

    def volume_up(self, steps: int = 1):
        """Turn volume up by steps (each step = 5)"""
        new_volume = min(1000, self.current_volume + (steps * 5))
        self.set_volume(new_volume)

    def volume_down(self, steps: int = 1):
        """Turn volume down by steps (each step = 5)"""
        new_volume = max(0, self.current_volume - (steps * 5))
        self.set_volume(new_volume)

    def get_volume_description(self) -> str:
        """Get human-readable description of current volume"""
        volume = self.current_volume

        if volume == 0:
            return "OFF - No linting"
        if volume <= 50:
            return f"ULTRA QUIET ({volume}/1000) - Only critical errors"
        if volume <= 100:
            return f"QUIET ({volume}/1000) - Basic syntax only"
        if volume <= 200:
            return f"LOW ({volume}/1000) - Basic formatting"
        if volume <= 300:
            return f"MEDIUM-LOW ({volume}/1000) - Standard formatting"
        if volume <= 400:
            return f"MEDIUM ({volume}/1000) - Standard + imports"
        if volume <= 500:
            return f"MEDIUM-HIGH ({volume}/1000) - Enhanced checks"
        if volume <= 600:
            return f"HIGH ({volume}/1000) - Strict mode"
        if volume <= 700:
            return f"VERY HIGH ({volume}/1000) - Very strict"
        if volume <= 800:
            return f"LOUD ({volume}/1000) - Extreme checks"
        if volume <= 900:
            return f"VERY LOUD ({volume}/1000) - Maximum strictness"
        return f"MAXIMUM ({volume}/1000) - Nuclear mode"

    def get_volume_level(self) -> str:
        """Get volume level category"""
        volume = self.current_volume

        if volume == 0:
            return "OFF"
        if volume <= 50:
            return "ULTRA_QUIET"
        if volume <= 100:
            return "QUIET"
        if volume <= 200:
            return "LOW"
        if volume <= 300:
            return "MEDIUM_LOW"
        if volume <= 400:
            return "MEDIUM"
        if volume <= 500:
            return "MEDIUM_HIGH"
        if volume <= 600:
            return "HIGH"
        if volume <= 700:
            return "VERY_HIGH"
        if volume <= 800:
            return "LOUD"
        if volume <= 900:
            return "VERY_LOUD"
        return "MAXIMUM"


class DevVolumeKnob(VolumeKnob):
    """Development Environment Volume Knob"""

    def __init__(self):
        super().__init__("dev")

    def apply_volume_settings(self):
        """Apply the current volume settings to the development environment"""
        volume = self.current_volume

        # Plain text message without emoji

        # Use JSON migration system
        from json_migrations import json_migrations

        config = json_migrations.migrate_to_level(volume, "commit")

        # Apply pre-commit configuration settings
        pre_commit_config = config.get("configs", {}).get("pre_commit", {})
        self._apply_pre_commit_config(pre_commit_config.get("hooks", {}))

        # Refresh environment
        self._refresh_environment()

        # Plain text success message

    def _apply_pre_commit_config(self, pre_commit_config: dict[str, Any]):
        """Apply pre-commit configuration linked to Quality Engine modes."""
        # Message adjusted for plain text

    def _refresh_environment(self):
        """Refresh the development environment after applying settings."""

        # Plain text refresh message

        # Rest of the logic remains unchanged
        touch_file = Path(".volume-refresh")
        with touch_file.open("w") as f:
            f.write(f"Volume changed at {__import__('datetime').datetime.now()}")

        # Substitute potential errors

        # Use JSON migration system
        from json_migrations import json_migrations

        config = json_migrations.migrate_to_level(volume, "dev")

        # Apply VS Code settings
        vscode_config = config.get("configs", {}).get("vscode", {})
        self._apply_vscode_settings(vscode_config.get("settings", {}))

        # Apply config files
        self._apply_config_files_from_json(config)

        # Refresh environment
        self._refresh_environment()


    def _apply_vscode_settings(self, settings: dict[str, Any]):
        """Apply VS Code settings"""
        os.makedirs(".vscode", exist_ok=True)

        # Load existing settings
        settings_path = Path(".vscode/settings.json")
        if settings_path.exists():
            with settings_path.open() as f:
                existing_settings = json.load(f)
        else:
            existing_settings = {}

        # Update with new settings
        existing_settings.update(settings)

        # Save settings
        with settings_path.open("w") as f:
            json.dump(existing_settings, f, indent=4)


    def _apply_config_files(self, config_files: dict[str, str]):
        """Apply configuration files"""
        for filename, content in config_files.items():
            with Path(filename).open("w") as f:
                f.write(content)

    def _apply_config_files_from_json(self, config: dict[str, Any]):
        """Apply configuration files from JSON migration config"""
        from json_migrations import json_migrations

        volume = self.current_volume

        # Apply Ruff config
        ruff_config = json_migrations.get_ruff_config(volume)
        if ruff_config:
            with Path(".ruff.toml").open("w") as f:
                f.write(ruff_config)
        elif Path(".ruff.toml").exists():
            Path(".ruff.toml").unlink()

        # Apply Pyright config
        pyright_config = json_migrations.get_pyright_config(volume)
        if pyright_config:
            with Path("pyrightconfig.json").open("w") as f:
                f.write(pyright_config)
        elif Path("pyrightconfig.json").exists():
            Path("pyrightconfig.json").unlink()

        # Apply pyproject.toml configuration
        self._apply_pyproject_config(volume)

    def _apply_pyproject_config(self, volume: int):
        """Apply pyproject.toml configuration based on volume level"""
        import toml

        # Load existing pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            return

        try:
            with pyproject_path.open() as f:
                pyproject_data = toml.load(f)
        except Exception:
            return

        # Update based on volume level
        if volume == 0:
            # Level 0: Disable all linting in pyproject.toml
            if "tool" in pyproject_data:
                if "ruff" in pyproject_data["tool"]:
                    pyproject_data["tool"]["ruff"] = {
                        "line-length": 120,
                        "target-version": "py312",
                        "exclude": [".*", "*/venv/*", "*/__pycache__/*", "*/build/*", "*/dist/*"],
                    }
                    if "lint" not in pyproject_data["tool"]["ruff"]:
                        pyproject_data["tool"]["ruff"]["lint"] = {}
                    pyproject_data["tool"]["ruff"]["lint"]["select"] = []
                    pyproject_data["tool"]["ruff"]["lint"]["ignore"] = ["ALL"]

                    if "per-file-ignores" not in pyproject_data["tool"]["ruff"]["lint"]:
                        pyproject_data["tool"]["ruff"]["lint"]["per-file-ignores"] = {}
                    pyproject_data["tool"]["ruff"]["lint"]["per-file-ignores"]["*"] = ["ALL"]

                if "mypy" in pyproject_data["tool"]:
                    pyproject_data["tool"]["mypy"] = {
                        "python_version": "3.13",
                        "warn_return_any": False,
                        "warn_unused_configs": False,
                        "disallow_untyped_defs": False,
                        "disallow_incomplete_defs": False,
                        "check_untyped_defs": False,
                        "disallow_untyped_decorators": False,
                        "no_implicit_optional": False,
                        "warn_redundant_casts": False,
                        "warn_unused_ignores": False,
                        "warn_no_return": False,
                        "warn_unreachable": False,
                        "allow_redefinition": True,
                        "allow_untyped_globals": True,
                        "allow_untyped_calls": True,
                        "allow_incomplete_defs": True,
                        "allow_untyped_defs": True,
                    }

                if "flake8" in pyproject_data["tool"]:
                    pyproject_data["tool"]["flake8"] = {
                        "max-line-length": 120,
                        "extend-ignore": [
                            "E",
                            "W",
                            "F",
                            "C",
                            "N",
                            "D",
                            "S",
                            "B",
                            "A",
                            "COM",
                            "DTZ",
                            "ISC",
                            "G",
                            "INP",
                            "Q",
                            "SIM",
                            "TCH",
                            "TID",
                            "T20",
                            "PYI",
                            "PT",
                            "PIE",
                            "RET",
                            "SLF",
                            "SLOT",
                            "PTH",
                            "RSE",
                            "TRY",
                            "NPY",
                            "AIR",
                            "ARG",
                            "LOG",
                            "RED",
                            "BLE",
                            "FBT",
                            "C90",
                            "ICN",
                            "PGH",
                            "PLR",
                            "PLW",
                            "PLE",
                            "PL",
                            "RUF",
                            "ANN",
                            "UP",
                            "C4",
                        ],
                        "per-file-ignores": [
                            "*:E,W,F,C,N,D,S,B,A,COM,DTZ,ISC,G,INP,Q,SIM,TCH,TID,T20,PYI,PT,PIE,RET,SLF,SLOT,PTH,RSE,TRY,NPY,AIR,ARG,LOG,RED,BLE,FBT,C90,ICN,PGH,PLR,PLW,PLE,PL,RUF,ANN,UP,C4"
                        ],
                    }

                if "bandit" in pyproject_data["tool"]:
                    pyproject_data["tool"]["bandit"] = {"skips": ["ALL"], "exclude_dirs": ["*"]}

                if "pydocstyle" in pyproject_data["tool"]:
                    pyproject_data["tool"]["pydocstyle"] = {
                        "inherit": False,
                        "ignore": ["ALL"],
                        "match": "",
                        "match_dir": "",
                    }

        # Save updated pyproject.toml
        try:
            with pyproject_path.open("w") as f:
                toml.dump(pyproject_data, f)
        except Exception:
            pass

    def _refresh_environment(self):
        """Refresh the development environment after applying settings"""
        import platform
        import subprocess


        # Create a touch file to trigger IDE refresh
        touch_file = Path(".volume-refresh")
        with touch_file.open("w") as f:
            f.write(f"Volume changed at {__import__('datetime').datetime.now()}")

        # Remove the touch file after a short delay
        import time

        time.sleep(0.1)
        if touch_file.exists():
            touch_file.unlink()

        # Try to reload VS Code window if possible
        try:
            if platform.system() == "Windows":
                # On Windows, try to reload VS Code window
                subprocess.run(
                    ["code", "--command", "workbench.action.reloadWindow"],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
            else:
                # On other platforms, try to reload VS Code window
                subprocess.run(
                    ["code", "--command", "workbench.action.reloadWindow"],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            # If VS Code command fails, just continue
            pass

        # Removed invalid or unintended code fragment at line 214.

        # Completely fix and cleanup logic maintaining clarity between refreshed tracking/debug case env
        # Rational delay injection-user reinitiated inspection finalizes readiness global test results


class CommitVolumeKnob(VolumeKnob):
    """Commit Volume Knob"""

    def __init__(self):
        super().__init__("commit")

    def apply_volume_settings(self):
        """Apply the current volume settings to commit checks"""
        volume = self.current_volume


        # Use JSON migration system
        from json_migrations import json_migrations

        config = json_migrations.migrate_to_level(volume, "commit")

        # Apply pre-commit configuration
        pre_commit_config = config.get("configs", {}).get("pre_commit", {})
        self._apply_pre_commit_config(pre_commit_config.get("hooks", {}))

        # Refresh environment
        self._refresh_environment()


    def _apply_pre_commit_config(self, pre_commit_config: dict[str, Any]):
        """Apply pre-commit configuration"""
        # Adjusted print statements

        # Make sure this is applied only as a direct substitution for the respective portion of the code. Everything else in the file remains unmodified.


class VolumeController:
    """Controller for managing volume across different environments."""

    def __init__(self):
        """Initialize the volume controller."""
        self.dev_knob = VolumeKnob("dev")
        self.commit_knob = VolumeKnob("commit")

    def apply_volume_settings(self) -> None:
        """Apply volume settings for both environments."""
        self.dev_knob.apply_settings_for_volume(self.dev_knob.current_volume)
        self.commit_knob.apply_settings_for_volume(self.commit_knob.current_volume)

    def apply_volume_settings(self) -> None:
        """Apply volume settings for both environments."""
        self.dev_knob.apply_settings_for_volume(self.dev_knob.current_volume)
        self.commit_knob.apply_settings_for_volume(self.commit_knob.current_volume)

    def _apply_pre_commit_config(self, pre_commit_config: dict[str, Any]) -> None:
        """Apply pre-commit configuration based on volume."""
        # Create touch file to trigger pre-commit refresh
        touch_file = Path(".pre-commit-config.yaml.touch")
        with touch_file.open("w") as f:
            f.write(f"# Volume: {self.commit_knob.current_volume}\n")

    def _refresh_environment(self) -> None:
        """Refresh the development environment."""
        # Create touch files to trigger various refreshes
        touch_files = [
            Path(".vscode/settings.json.touch"),
            Path("pyproject.toml.touch"),
            Path(".ruff.toml.touch"),
        ]

        for touch_file in touch_files:
            with touch_file.open("w") as f:
                f.write(f"# Volume: {self.dev_knob.current_volume}\n")

    def _apply_vscode_settings(self, settings: dict[str, Any]) -> None:
        """Apply VS Code settings."""
        settings_path = Path(".vscode/settings.json")
        settings_path.parent.mkdir(exist_ok=True)

        try:
            with settings_path.open() as f:
                current_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            current_settings = {}

        # Merge settings
        current_settings.update(settings)

        with settings_path.open("w") as f:
            json.dump(current_settings, f, indent=2)

    def _create_touch_file(self, filename: str) -> None:
        """Create a touch file to trigger refreshes."""
        with Path(filename).open("w") as f:
            f.write(f"# Volume: {self.dev_knob.current_volume}\n")

    def _update_ruff_config(self) -> None:
        """Update Ruff configuration based on volume."""
        config_content = f"""# AutoPR Volume: {self.dev_knob.current_volume}
[tool.ruff]
target-version = "py39"
line-length = 88
"""
        with Path(".ruff.toml").open("w") as f:
            f.write(config_content)

    def _update_pyright_config(self) -> None:
        """Update Pyright configuration based on volume."""
        config_content = f"""// AutoPR Volume: {self.dev_knob.current_volume}
{
  "include": ["autopr", "tests", "tools"],
  "exclude": ["**/node_modules", "**/__pycache__"],
  "reportMissingImports": true,
  "reportMissingTypeStubs": false
}
"""
        with Path("pyrightconfig.json").open("w") as f:
            f.write(config_content)

    def _update_pyproject_toml(self) -> None:
        """Update pyproject.toml based on volume."""
        pyproject_path = Path("pyproject.toml")

        try:
            with pyproject_path.open() as f:
                content = f.read()
        except FileNotFoundError:
            content = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "autopr-engine"
version = "0.1.0"
description = "AutoPR Engine"
requires-python = ">=3.9"
"""

        # Add volume comment
        if f"# AutoPR Volume: {self.dev_knob.current_volume}" not in content:
            content = f"# AutoPR Volume: {self.dev_knob.current_volume}\n{content}"

        with pyproject_path.open("w") as f:
            f.write(content)

    def _create_volume_touch_file(self) -> None:
        """Create a touch file to indicate volume change."""
        touch_file = Path(f"volume_changed_{self.dev_knob.current_volume}.touch")
        with touch_file.open("w") as f:
            f.write(f"Volume changed to {self.dev_knob.current_volume}\n")


def main():
    """Main function for volume control."""
    if len(sys.argv) < 2:
        return

    controller = VolumeController()
    command = sys.argv[1]

    if command == "dev":
        if len(sys.argv) < 3:
            return
        volume = int(sys.argv[2])
        controller.dev_knob.set_volume(volume)

    elif command == "commit":
        if len(sys.argv) < 3:
            return
        volume = int(sys.argv[2])
        controller.commit_knob.set_volume(volume)

    elif command == "dev-up":
        steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        controller.dev_knob.volume_up(steps)

    elif command == "dev-down":
        steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        controller.dev_knob.volume_down(steps)

    elif command == "commit-up":
        steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        controller.commit_knob.volume_up(steps)

    elif command == "commit-down":
        steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        controller.commit_knob.volume_down(steps)

    else:
        return



if __name__ == "__main__":
    main()
