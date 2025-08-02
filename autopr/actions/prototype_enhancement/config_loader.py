"""
Configuration and template loading utilities for the AutoPR prototype enhancement system.

This module provides utilities to load externalized configuration files and templates
from the organized configs/ and templates/ directories.
"""

from functools import lru_cache
import json
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Base paths for configurations and templates
CONFIG_BASE_PATH = Path(__file__).parent.parent.parent.parent / "configs"
TEMPLATE_BASE_PATH = Path(__file__).parent.parent.parent.parent / "templates"


class ConfigLoader:
    """Utility class for loading configuration files and templates."""

    @staticmethod
    @lru_cache(maxsize=32)
    def load_platform_config(platform_name: str) -> dict[str, Any]:
        """Load platform configuration from JSON file.

        Args:
            platform_name: Name of the platform (e.g., 'replit', 'lovable', 'bolt')

        Returns:
            Dictionary containing platform configuration

        Raises:
            FileNotFoundError: If platform config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        config_path = CONFIG_BASE_PATH / "platforms" / f"{platform_name}.json"

        if not config_path.exists():
            msg = f"Platform config not found: {config_path}"
            raise FileNotFoundError(msg)

        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = json.load(f)
            logger.debug(f"Loaded platform config for {platform_name}")
            if isinstance(config_data, dict):
                return config_data
            return {}
        except json.JSONDecodeError as e:
            logger.exception(f"Invalid JSON in platform config {config_path}: {e}")
            raise

    @staticmethod
    @lru_cache(maxsize=16)
    def load_package_dependencies(category: str) -> dict[str, Any]:
        """Load package dependencies configuration from JSON file.

        Args:
            category: Package category (e.g., 'security', 'testing', 'performance')

        Returns:
            Dictionary containing package dependencies
        """
        config_path = CONFIG_BASE_PATH / "packages" / f"{category}.json"

        if not config_path.exists():
            msg = f"Package config not found: {config_path}"
            raise FileNotFoundError(msg)

        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = json.load(f)
            logger.debug(f"Loaded package dependencies for {category}")
            if isinstance(config_data, dict):
                return config_data
            return {}
        except json.JSONDecodeError as e:
            logger.exception(f"Invalid JSON in package config {config_path}: {e}")
            raise

    @staticmethod
    def load_template_metadata(template_path: str) -> dict[str, Any]:
        """Load metadata from a YAML template file."""
        try:
            with open(template_path, encoding="utf-8") as f:
                content = f.read()

            # Split YAML front matter from template content
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 2:
                    yaml_content = parts[1]
                    metadata = yaml.safe_load(yaml_content)
                    return metadata if isinstance(metadata, dict) else {}

            return {}
        except Exception:
            return {}

    @staticmethod
    @lru_cache(maxsize=32)
    def load_workflow_config(workflow_name: str) -> dict[str, Any]:
        """Load workflow configuration from YAML file.

        Args:
            workflow_name: Name of the workflow

        Returns:
            Dictionary containing workflow configuration
        """
        config_path = CONFIG_BASE_PATH / "workflows" / f"{workflow_name}.yml"

        if not config_path.exists():
            msg = f"Workflow config not found: {config_path}"
            raise FileNotFoundError(msg)

        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.debug(f"Loaded workflow config for {workflow_name}")
            return config if isinstance(config, dict) else {}
        except yaml.YAMLError as e:
            logger.exception(f"Invalid YAML in workflow config {config_path}: {e}")
            raise

    @staticmethod
    @lru_cache(maxsize=64)
    def load_template_config(template_name: str, category: str | None = None) -> dict[str, Any]:
        """Load template configuration from YAML file.

        Args:
            template_name: Name of the template
            category: Optional category to search within

        Returns:
            Dictionary containing template configuration
        """
        if category:
            config_path = TEMPLATE_BASE_PATH / category / f"{template_name}.yml"
        else:
            # Search in common categories
            for cat in ["build", "deployment", "security", "testing", "monitoring"]:
                config_path = TEMPLATE_BASE_PATH / cat / f"{template_name}.yml"
                if config_path.exists():
                    break
            else:
                config_path = TEMPLATE_BASE_PATH / f"{template_name}.yml"

        if not config_path.exists():
            msg = f"Template config not found: {config_path}"
            raise FileNotFoundError(msg)

        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.debug(f"Loaded template config for {template_name}")
            return config if isinstance(config, dict) else {}
        except yaml.YAMLError as e:
            logger.exception(f"Invalid YAML in template config {config_path}: {e}")
            raise

    @staticmethod
    def get_available_platforms() -> list[str]:
        """Get list of available platform configurations.

        Returns:
            List of platform names
        """
        platforms_dir = CONFIG_BASE_PATH / "platforms"
        if not platforms_dir.exists():
            return []

        platforms = [config_file.stem for config_file in platforms_dir.glob("*.json")]

        return sorted(platforms)

    @staticmethod
    def get_available_package_categories() -> list[str]:
        """Get list of available package categories.

        Returns:
            List of package category names
        """
        packages_dir = CONFIG_BASE_PATH / "packages"
        if not packages_dir.exists():
            return []

        categories = [config_file.stem for config_file in packages_dir.glob("*.json")]

        return sorted(categories)

    @staticmethod
    def get_available_templates(category: str | None = None) -> dict[str, list[str]]:
        """Get list of available templates, optionally filtered by category.

        Args:
            category: Optional category to filter by

        Returns:
            Dictionary mapping categories to lists of template names
        """
        templates = {}

        if category:
            # Search specific category
            category_dir = TEMPLATE_BASE_PATH / category
            if category_dir.exists():
                template_files = [
                    template_file.stem for template_file in category_dir.glob("*.yml")
                ]
                templates[category] = sorted(template_files)
        else:
            # Search all categories
            for category_dir in TEMPLATE_BASE_PATH.iterdir():
                if category_dir.is_dir():
                    template_files = []
                    for template_file in category_dir.glob("*.yml"):
                        template_files.append(template_file.stem)
                    if template_files:
                        templates[category_dir.name] = sorted(template_files)

        return templates

    @staticmethod
    def get_template_variants(template_path: str) -> list[str]:
        """Get available variants for a template.

        Args:
            template_path: Path to the template file

        Returns:
            List of variant names
        """
        try:
            metadata = ConfigLoader.load_template_metadata(template_path)
            variants = metadata.get("variants", {})
            return list(variants.keys()) if isinstance(variants, dict) else []
        except Exception:
            return []

    @staticmethod
    @lru_cache(maxsize=32)
    def load_template(category: str, template_name: str) -> str:
        """Load template content from file.

        Args:
            category: Template category (e.g., 'docker', 'security', 'testing')
            template_name: Name of the template file

        Returns:
            Template content as string

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template_path = TEMPLATE_BASE_PATH / category / template_name

        if not template_path.exists():
            msg = f"Template not found: {template_path}"
            raise FileNotFoundError(msg)

        try:
            with open(template_path, encoding="utf-8") as f:
                content = f.read()
            logger.debug(f"Loaded template {category}/{template_name}")
            return content
        except Exception as e:
            logger.exception(f"Error loading template {template_path}: {e}")
            raise


# Convenience functions for backward compatibility
def load_platform_config(platform_name: str) -> dict[str, Any]:
    """Load platform configuration - convenience function."""
    return ConfigLoader.load_platform_config(platform_name)


def load_package_dependencies(category: str) -> dict[str, Any]:
    """Load package dependencies - convenience function."""
    return ConfigLoader.load_package_dependencies(category)


def load_template_config(template_name: str, category: str | None = None) -> dict[str, Any]:
    """Load template configuration - convenience function."""
    return ConfigLoader.load_template_config(template_name, category)
