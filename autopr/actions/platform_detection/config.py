"""
Platform Configuration Module

Loads and manages platform configurations from JSON files using the new schema.
"""

import json
import logging
from pathlib import Path
from typing import Any, ClassVar, Optional, Self, TypeVar

from .schema import PlatformConfig, PlatformType

# Set up logging
logger = logging.getLogger(__name__)

T = TypeVar("T", bound="PlatformConfigManager")


class PlatformConfigManager:
    """Manages platform configurations with the new schema."""

    _instance: ClassVar[Optional["PlatformConfigManager"]] = None
    _configs_loaded: bool = False
    _platforms: dict[str, PlatformConfig] = {}
    _platforms_by_category: dict[str, list[str]] = {}
    _platforms_by_type: dict[PlatformType, list[str]] = {}

    # Default configuration directories
    _BASE_CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "configs" / "platforms"
    _CATEGORY_FILES = {
        "core": "core_platforms.json",
        "ai": "ai_platforms.json",
        "cloud": "cloud_platforms.json",
    }

    def __new__(cls) -> Self:
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance  # type: ignore[return-value]

    def _initialize(self) -> None:
        """Initialize the configuration manager.

        This method sets up the initial state of the configuration manager
        and loads all platform configurations.
        """
        self._platforms = {}
        self._platforms_by_category = {}
        self._platforms_by_type = {}
        self._platforms_by_id: dict[str, PlatformConfig] = {}
        self._load_config_files()
        self._index_platforms()
        self._configs_loaded = True

    @classmethod
    def _load_platform_file(cls, file_path: Path) -> PlatformConfig | None:
        """
        Load a single platform configuration file.

        Args:
            file_path: Path to the platform configuration file

        Returns:
            PlatformConfig instance if successful, None otherwise
        """
        try:
            if not file_path.exists():
                logger.warning(f"Platform config file not found: {file_path}")
                return None

            file_path.stem
            return PlatformConfig.from_file(file_path)

        except (OSError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error loading platform config {file_path}: {e}", exc_info=True)
            return None

    def _load_platforms_from_category(self, category: str) -> dict[str, PlatformConfig]:
        """
        Load all platforms from a category directory.

        Args:
            category: Category name (core, ai, cloud, etc.)

        Returns:
            Dictionary of platform_id -> PlatformConfig
        """
        category_dir = self._BASE_CONFIG_DIR / category
        if not category_dir.exists() or not category_dir.is_dir():
            logger.warning("Category directory not found: %s", category_dir)
            return {}

        platforms = {}

        # Load all JSON files in the category directory
        for config_file in category_dir.glob("*.json"):
            if config_file.name in self._CATEGORY_FILES.values():
                # Skip category index files
                continue

            platform = self._load_platform_file(config_file)
            if platform:
                platforms[platform.id] = platform

                # Update indexes

        return platforms

    def _load_config_files(self) -> None:
        """Load platform configuration files from the configured directories.

        This method loads platform configurations from JSON files in the
        configured category directories and registers them with the manager.
        """
        # Load platform configurations from each category
        for category, filename in self._CATEGORY_FILES.items():
            try:
                config_path = self._BASE_CONFIG_DIR / filename
                if not config_path.exists():
                    logger.warning(f"Config file not found: {config_path}")
                    continue

                with open(config_path, encoding="utf-8") as f:
                    config_data = json.load(f)

                # Validate the config file structure
                if not isinstance(config_data, dict) or "platforms" not in config_data:
                    logger.error(f"Invalid config file format in {config_path}")
                    continue

                # Process each platform in the config file
                for platform_ref in config_data["platforms"]:
                    try:
                        platform_id = platform_ref.get("id")
                        config_file = platform_ref.get("config_file")

                        if not platform_id or not config_file:
                            logger.warning(
                                f"Missing required fields in platform reference: {platform_ref}"
                            )
                            continue

                        # Load the platform configuration
                        platform_config_path = self._BASE_CONFIG_DIR / config_file
                        if not platform_config_path.exists():
                            logger.warning(f"Platform config not found: {platform_config_path}")
                            continue

                        with open(platform_config_path, encoding="utf-8") as pf:
                            platform_data = json.load(pf)

                        # Create and store the platform config
                        platform_config = PlatformConfig.from_dict(platform_id, platform_data)
                        self._platforms[platform_id] = platform_config

                        # Update indexes
                        if category not in self._platforms_by_category:
                            self._platforms_by_category[category] = []
                        self._platforms_by_category[category].append(platform_id)

                        platform_type = platform_config.type
                        if platform_type not in self._platforms_by_type:
                            self._platforms_by_type[platform_type] = []
                        self._platforms_by_type[platform_type].append(platform_id)

                    except Exception as e:
                        logger.exception(f"Error loading platform config {platform_id}: {e!s}")
                        continue

            except Exception as e:
                logger.exception(f"Error loading config file {filename}: {e!s}")
                continue

    def _index_platforms(self) -> None:
        """Index platforms for faster lookups.

        This method creates additional indexes to optimize platform lookups
        by various criteria.
        """
        self._platforms_by_id = {p.id: p for p in self._platforms.values()}

        # Ensure all categories and types have lists, even if empty
        for platform in self._platforms.values():
            if platform.category not in self._platforms_by_category:
                self._platforms_by_category[platform.category] = []
            if platform.type not in self._platforms_by_type:
                self._platforms_by_type[platform.type] = []

        # Sort platforms by priority within each category/type
        for category in self._platforms_by_category:
            self._platforms_by_category[category].sort(
                key=lambda x: self._platforms[x].priority, reverse=True
            )

        for platform_type in self._platforms_by_type:
            self._platforms_by_type[platform_type].sort(
                key=lambda x: self._platforms[x].priority, reverse=True
            )

    def get_platform(self, platform_id: str) -> dict[str, Any] | None:
        """Get a platform configuration by ID.

        Args:
            platform_id: The ID of the platform to retrieve

        Returns:
            The platform configuration as a dictionary, or None if not found
        """
        platform = self._platforms_by_id.get(platform_id)
        return platform.to_dict() if platform else None

    def get_platforms_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get all platforms in a specific category.

        Args:
            category: The category to filter platforms by

        Returns:
            A list of platform configurations in the specified category
        """
        return [
            self._platforms[pid].to_dict() for pid in self._platforms_by_category.get(category, [])
        ]

    def get_ai_platforms(self) -> dict[str, dict[str, Any]]:
        """Get all AI development platforms.

        Returns:
            A dictionary mapping platform IDs to their configurations for AI platforms
        """
        ai_platforms = {}
        for platform_id, platform in self._platforms.items():
            platform_dict = platform.to_dict()
            if platform_dict.get("category") == "ai_development":
                ai_platforms[platform_id] = platform_dict
        return ai_platforms

    def get_platforms_by_type(self, platform_type: str) -> list[dict[str, Any]]:
        """Get all platforms of a specific type.

        Args:
            platform_type: The platform type to filter by

        Returns:
            A list of platform configurations of the specified type
        """
        platform_ids: list[str] = self._platforms_by_type.get(platform_type, [])
        return [self._platforms[pid].to_dict() for pid in platform_ids]

    def get_all_platforms(self) -> dict[str, dict[str, Any]]:
        """Get all platform configurations.

        Returns:
            A dictionary mapping platform IDs to their configurations
        """
        return {pid: platform.to_dict() for pid, platform in self._platforms.items()}

    def get_platforms_with_detection_rules(self) -> dict[str, dict[str, Any]]:
        """Get platforms that have detection rules configured.

        This is useful for the detector to only process platforms
        that actually have detection rules defined.

        Returns:
            A dictionary of platform configurations with detection rules
        """
        return {
            pid: platform.to_dict()
            for pid, platform in self._platforms.items()
            if hasattr(platform, "detection") and platform.detection
        }

    def get_active_platforms(self) -> dict[str, dict[str, Any]]:
        """
        Get all active platform configurations.

        Returns:
            Dictionary of platform_id -> PlatformConfig
        """
        if not self._configs_loaded:
            self._load_config_files()
        return {pid: p.to_dict() for pid, p in self._platforms.items() if p.is_active}

    def find_platforms(self, **filters: Any) -> dict[str, PlatformConfig]:
        """
        Find platforms matching the given filters.

        Args:
            **filters: Field names and values to filter by

        Returns:
            Dictionary of platform_id -> PlatformConfig that match all filters
        """
        if not self._configs_loaded:
            self._load_config_files()

        result = {}
        for platform_id, platform in self._platforms.items():
            match = True
            for field, value in filters.items():
                if not hasattr(platform, field):
                    match = False
                    break

                if getattr(platform, field) != value:
                    match = False
                    break

            if match:
                result[platform_id] = platform

        return result

    def get_platform_categories(self) -> dict[str, list[str]]:
        """
        Get platform categories with their associated platform IDs.

        Returns:
            Dictionary mapping category names to lists of platform IDs
        """
        if not self._configs_loaded:
            self._load_config_files()

        return {
            category: platform_ids.copy()
            for category, platform_ids in self._platforms_by_category.items()
        }


# For backward compatibility
# Backward compatibility alias
# PlatformConfig = PlatformConfigManager
