"""
AutoPR Configuration Module

Centralized configuration management system with:
- Environment-specific configurations
- Comprehensive validation
- Secure secret handling
- Hot reloading capabilities
- Backward compatibility
"""

from dataclasses import dataclass, field
import os
import pathlib
from typing import Any, Dict, Optional
import warnings

import yaml

# Import new centralized configuration system
from .settings import (
    AutoPRSettings,
    Environment,
    LLMProvider,
    get_settings,
    reload_settings,
    set_settings,
)
from .validation import check_environment_variables, generate_config_report, validate_configuration


@dataclass
class AutoPRConfig:
    """
    Main configuration class for AutoPR Engine.

    Handles loading configuration from environment variables,
    YAML files, and provides sensible defaults.
    """

    # GitHub configuration
    github_token: str | None = None
    github_app_id: str | None = None
    github_private_key: str | None = None
    github_webhook_secret: str | None = None

    # AI/LLM configuration
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    default_llm_provider: str = "openai"

    # Engine configuration
    max_concurrent_workflows: int = 10
    workflow_timeout: int = 300  # seconds
    enable_debug_logging: bool = False

    # Database configuration
    database_url: str | None = None
    redis_url: str | None = None

    # Additional settings
    custom_settings: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Load configuration from environment variables after initialization."""
        self._load_from_environment()
        self._load_from_file()

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            "GITHUB_TOKEN": "github_token",
            "GITHUB_APP_ID": "github_app_id",
            "GITHUB_PRIVATE_KEY": "github_private_key",
            "GITHUB_WEBHOOK_SECRET": "github_webhook_secret",
            "OPENAI_API_KEY": "openai_api_key",
            "ANTHROPIC_API_KEY": "anthropic_api_key",
            "DEFAULT_LLM_PROVIDER": "default_llm_provider",
            "DATABASE_URL": "database_url",
            "REDIS_URL": "redis_url",
            "MAX_CONCURRENT_WORKFLOWS": "max_concurrent_workflows",
            "WORKFLOW_TIMEOUT": "workflow_timeout",
            "ENABLE_DEBUG_LOGGING": "enable_debug_logging",
        }

        for env_var, attr_name in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Handle type conversion
                if attr_name in {"max_concurrent_workflows", "workflow_timeout"}:
                    setattr(self, attr_name, int(env_value))
                elif attr_name == "enable_debug_logging":
                    setattr(self, attr_name, env_value.lower() in {"true", "1", "yes", "on"})
                else:
                    setattr(self, attr_name, env_value)

    def _load_from_file(self, config_path: str | None = None) -> None:
        """Load configuration from YAML file."""
        if config_path is None:
            # Look for config file in common locations
            possible_paths = [
                "autopr.yaml",
                "autopr.yml",
                ".autopr.yaml",
                ".autopr.yml",
                pathlib.Path("~/.autopr.yaml").expanduser(),
                pathlib.Path("~/.autopr.yml").expanduser(),
            ]

            for path in possible_paths:
                if pathlib.Path(path).exists():
                    config_path = path
                    break

        if config_path and pathlib.Path(config_path).exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)

                if config_data:
                    for key, value in config_data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                        else:
                            self.custom_settings[key] = value
            except Exception as e:
                # Don't fail if config file is malformed, just log and continue
                import logging

                logging.warning(f"Failed to load config from {config_path}: {e}")

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            # Don't include sensitive information in dict representation
            if (
                "key" in field_name.lower()
                or "token" in field_name.lower()
                or "secret" in field_name.lower()
            ):
                result[field_name] = "***" if value else None
            else:
                result[field_name] = value
        return result

    def validate(self) -> bool:
        """
        Validate the configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        # Basic validation - ensure we have at least one way to authenticate with GitHub
        if not any([self.github_token, self.github_app_id]):
            return False

        # Ensure we have at least one LLM provider configured
        return any([self.openai_api_key, self.anthropic_api_key])

    @classmethod
    def from_file(cls, config_path: str) -> "AutoPRConfig":
        """
        Create configuration instance from file.

        Args:
            config_path: Path to configuration file

        Returns:
            AutoPRConfig instance
        """
        config = cls()
        config._load_from_file(config_path)
        return config


# Backward compatibility wrapper
def get_config() -> AutoPRConfig:
    """
    Get legacy configuration (deprecated).

    Returns:
        AutoPRConfig instance for backward compatibility

    Deprecated:
        Use get_settings() instead for the new configuration system
    """
    warnings.warn(
        "get_config() is deprecated. Use get_settings() from autopr.config.settings instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return AutoPRConfig()


# New centralized configuration exports
__all__ = [
    # Legacy configuration (deprecated)
    "AutoPRConfig",
    # New centralized configuration system
    "AutoPRSettings",
    "Environment",
    "LLMProvider",
    "check_environment_variables",
    "generate_config_report",
    "get_config",
    "get_settings",
    "reload_settings",
    "set_settings",
    # Validation utilities
    "validate_configuration",
]
