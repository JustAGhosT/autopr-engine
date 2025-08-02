import os
from typing import Any

import pydantic
import toml
import yaml


class ToolConfig(pydantic.BaseModel):
    """Configuration for a single quality tool."""

    enabled: bool = True
    config: dict[str, Any] = {}


class QualityEngineConfig(pydantic.BaseModel):
    """Configuration for the Quality Engine."""

    default_mode: str = "smart"
    tools: dict[str, ToolConfig] = {}
    modes: dict[str, list[str]] = {}  # New Field for mode tools


def validate_config(config: QualityEngineConfig):
    """Validates the loaded configuration."""
    for mode, tools in config.modes.items():
        for tool in tools:
            if tool not in config.tools:
                raise ValueError(
                    f"Tool '{tool}' in mode '{mode}' is not defined in the tools section."
                )


def load_config(config_path: str = "pyproject.toml") -> QualityEngineConfig:
    """Loads the quality engine configuration from the project settings."""
    default_config = {
        "default_mode": "smart",
        "tools": {
            "ruff": {"enabled": True},
            "mypy": {"enabled": True},
            "bandit": {"enabled": True},
            "interrogate": {"enabled": True},
            "radon": {"enabled": True},
            "pytest": {"enabled": True},
            "codeql": {"enabled": True},
            "sonarqube": {"enabled": True},
            "ai_feedback": {"enabled": True},
            "eslint": {"enabled": True},
            "dependency_scanner": {"enabled": True},
            "performance_analyzer": {"enabled": True},
        },
        "modes": {  # Define which tools to use for each mode
            "fast": ["ruff"],
            "comprehensive": [
                "ruff",
                "mypy",
                "bandit",
                "interrogate",
                "radon",
                "pytest",
                "codeql",
                "sonarqube",
                "eslint",
                "dependency_scanner",
                "performance_analyzer",
            ],
            "ai_enhanced": [
                "ruff",
                "mypy",
                "bandit",
                "interrogate",
                "radon",
                "pytest",
                "ai_feedback",
            ],
            "smart": [],  # Determined dynamically
        },
    }

    try:
        # Try to load configuration from the specified file
        if os.path.exists(config_path):
            if config_path.endswith(".toml"):
                with open(config_path) as f:
                    file_config = toml.load(f)

                # Extract tool configuration from pyproject.toml
                if "autopr" in file_config and "quality" in file_config["autopr"]:
                    quality_config = file_config["autopr"]["quality"]

                    # Merge with default config
                    if "default_mode" in quality_config:
                        default_config["default_mode"] = quality_config["default_mode"]

                    if "tools" in quality_config:
                        for tool, tool_config in quality_config["tools"].items():
                            default_config["tools"][tool] = tool_config

                    if "modes" in quality_config:
                        for mode, tools in quality_config["modes"].items():
                            default_config["modes"][mode] = tools

            elif config_path.endswith(".yaml") or config_path.endswith(".yml"):
                with open(config_path) as f:
                    yaml_config = yaml.safe_load(f)

                # Merge with default config
                if yaml_config:
                    if "default_mode" in yaml_config:
                        default_config["default_mode"] = yaml_config["default_mode"]

                    if "tools" in yaml_config:
                        for tool, tool_config in yaml_config["tools"].items():
                            default_config["tools"][tool] = tool_config

                    if "modes" in yaml_config:
                        for mode, tools in yaml_config["modes"].items():
                            default_config["modes"][mode] = tools

    except Exception as e:
        print(f"Error loading configuration from {config_path}: {e}")
        print("Using default configuration.")

    config = QualityEngineConfig.parse_obj(default_config)
    validate_config(config)
    return config
