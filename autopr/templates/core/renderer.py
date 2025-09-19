"""
Template Renderer

Handles rendering of templates with variables and variants.
"""

import logging
from pathlib import Path
import re
from typing import Any

import jinja2
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateError

from autopr.templates.models import TemplateMetadata, TemplateVariant


logger = logging.getLogger(__name__)


class TemplateRenderer:
    """Handles rendering of templates with variables and variants."""

    def __init__(self, template_dirs: list[Path] | None = None):
        """Initialize the template renderer.

        Args:
            template_dirs: List of directories to search for templates.
        """
        self.template_dirs = template_dirs or []
        self._env = self._create_environment()

    def _create_environment(self) -> Environment:
        """Create and configure a Jinja2 environment."""
        # Create a custom loader that can handle multiple template directories
        loaders = [
            FileSystemLoader(str(template_dir))
            for template_dir in self.template_dirs
            if template_dir.exists()
        ]

        if not loaders:
            loaders = [FileSystemLoader(searchpath=Path.cwd())]

        env = Environment(
            loader=jinja2.ChoiceLoader(loaders),
            undefined=StrictUndefined,  # Raise error for undefined variables
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            autoescape=True,
        )

        # Add custom filters and tests
        self._add_custom_filters(env)
        self._add_custom_tests(env)

        return env

    def _add_custom_filters(self, env: Environment) -> None:
        """Add custom Jinja2 filters."""

        # Example filter: convert string to snake_case
        def to_snake_case(s: str) -> str:
            s = re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()
            return re.sub(r"[^\w]+", "_", s).strip("_")

        env.filters["to_snake_case"] = to_snake_case

        # Add more filters as needed...

    def _add_custom_tests(self, env: Environment) -> None:
        """Add custom Jinja2 tests."""

        # Example test: check if a value is a specific type
        def is_type(value: Any, type_name: str) -> bool:
            type_map = {
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
            }
            target_type = type_map.get(type_name)
            if target_type is None:
                return False
            return isinstance(value, target_type)

        env.tests["type"] = is_type

    def render_template(
        self,
        template_path: str | Path,
        variables: dict[str, Any] | None = None,
        variant: str | TemplateVariant | None = None,
        *,
        strict: bool = True,
    ) -> str:
        """Render a template with the given variables and variant.

        Args:
            template_path: Path to the template file, relative to template directories.
            variables: Dictionary of variables to pass to the template.
            variant: Optional variant to apply to the template.
            strict: If True, raise an error if the template is not found.

        Returns:
            Rendered template as a string.

        Raises:
            TemplateError: If the template cannot be rendered.
            FileNotFoundError: If the template file is not found and strict=True.
        """
        if variables is None:
            variables = {}

        # Convert Path to string if needed
        template_path = str(template_path)

        try:
            # Try to load the template
            template = self._env.get_template(template_path)
        except jinja2.TemplateNotFound as e:
            if strict:
                msg = f"Template not found: {template_path}"
                raise FileNotFoundError(msg) from e
            logger.warning(
                "Template not found, using empty template: %s", template_path
            )
            return ""

        # Apply variant modifications if specified
        if variant is not None:
            if isinstance(variant, str):
                # Treat unknown string variant as no-op by clearing variant
                variant = None

            # Apply variant modifications to variables
            if isinstance(variant, TemplateVariant):
                variables = self._apply_variant(variant, variables)

        try:
            # Render the template with the provided variables
            return template.render(**variables)
        except Exception as e:
            msg = f"Failed to render template {template_path}: {e}"
            raise TemplateError(msg) from e

    def _apply_variant(
        self, variant: TemplateVariant, variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply variant modifications to the variables.

        Args:
            variant: The variant to apply.
            variables: The current template variables.

        Returns:
            A new dictionary with the modified variables.
        """
        # Start with a copy of the original variables
        result = variables.copy()

        # Apply each modification from the variant
        for mod in variant.modifications:
            if not isinstance(mod, dict):
                continue

            op = mod.get("op", "set")
            path = mod.get("path", "").split(".")
            value = mod.get("value")

            if not path:
                continue

            # Navigate to the target in the variables
            target = result
            for part in path[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]

            # Apply the operation
            last_part = path[-1]
            if op == "set":
                target[last_part] = value
            elif (
                op == "update"
                and isinstance(target.get(last_part), dict)
                and isinstance(value, dict)
            ):
                target[last_part].update(value)
            elif op == "append" and isinstance(target.get(last_part), list):
                target[last_part].extend(value if isinstance(value, list) else [value])
            elif op == "prepend" and isinstance(target.get(last_part), list):
                target[last_part] = (
                    value if isinstance(value, list) else [value]
                ) + target[last_part]
            elif op == "delete" and last_part in target:
                del target[last_part]

        return result

    def render_template_metadata(
        self,
        template_metadata: TemplateMetadata,
        variables: dict[str, Any] | None = None,
        variant_name: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Render a template using its metadata.

        Args:
            template_metadata: The template metadata.
            variables: Variables to pass to the template.
            variant_name: Optional name of the variant to apply.

        Returns:
            A tuple of (rendered_content, used_variables)
        """
        if variables is None:
            variables = {}

        # Get the variant if specified
        variant = None
        if variant_name:
            variant = template_metadata.variants.get(variant_name)
            if variant is None:
                logger.warning(
                    "Variant '%s' not found in template '%s'",
                    variant_name,
                    template_metadata.id,
                )

        # Get the template path relative to the template directories
        template_path = template_metadata.source_path

        # Render the template
        rendered = self.render_template(
            template_path=template_path,
            variables=variables,
            variant=variant,
        )

        return rendered, variables
