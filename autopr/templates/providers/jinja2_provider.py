"""
Jinja2 template provider implementation.
"""

import logging
import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined
import yaml

from ..base import TemplateMetadata, TemplateProvider

logger = logging.getLogger(__name__)


class Jinja2TemplateProvider(TemplateProvider):
    """Template provider using Jinja2 for rendering."""

    def __init__(self, template_dirs=None):
        """Initialize the Jinja2 template provider.

        Args:
            template_dirs: List of directories to search for templates
        """
        self.template_dirs = [Path(d) for d in (template_dirs or [])]
        self.template_cache = {}
        self.metadata_cache = {}

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader([str(d) for d in self.template_dirs]),
            undefined=StrictUndefined,
            autoescape=True,
            keep_trailing_newline=True,
        )

        # Add custom filters and globals
        self._add_custom_filters()
        self._add_custom_globals()

        # Load all templates
        self._load_all_templates()

    def _add_custom_filters(self):
        """Add custom Jinja2 filters."""

        def datetime_format(value, format_str="%Y-%m-%d %H:%M:%S"):
            """Format a datetime object."""
            if value is None:
                return ""
            if isinstance(value, str):
                return value
            return value.strftime(format_str)

        self.env.filters["datetime"] = datetime_format

    def _add_custom_globals(self):
        """Add custom Jinja2 globals."""
        from datetime import datetime

        self.env.globals.update({"now": datetime.now, "env": os.environ.get})

    def _load_template_metadata(self, template_dir: Path) -> dict[str, Any] | None:
        """Load template metadata from a directory."""
        metadata_file = template_dir / f"{template_dir.name}.meta.yaml"
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.exception(f"Error loading metadata from {metadata_file}: {e}")
            return None

    def _load_all_templates(self):
        """Load all templates from the template directories."""
        self.template_cache.clear()
        self.metadata_cache.clear()

        for template_dir in self.template_dirs:
            if not template_dir.exists():
                logger.warning(f"Template directory not found: {template_dir}")
                continue

            for root, _, files in os.walk(template_dir):
                root_path = Path(root)

                # Skip hidden directories
                if root_path.name.startswith("."):
                    continue

                # Look for template files
                for file in files:
                    if file.endswith(".j2") and not file.startswith("_"):
                        template_id = f"{root_path.relative_to(template_dir)}/{file[:-3]}"
                        self._load_template(template_id, root_path, file)

    def _load_template(self, template_id: str, root_path: Path, filename: str) -> bool:
        """Load a single template into the cache."""
        try:
            # Load metadata
            metadata = self._load_template_metadata(root_path)
            if not metadata:
                return False

            # Create template metadata object
            template_metadata = TemplateMetadata(
                template_id=template_id,
                title=metadata.get("title", template_id),
                description=metadata.get("description", ""),
                version=metadata.get("version", "1.0.0"),
                author=metadata.get("author", "Unknown"),
                tags=metadata.get("tags", []),
                category=metadata.get("category", "uncategorized"),
                platforms=metadata.get("platforms", ["all"]),
                variables=metadata.get("variables", {}),
                variants=metadata.get("variants", {}),
                documentation=metadata.get("documentation", ""),
                discovery=metadata.get("discovery", {}),
            )

            # Add to caches
            self.metadata_cache[template_id] = template_metadata
            self.template_cache[template_id] = {
                "path": root_path / filename,
                "metadata": template_metadata,
            }

            return True

        except Exception as e:
            logger.exception(f"Error loading template {template_id}: {e}")
            return False

    def get_template(self, template_id: str) -> TemplateMetadata | None:
        """Get template metadata by ID."""
        return self.metadata_cache.get(template_id)

    def get_all_templates(self) -> list[TemplateMetadata]:
        """Get all available templates."""
        return list(self.metadata_cache.values())

    def search_templates(self, query: str) -> list[TemplateMetadata]:
        """Search for templates matching the query."""
        query = query.lower()

        return [
            metadata
            for metadata in self.metadata_cache.values()
            if query in metadata.template_id.lower()
            or query in metadata.title.lower()
            or query in metadata.description.lower()
            or any(query in tag.lower() for tag in metadata.tags)
        ]

    def render_template(
        self, template_id: str, context: dict[str, Any], variant: str | None = None
    ) -> str:
        """Render a template with the given context and optional variant."""
        if template_id not in self.template_cache:
            msg = f"Template not found: {template_id}"
            raise ValueError(msg)

        # Get template info
        template_info = self.template_cache[template_id]
        metadata = template_info["metadata"]

        # Apply variant if specified
        if variant and variant in metadata.variants:
            variant_data = metadata.variants[variant]
            if "variables" in variant_data:
                context = {**context, **variant_data["variables"]}

        # Add metadata to context
        context["template"] = metadata.__dict__

        try:
            # Get the template path relative to the template directory
            rel_path = template_info["path"].relative_to(
                next(d for d in self.template_dirs if d in template_info["path"].parents)
            )

            # Load and render the template
            template = self.env.get_template(str(rel_path))
            return template.render(**context)

        except Exception as e:
            logger.exception(f"Error rendering template {template_id}: {e}")
            raise

    def render_to_file(
        self,
        template_id: str,
        output_path: str | Path,
        context: dict[str, Any],
        variant: str | None = None,
        **kwargs,
    ) -> None:
        """Render a template to a file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        rendered = self.render_template(template_id, context, variant)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)
