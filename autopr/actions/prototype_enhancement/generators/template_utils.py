"""
Template Utilities Module

Provides template management and rendering functionality.
"""

from pathlib import Path
from typing import Any

import jinja2

from autopr.actions.prototype_enhancement.template_metadata import (
    TemplateMetadata,
    TemplateRegistry,
)


class TemplateManager:
    """Manages template loading and rendering with support for variants and inheritance."""

    def __init__(self, templates_dir: str):
        """Initialize the template manager.

        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = Path(templates_dir)
        self.jinja_env = self._create_jinja_environment()
        self.template_registry = TemplateRegistry(templates_dir)

    def _create_jinja_environment(self) -> jinja2.Environment:
        """Create and configure a Jinja2 environment.

        Returns:
            Configured Jinja2 environment
        """
        # Create a custom loader that can handle our template structure
        loader = jinja2.FileSystemLoader(
            searchpath=str(self.templates_dir), encoding="utf-8", followlinks=True
        )

        return jinja2.Environment(
            loader=loader,
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Add custom filters and globals here if needed
        # env.filters['custom_filter'] = custom_filter_function

    def render(
        self,
        template_key: str,
        variables: dict[str, Any] | None = None,
        variants: list[str] | None = None,
    ) -> str | None:
        """Render a template with the given variables and variants.

        Args:
            template_key: Key identifying the template (e.g., 'docker/Dockerfile')
            variables: Variables to pass to the template
            variants: List of variants to apply
        Returns:
            Rendered template content, or None if template not found
        """
        if variables is None:
            variables = {}
        # Get template metadata
        template_meta = self.template_registry.get_template(template_key)
        if not template_meta:
            return None

        # Apply variants if specified
        if variants:
            template_meta = self._apply_variants(template_meta, variants)

        # Get the template content
        template_path = self.templates_dir / template_meta.path
        if not template_path.exists():
            return None

        template_content = template_path.read_text(encoding="utf-8")

        # If it's a Jinja2 template (has .j2 extension), render it
        if template_path.suffix == ".j2":
            template = self.jinja_env.from_string(template_content)
            return template.render(**variables)

        # Otherwise, return the raw content
        return template_content

    def _apply_variants(
        self, template_meta: TemplateMetadata, variants: list[str]
    ) -> TemplateMetadata:
        """Apply variants to a template metadata.

        Args:
            template_meta: Original template metadata
            variants: List of variant names to apply

        Returns:
            New template metadata with variants applied
        """
        # Start with a copy of the original metadata
        result = template_meta.copy()
        # Apply each variant in order
        for variant in variants:
            if variant in template_meta.variants:
                variant_meta = template_meta.variants[variant]
                # Merge the variant's variables with the current ones
                if variant_meta.variables:
                    result.variables = {**result.variables, **variant_meta.variables}
                # Apply any template overrides
                if variant_meta.template:
                    result.template = variant_meta.template
        return result
