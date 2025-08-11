"""
Template Registry

Manages template discovery, loading, and caching.
"""
# mypy: disable-error-code=import-untyped

import logging
import os
from pathlib import Path
from typing import Any, Self, TypeVar

from autopr.templates.models import (
    TemplateMetadata,
    TemplateType,
    TemplateVariable,
    TemplateVariableType,
    TemplateVariant,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="TemplateRegistry")


class TemplateRegistry:
    """Registry for managing template discovery, loading, and caching."""

    def __init__(self, template_dirs: list[Path] | None = None):
        """Initialize the template registry.

        Args:
            template_dirs: List of directories to search for templates.
        """
        self.template_dirs = template_dirs or []
        self._templates: dict[str, TemplateMetadata] = {}
        self._loaded = False

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> Self:
        """Create a TemplateRegistry instance from a configuration dictionary."""
        template_dirs = [Path(d) for d in config.get("template_dirs", [])]
        return cls(template_dirs=template_dirs)

    def add_template_dir(self, template_dir: Path) -> None:
        """Add a directory to search for templates."""
        if template_dir not in self.template_dirs:
            self.template_dirs.append(template_dir)

    def load_all(self) -> None:
        """Load all templates from the configured directories."""
        if self._loaded:
            return

        self._templates = {}

        for template_dir in self.template_dirs:
            if not template_dir.exists():
                logger.warning("Template directory does not exist: %s", template_dir)
                continue

            self._load_templates_from_dir(template_dir)

        self._loaded = True

    def _load_templates_from_dir(self, base_dir: Path) -> None:
        """Recursively load templates from a directory."""
        for root, _, files in os.walk(base_dir):
            root_path = Path(root)

            # Look for template metadata files
            for file in files:
                if not file.endswith((".yaml", ".yml")):
                    continue

                metadata_path = root_path / file
                try:
                    self._load_template_metadata(metadata_path, base_dir)
                except Exception:
                    logger.exception(
                        "Failed to load template from %s", metadata_path
                    )

    def _load_template_metadata(self, metadata_path: Path, base_dir: Path) -> None:
        """Load template metadata from a YAML file."""
        # Local runtime import via importlib to avoid mypy 'import-untyped' on PyYAML
        import importlib
        from typing import Any, cast
        _yaml = cast(Any, importlib.import_module("yaml"))

        with metadata_path.open(encoding="utf-8") as f:
            metadata_dict = _yaml.safe_load(f) or {}

        # Calculate template ID and source path
        rel_path = metadata_path.relative_to(base_dir)
        template_id = str(rel_path.with_suffix("")).replace(os.sep, ".")
        source_path = metadata_path.with_suffix("")  # Remove .yaml/.yml extension

        # Parse template type
        template_type = TemplateType(metadata_dict.get("type", "file").lower())

        # Parse variables
        variables = self._parse_variables(metadata_dict.get("variables", {}))

        # Parse variants
        variants = self._parse_variants(metadata_dict.get("variants", {}), variables)

        # Create template metadata
        template = TemplateMetadata(
            id=template_id,
            name=metadata_dict.get("name", template_id),
            description=metadata_dict.get("description", ""),
            type=template_type,
            source_path=source_path,
            category=metadata_dict.get("category", ""),
            tags=metadata_dict.get("tags", []),
            platforms=metadata_dict.get("platforms", []),
            dependencies=metadata_dict.get("dependencies", {}),
            variables=variables,
            variants=variants,
            version=metadata_dict.get("version", "1.0.0"),
            min_auto_pr_version=metadata_dict.get("min_auto_pr_version"),
            examples=metadata_dict.get("examples", []),
            notes=metadata_dict.get("notes", []),
        )

        self._templates[template_id] = template

    def _parse_variables(self, variables_dict: dict) -> dict[str, TemplateVariable]:
        """Parse template variables from a dictionary."""
        variables = {}

        for name, config in variables_dict.items():
            if not isinstance(config, dict):
                config = {"type": "string", "default": config}

            var_type = TemplateVariableType(config.get("type", "string").lower())

            # Handle choices for CHOICE type
            choices = None
            if var_type == TemplateVariableType.CHOICE:
                choices = config.get("choices")
                if not isinstance(choices, list):
                    choices = [choices] if choices is not None else None

            variables[name] = TemplateVariable(
                name=name,
                type=var_type,
                description=config.get("description", ""),
                default=config.get("default"),
                required=config.get("required", False),
                choices=choices,
                min_length=config.get("min_length"),
                max_length=config.get("max_length"),
                pattern=config.get("pattern"),
            )

        return variables

    def _parse_variants(
        self, variants_dict: dict, base_variables: dict[str, TemplateVariable]
    ) -> dict[str, TemplateVariant]:
        """Parse template variants from a dictionary."""
        variants = {}

        for name, config in variants_dict.items():
            if not isinstance(config, dict):
                config = {}

            # Create a copy of base variables that can be modified by the variant
            variant_vars = base_variables.copy()

            # Apply variable overrides from the variant
            if "variables" in config:
                variant_vars.update(self._parse_variables(config["variables"]))

            variants[name] = TemplateVariant(
                name=name,
                description=config.get("description", ""),
                modifications=config.get("modifications", []),
                variables=variant_vars,
            )

        return variants

    def get_template(self, template_id: str) -> TemplateMetadata | None:
        """Get a template by ID."""
        if not self._loaded:
            self.load_all()
        return self._templates.get(template_id)

    def find_templates(
        self,
        search: str | None = None,
        template_type: TemplateType | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        platform: str | None = None,
    ) -> list[TemplateMetadata]:
        """Find templates matching the given criteria."""
        if not self._loaded:
            self.load_all()

        results = []

        for template in self._templates.values():
            # Filter by search term
            if (
                search
                and search.lower() not in (template.name + " " + template.description).lower()
            ):
                continue

            # Filter by type
            if template_type is not None and template.type != template_type:
                continue

            # Filter by category
            if category and template.category.lower() != category.lower():
                continue

            # Filter by tags (all must match)
            if tags and not all(tag.lower() in [t.lower() for t in template.tags] for tag in tags):
                continue

            # Filter by platform
            if platform and platform.lower() not in [p.lower() for p in template.platforms]:
                continue

            results.append(template)

        return results

    def get_all_templates(self) -> list[TemplateMetadata]:
        """Get all available templates."""
        if not self._loaded:
            self.load_all()
        return list(self._templates.values())

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._templates = {}
        self._loaded = False
