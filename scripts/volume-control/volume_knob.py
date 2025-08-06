#!/usr/bin/env python3
"""
Volume Knob for AutoPR Engine

A proper HiFi-style volume control system with 0-1000 scale in ticks of 5.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any
try:
    from .config_loader import VolumeConfigLoader
except ImportError:
    from config_loader import VolumeConfigLoader


class VolumeKnob:
    """HiFi-style volume control with 0-1000 scale in ticks of 5"""
    
    def __init__(self, knob_name: str):
        self.knob_name = knob_name
        self.config_file = f".volume-{knob_name}.json"
        self.current_volume = self.load_volume()
        self.config_loader = VolumeConfigLoader()
        self.vscode_settings_file = Path(".vscode/settings.json")
    
    def load_volume(self) -> int:
        """Load current volume setting"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get('volume', 0)
        return 0
    
    def save_volume(self, volume: int):
        """Save volume setting with current timestamp"""
        from datetime import datetime
        
        config = {
            'knob_name': self.knob_name,
            'volume': volume,
            'last_updated': datetime.utcnow().isoformat() + 'Z'  # ISO 8601 with UTC timezone
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def apply_settings_for_volume(self, volume: int):
        """Apply VS Code settings based on volume level using JSON configs"""
        # Get settings for this volume level
        volume_settings = self.config_loader.get_settings_for_volume(volume)
        
        # Load existing VS Code settings
        if self.vscode_settings_file.exists():
            with open(self.vscode_settings_file, 'r') as f:
                current_settings = json.load(f)
        else:
            current_settings = {}
        
        # Apply volume-specific settings
        current_settings.update(volume_settings)
        
        # Ensure .vscode directory exists
        self.vscode_settings_file.parent.mkdir(exist_ok=True)
        
        # Write updated settings
        with open(self.vscode_settings_file, 'w') as f:
            json.dump(current_settings, f, indent=2)
        
        # Show what's active
        active_tools = self.config_loader.get_active_tools(volume)
        if active_tools:
            print(f"Active tools: {', '.join(active_tools)}")
        else:
            print("All tools disabled (Volume 0)")
    
    def set_volume(self, volume: int):
        """Set volume (0-1000, must be multiple of 5)"""
        if not 0 <= volume <= 1000:
            raise ValueError(f"Volume must be between 0 and 1000, got {volume}")
        
        if volume % 5 != 0:
            raise ValueError(f"Volume must be multiple of 5, got {volume}")
        
        self.current_volume = volume
        self.save_volume(volume)
        self.apply_settings_for_volume(volume)
        print(f"Volume {self.knob_name} set to {volume}/1000")
    
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
        elif volume <= 50:
            return f"ULTRA QUIET ({volume}/1000) - Only critical errors"
        elif volume <= 100:
            return f"QUIET ({volume}/1000) - Basic syntax only"
        elif volume <= 200:
            return f"LOW ({volume}/1000) - Basic formatting"
        elif volume <= 300:
            return f"MEDIUM-LOW ({volume}/1000) - Standard formatting"
        elif volume <= 400:
            return f"MEDIUM ({volume}/1000) - Standard + imports"
        elif volume <= 500:
            return f"MEDIUM-HIGH ({volume}/1000) - Enhanced checks"
        elif volume <= 600:
            return f"HIGH ({volume}/1000) - Strict mode"
        elif volume <= 700:
            return f"VERY HIGH ({volume}/1000) - Very strict"
        elif volume <= 800:
            return f"LOUD ({volume}/1000) - Extreme checks"
        elif volume <= 900:
            return f"VERY LOUD ({volume}/1000) - Maximum strictness"
        else:
            return f"MAXIMUM ({volume}/1000) - Nuclear mode"
    
    def get_volume_level(self) -> str:
        """Get volume level category"""
        volume = self.current_volume
        
        if volume == 0:
            return "OFF"
        elif volume <= 50:
            return "ULTRA_QUIET"
        elif volume <= 100:
            return "QUIET"
        elif volume <= 200:
            return "LOW"
        elif volume <= 300:
            return "MEDIUM_LOW"
        elif volume <= 400:
            return "MEDIUM"
        elif volume <= 500:
            return "MEDIUM_HIGH"
        elif volume <= 600:
            return "HIGH"
        elif volume <= 700:
            return "VERY_HIGH"
        elif volume <= 800:
            return "LOUD"
        elif volume <= 900:
            return "VERY_LOUD"
        else:
            return "MAXIMUM"


class DevVolumeKnob(VolumeKnob):
    """Development Environment Volume Knob"""
    
    def __init__(self):
        super().__init__("dev")
    
    def apply_volume_settings(self):
        """Apply the current volume settings to the development environment"""
        volume = self.current_volume
    def apply_volume_settings(self):
        """Apply the current volume settings to the development environment"""
        volume = self.current_volume
        
        # Plain text message without emoji
        print(f"Applying Commit Volume {volume}/1000: {self.get_volume_description()}")

        # Use JSON migration system
        from json_migrations import json_migrations
        config = json_migrations.migrate_to_level(volume, "commit")

        # Apply pre-commit configuration settings
        pre_commit_config = config.get('configs', {}).get('pre_commit', {})
        self._apply_pre_commit_config(pre_commit_config.get('hooks', {}))

        # Refresh environment
        self._refresh_environment()

        # Plain text success message
        print(f"Commit Volume {volume}/1000 applied successfully")
        print(f"Checks enabled: {', '.join(config.get('checks', []))}")

    def _apply_pre_commit_config(self, pre_commit_config: Dict[str, Any]):
        """Apply pre-commit configuration linked to Quality Engine modes."""
        # Message adjusted for plain text
        print("Updated pre-commit configuration")
        print(f"Config: {pre_commit_config}")

    def _refresh_environment(self):
        """Refresh the development environment after applying settings."""
        import subprocess
        import platform

        # Plain text refresh message
        print("Refreshing environment...")

        # Rest of the logic remains unchanged
        touch_file = ".volume-refresh"
        with open(touch_file, 'w') as f:
            f.write(f"Volume changed at {__import__('datetime').datetime.now()}")

        # Substitute potential errors
        print("Environment refresh triggered")
        print("If using VS Code or Cursor, consider manually reloading the window and restarting the language server.")
        
        # Use JSON migration system
        from json_migrations import json_migrations
        config = json_migrations.migrate_to_level(volume, "dev")
        
        # Apply VS Code settings
        vscode_config = config.get('configs', {}).get('vscode', {})
        self._apply_vscode_settings(vscode_config.get('settings', {}))
        
        # Apply config files
        self._apply_config_files_from_json(config)
        
        # Refresh environment
        self._refresh_environment()
        
        print(f"✅ Dev Volume {volume}/1000 applied successfully")
        print(f"   Checks enabled: {', '.join(config.get('checks', []))}")
    
    def _apply_vscode_settings(self, settings: Dict[str, Any]):
        """Apply VS Code settings"""
        os.makedirs(".vscode", exist_ok=True)
        
        # Load existing settings
        settings_path = ".vscode/settings.json"
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                existing_settings = json.load(f)
        else:
            existing_settings = {}
        
        # Update with new settings
        existing_settings.update(settings)
        
        # Save settings
        with open(settings_path, 'w') as f:
            json.dump(existing_settings, f, indent=4)
        
        print("✅ Applied VS Code settings")
    
    def _apply_config_files(self, config_files: Dict[str, str]):
        """Apply configuration files"""
        for filename, content in config_files.items():
            with open(filename, 'w') as f:
                f.write(content)
            print(f"✅ Created {filename}")
    
    def _apply_config_files_from_json(self, config: Dict[str, Any]):
        """Apply configuration files from JSON migration config"""
        from json_migrations import json_migrations
        volume = self.current_volume
        
        # Apply Ruff config
        ruff_config = json_migrations.get_ruff_config(volume)
        if ruff_config:
            with open(".ruff.toml", 'w') as f:
                f.write(ruff_config)
            print("✅ Created .ruff.toml")
        elif os.path.exists(".ruff.toml"):
            os.remove(".ruff.toml")
            print("✅ Removed .ruff.toml")
        
        # Apply Pyright config
        pyright_config = json_migrations.get_pyright_config(volume)
        if pyright_config:
            with open("pyrightconfig.json", 'w') as f:
                f.write(pyright_config)
            print("✅ Created pyrightconfig.json")
        elif os.path.exists("pyrightconfig.json"):
            os.remove("pyrightconfig.json")
            print("✅ Removed pyrightconfig.json")
        
        # Apply pyproject.toml configuration
        self._apply_pyproject_config(volume)
    
    def _apply_pyproject_config(self, volume: int):
        """Apply pyproject.toml configuration based on volume level"""
        import toml
        
        # Load existing pyproject.toml
        pyproject_path = "pyproject.toml"
        if not os.path.exists(pyproject_path):
            print("⚠️  pyproject.toml not found")
            return
        
        try:
            with open(pyproject_path, 'r') as f:
                pyproject_data = toml.load(f)
        except Exception as e:
            print(f"⚠️  Error reading pyproject.toml: {e}")
            return
        
        # Update based on volume level
        if volume == 0:
            # Level 0: Disable all linting in pyproject.toml
            if 'tool' in pyproject_data:
                if 'ruff' in pyproject_data['tool']:
                    pyproject_data['tool']['ruff'] = {
                        'line-length': 120,
                        'target-version': 'py312',
                        'exclude': ['.*', '*/venv/*', '*/__pycache__/*', '*/build/*', '*/dist/*']
                    }
                    if 'lint' not in pyproject_data['tool']['ruff']:
                        pyproject_data['tool']['ruff']['lint'] = {}
                    pyproject_data['tool']['ruff']['lint']['select'] = []
                    pyproject_data['tool']['ruff']['lint']['ignore'] = ['ALL']
                    
                    if 'per-file-ignores' not in pyproject_data['tool']['ruff']['lint']:
                        pyproject_data['tool']['ruff']['lint']['per-file-ignores'] = {}
                    pyproject_data['tool']['ruff']['lint']['per-file-ignores']['*'] = ['ALL']
                
                if 'mypy' in pyproject_data['tool']:
                    pyproject_data['tool']['mypy'] = {
                        'python_version': '3.13',
                        'warn_return_any': False,
                        'warn_unused_configs': False,
                        'disallow_untyped_defs': False,
                        'disallow_incomplete_defs': False,
                        'check_untyped_defs': False,
                        'disallow_untyped_decorators': False,
                        'no_implicit_optional': False,
                        'warn_redundant_casts': False,
                        'warn_unused_ignores': False,
                        'warn_no_return': False,
                        'warn_unreachable': False,
                        'warn_return_any': False,
                        'allow_redefinition': True,
                        'allow_untyped_globals': True,
                        'allow_untyped_calls': True,
                        'allow_incomplete_defs': True,
                        'allow_untyped_defs': True
                    }
                
                if 'flake8' in pyproject_data['tool']:
                    pyproject_data['tool']['flake8'] = {
                        'max-line-length': 120,
                        'extend-ignore': ['E', 'W', 'F', 'C', 'N', 'D', 'S', 'B', 'A', 'COM', 'DTZ', 'ISC', 'G', 'INP', 'Q', 'SIM', 'TCH', 'TID', 'T20', 'PYI', 'PT', 'PIE', 'RET', 'SLF', 'SLOT', 'PTH', 'RSE', 'TRY', 'NPY', 'AIR', 'ARG', 'LOG', 'RED', 'BLE', 'FBT', 'C90', 'ICN', 'PGH', 'PLR', 'PLW', 'PLE', 'PL', 'RUF', 'ANN', 'UP', 'C4'],
                        'per-file-ignores': ['*:E,W,F,C,N,D,S,B,A,COM,DTZ,ISC,G,INP,Q,SIM,TCH,TID,T20,PYI,PT,PIE,RET,SLF,SLOT,PTH,RSE,TRY,NPY,AIR,ARG,LOG,RED,BLE,FBT,C90,ICN,PGH,PLR,PLW,PLE,PL,RUF,ANN,UP,C4']
                    }
                
                if 'bandit' in pyproject_data['tool']:
                    pyproject_data['tool']['bandit'] = {
                        'skips': ['ALL'],
                        'exclude_dirs': ['*']
                    }
                
                if 'pydocstyle' in pyproject_data['tool']:
                    pyproject_data['tool']['pydocstyle'] = {
                        'inherit': False,
                        'ignore': ['ALL'],
                        'match': '',
                        'match_dir': ''
                    }
        
        # Save updated pyproject.toml
        try:
            with open(pyproject_path, 'w') as f:
                toml.dump(pyproject_data, f)
            print("✅ Updated pyproject.toml for level 0")
        except Exception as e:
            print(f"⚠️  Error writing pyproject.toml: {e}")
    
    def _refresh_environment(self):
        """Refresh the development environment after applying settings"""
        import subprocess
        import platform
        
        print("🔄 Refreshing environment...")
        
        # Create a touch file to trigger IDE refresh
        touch_file = ".volume-refresh"
        with open(touch_file, 'w') as f:
            f.write(f"Volume changed at {__import__('datetime').datetime.now()}")
        
        # Remove the touch file after a short delay
        import time
        time.sleep(0.1)
        if os.path.exists(touch_file):
            os.remove(touch_file)
        
        # Try to reload VS Code window if possible
        try:
            if platform.system() == "Windows":
                # On Windows, try to reload VS Code window
                subprocess.run([
                    "code", "--command", "workbench.action.reloadWindow"
                ], capture_output=True, timeout=5)
            else:
                # On other platforms, try to reload VS Code window
                subprocess.run([
                    "code", "--command", "workbench.action.reloadWindow"
                ], capture_output=True, timeout=5)
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            # If VS Code command fails, just continue
            pass
        print("✅ Environment refresh triggered")
        print("💡 If using VS Code/Cursor, you may need to:")
        print("   - Reload the window (Ctrl+Shift+P -> 'Developer: Reload Window')")
        print("   - Or restart the Python language server")
        print("   - Or restart your IDE")

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
        
        print(f"🎛️ Applying Commit Volume {volume}/1000: {self.get_volume_description()}")
        
        # Use JSON migration system
        from json_migrations import json_migrations
        config = json_migrations.migrate_to_level(volume, "commit")
        
        # Apply pre-commit configuration
        pre_commit_config = config.get('configs', {}).get('pre_commit', {})
        self._apply_pre_commit_config(pre_commit_config.get('hooks', {}))
        
        # Refresh environment
        self._refresh_environment()
        
        print(f"Commit Volume {volume}/1000 applied successfully")
        print(f"Checks enabled: {', '.join(config.get('checks', []))}")
    
    def _apply_pre_commit_config(self, pre_commit_config: Dict[str, Any]):
        """Apply pre-commit configuration"""
        # Adjusted print statements
        print("Updated pre-commit configuration")
        print(f"Config: {pre_commit_config}")

#Make sure this is applied only as a direct substitution for the respective portion of the code. Everything else in the file remains unmodified.
        print(f"   Config: {pre_commit_config}")


def main():
    """Main function for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python volume_knob.py dev <0-1000>")
        print("  python volume_knob.py commit <0-1000>")
        print("  python volume_knob.py dev up [steps]")
        print("  python volume_knob.py dev down [steps]")
        return
    
    knob_type = sys.argv[1].lower()
    
    if knob_type == "dev":
        knob = DevVolumeKnob()
    elif knob_type == "commit":
        knob = CommitVolumeKnob()
    else:
        print(f"Unknown knob type: {knob_type}")
        return
    
    if len(sys.argv) >= 3:
        command = sys.argv[2].lower()
        
        if command == "up":
            steps = int(sys.argv[3]) if len(sys.argv) >= 4 else 1
            knob.volume_up(steps)
        elif command == "down":
            steps = int(sys.argv[3]) if len(sys.argv) >= 4 else 1
            knob.volume_down(steps)
        else:
            try:
                volume = int(command)
                knob.set_volume(volume)
            except ValueError:
                print(f"Invalid volume: {command}")
                return
    
    # Apply the settings
    knob.apply_volume_settings()
    
def main():
    """Entry point for volume control knob operations"""
    import sys

    if len(sys.argv) < 2:
        print("Usage examples:")
        print("  python volume_knob.py dev 100  # Set dev volume to 100")
        print("  python volume_knob.py commit up 5  # Increase commit volume by 5 ticks")
        return

    knob_type = sys.argv[1].lower()

    # Create and validate knob instance
    knob = None
    if knob_type == "dev":
        knob = DevVolumeKnob()
    elif knob_type == "commit":
        knob = CommitVolumeKnob()
    else:
        print("Error: Unknown knob type. Use 'dev' or 'commit'.")
        return

    # Verify the knob was created correctly
    if not knob:
        raise RuntimeError("Failed to initialize the volume knob")

    # Accept commands like setting a volume, increasing or decreasing
    if len(sys.argv) > 2:
        command = sys.argv[2]
        try:
            if command == "up":
                steps = int(sys.argv[3]) if len(sys.argv) > 3 else 1
                knob.volume_up(steps)
            elif command == "down":
                steps = int(sys.argv[3]) if len(sys.argv) > 3 else 1
                knob.volume_down(steps)
            else:
                volume = int(command)
                knob.set_volume(volume)
        except (ValueError, IndexError):
            print("Invalid command or parameters. See usage examples.")
            return

        # Apply and confirm the settings
        knob.apply_volume_settings()
        print(f"Active Knob: {knob.knob_name.upper()}")
        print(f"Current Volume: {knob.get_volume()} / 1000")

if __name__ == "__main__":
    main() 