"""Configuration loading for the Quality Engine."""

import importlib
import os
from typing import Any, cast

import pydantic


class ToolConfig(pydantic.BaseModel):
    """Configuration for a single quality tool."""

    enabled: bool = True
    config: dict[str, Any] = {}


class QualityEngineConfig(pydantic.BaseModel):
    """Define the configuration for the Quality Engine."""

    default_mode: str = "smart"
    tools: dict[str, ToolConfig] = {}
    modes: dict[str, list[str]] = {}  # New Field for mode tools


def validate_config(config: QualityEngineConfig) -> None:
    """Validate the loaded configuration."""
    for mode, tools in config.modes.items():
        for tool in tools:
            if tool not in config.tools:
                msg = f"Tool '{tool}' in mode '{mode}' is not defined in the tools section."
                raise ValueError(msg)


def _merge_quality_from_dict(
    quality_config: dict[str, Any], default_config: dict[str, Any]
) -> None:
    """Merge quality configuration dict into the default config in-place."""
    # Merge default mode
    if "default_mode" in quality_config:
        default_config["default_mode"] = cast("str", quality_config["default_mode"])

    # Merge tools
    if isinstance(quality_config.get("tools"), dict):
        merged_tools: dict[str, Any] = dict(cast("dict[str, Any]", default_config.get("tools", {})))
        for tool, tool_config in cast("dict[str, Any]", quality_config["tools"]).items():
            merged_tools[cast("str", tool)] = cast("dict[str, Any]", tool_config)
        default_config["tools"] = merged_tools

    # Merge modes
    if isinstance(quality_config.get("modes"), dict):
        merged_modes: dict[str, list[str]] = dict(
            cast("dict[str, list[str]]", default_config.get("modes", {}))
        )
        for mode, tools in cast("dict[str, Any]", quality_config["modes"]).items():
            merged_modes[cast("str", mode)] = cast("list[str]", tools)
        default_config["modes"] = merged_modes


def _load_toml_config(config_path: str) -> dict[str, Any]:
    """Load a TOML file if the toml module is available; otherwise return empty dict."""
    try:
        toml_mod = importlib.import_module("toml")  # type: ignore[import-not-found]
    except Exception:
        return {}
    with open(config_path, "rb") as f:
        return cast("dict[str, Any]", toml_mod.load(f))  # type: ignore[attr-defined]


def _load_yaml_config(config_path: str) -> dict[str, Any]:
    """Load a YAML file if PyYAML is available; otherwise return empty dict."""
    try:
        yaml_mod = importlib.import_module("yaml")  # type: ignore[import-not-found]
    except Exception:
        return {}
    with open(config_path, encoding="utf-8") as f:
        return cast("dict[str, Any]", yaml_mod.safe_load(f)) or {}  # type: ignore[attr-defined]


def load_config(config_path: str = "pyproject.toml") -> QualityEngineConfig:
    """Load the quality engine configuration from project settings."""
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
                file_config = _load_toml_config(config_path)
                # Extract tool configuration from pyproject.toml
                autopr_section = (
                    cast("dict[str, Any] | None", file_config.get("autopr"))
                    if file_config
                    else None
                )
                if (
                    autopr_section
                    and isinstance(autopr_section, dict)
                    and "quality" in autopr_section
                ):
                    _merge_quality_from_dict(
                        cast("dict[str, Any]", autopr_section["quality"]),
                        default_config,
                    )

            elif config_path.endswith((".yaml", ".yml")):
                yaml_config = _load_yaml_config(config_path)
                if yaml_config:
                    _merge_quality_from_dict(yaml_config, default_config)

    except Exception:
        pass

    config = QualityEngineConfig.parse_obj(default_config)
    validate_config(config)
    return config
