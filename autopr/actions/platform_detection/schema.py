"""
Platform Configuration Schema

Defines the structure and validation for platform configuration files.

This module contains schemas for:
1. PlatformIndex: For platform collection files (e.g., cloud_platforms.json)
2. PlatformConfig: For individual platform configuration files (e.g., cloud/vercel.json)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
import json
from typing import TYPE_CHECKING, Any, ClassVar, TypedDict

if TYPE_CHECKING:
    from pathlib import Path


class PlatformType(StrEnum):
    """Types of platforms we support."""

    IDE = "ide"
    CLOUD = "cloud"
    VCS = "vcs"
    CI_CD = "ci_cd"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    SECURITY = "security"
    AI = "ai"
    DEVELOPMENT_PLATFORM = "development_platform"
    GENERAL = "general"


class PlatformSource(StrEnum):
    """Source of the platform configuration."""

    OFFICIAL = "official"
    COMMUNITY = "community"
    THIRD_PARTY = "third_party"
    # Handle URL-based sources by mapping them to valid enum values
    SAME_NEW = "https://same.new"
    REPLIT = "https://replit.com"


class PlatformStatus(StrEnum):
    """Status of the platform support."""

    ACTIVE = "active"
    BETA = "beta"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class DetectionRules(TypedDict, total=False):
    """Configuration for platform detection rules."""

    files: list[str]
    dependencies: list[str]
    folder_patterns: list[str]
    commit_patterns: list[str]
    content_patterns: list[str]
    package_scripts: list[str]
    confidence_weights: dict[str, float]


class PlatformReference(TypedDict):
    """Minimal platform reference used in index files."""

    id: str
    name: str
    category: str
    description: str
    config_file: str
    is_active: bool
    priority: int


class PlatformIndex(TypedDict):
    """Schema for platform index files (e.g., cloud_platforms.json)."""

    version: str
    last_updated: str
    description: str
    platforms: list[PlatformReference]
    metadata: dict[str, Any]


class ProjectConfig(TypedDict, total=False):
    """Configuration for project setup and deployment."""

    primary_language: str
    framework: str
    deployment_targets: list[str]
    common_files: list[str]
    features: list[str]
    configuration_files: list[str]


@dataclass
class PlatformConfig:
    """
    Platform configuration container with validation.

    This class represents the complete configuration for a platform that AutoPR can interact with.
    It includes metadata, detection rules, and project configuration.
    """

    # Required fields (must be in root)
    id: str
    name: str
    category: str
    description: str
    priority: int

    # Display information
    display_name: str = ""
    version: str = "1.0.0"
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Status
    status: PlatformStatus = PlatformStatus.ACTIVE
    is_active: bool = True
    is_beta: bool = False
    is_deprecated: bool = False
    deprecation_message: str | None = None

    # Categorization
    type: PlatformType = PlatformType.GENERAL
    subcategory: str = ""
    tags: list[str] = field(default_factory=list)

    # Integration
    supported_languages: list[str] = field(default_factory=list)
    supported_frameworks: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)

    # Documentation
    documentation_url: str = ""
    setup_guide: str = ""
    troubleshooting_guide: str = ""

    # Ownership
    maintainer: str = ""
    source: PlatformSource = PlatformSource.COMMUNITY
    license: str = "MIT"

    # Technical metadata
    min_autopr_version: str = "0.1.0"
    dependencies: dict[str, str] = field(default_factory=dict)
    compatibility: dict[str, Any] = field(default_factory=dict)

    # Nested configurations
    detection: DetectionRules = field(default_factory=dict)
    project_config: ProjectConfig = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Class variables
    _required_fields: ClassVar[list] = ["id", "name", "category", "description"]

    @classmethod
    def from_dict(cls, platform_id: str, data: dict) -> PlatformConfig:
        """
        Create a PlatformConfig from a dictionary, with validation.

        Args:
            platform_id: The unique identifier for the platform
            data: Dictionary containing platform configuration

        Returns:
            A validated PlatformConfig instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        missing_fields = [f for f in cls._required_fields if f not in data]
        if missing_fields:
            msg = f"Missing required fields: {', '.join(missing_fields)}"
            raise ValueError(msg)

        # Handle enums and special types
        status = PlatformStatus(data.get("status", "active")) if "status" in data else None
        platform_type = PlatformType(data["type"]) if "type" in data else None

        # Handle source more flexibly
        source = None
        if "source" in data:
            try:
                source = PlatformSource(data["source"])
            except ValueError:
                # If the source value isn't in the enum, default to COMMUNITY
                source = PlatformSource.COMMUNITY

        # Create and return the config
        # Handle priority conversion
        priority_value = data.get("priority", 0)
        if isinstance(priority_value, str):
            # Convert string priorities to numeric values
            priority_map = {
                "high": 10,
                "medium": 5,
                "low": 1,
                "critical": 15,
                "important": 8,
                "normal": 5,
                "minor": 2,
            }
            priority_value = priority_map.get(priority_value.lower(), 0)
        elif isinstance(priority_value, int):
            priority_value = priority_value
        else:
            priority_value = 0

        return cls(
            id=platform_id,
            name=data["name"],
            category=data["category"],
            description=data["description"],
            priority=priority_value,
            # Display information
            display_name=data.get("display_name", data["name"]),
            version=data.get("version", "1.0.0"),
            last_updated=data.get("last_updated", datetime.utcnow().isoformat()),
            # Status
            status=status
            or (
                PlatformStatus.BETA
                if data.get("is_beta")
                else (
                    PlatformStatus.DEPRECATED
                    if data.get("is_deprecated")
                    else PlatformStatus.ACTIVE
                )
            ),
            is_active=data.get("is_active", True),
            is_beta=data.get("is_beta", False),
            is_deprecated=data.get("is_deprecated", False),
            deprecation_message=data.get("deprecation_message"),
            # Categorization
            type=platform_type or PlatformType.GENERAL,
            subcategory=data.get("subcategory", ""),
            tags=data.get("tags", []),
            # Integration
            supported_languages=data.get("supported_languages", []),
            supported_frameworks=data.get("supported_frameworks", []),
            integrations=data.get("integrations", []),
            # Documentation
            documentation_url=data.get("documentation_url", ""),
            setup_guide=data.get("setup_guide", ""),
            troubleshooting_guide=data.get("troubleshooting_guide", ""),
            # Ownership
            maintainer=data.get("maintainer", ""),
            source=source or PlatformSource.COMMUNITY,
            license=data.get("license", "MIT"),
            # Technical metadata
            min_autopr_version=data.get("min_autopr_version", "0.1.0"),
            dependencies=data.get("dependencies", {}),
            compatibility=data.get("compatibility", {}),
            # Nested configurations
            detection=data.get("detection", {}),
            project_config=data.get("project_config", {}),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_file(cls, file_path: Path) -> PlatformConfig:
        """Load a platform configuration from a JSON file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Use the filename (without .json) as the ID if not specified
            platform_id = data.get("id", file_path.stem)
            return cls.from_dict(platform_id, data)

        except (OSError, json.JSONDecodeError) as e:
            msg = f"Error loading platform config {file_path}: {e}"
            raise ValueError(msg)

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        result = {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "is_active": self.is_active,
            "priority": self.priority,
        }

        # Add nested sections if they're not empty
        if self.detection:
            result["detection"] = self.detection
        if self.project_config:
            result["project_config"] = self.project_config
        if self.metadata:
            result["metadata"] = self.metadata

        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert the configuration to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
