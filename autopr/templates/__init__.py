"""
AutoPR Template System

This module provides a flexible template system with support for multiple template providers.
The default provider uses Jinja2 for template rendering, with optional integration
with the AutoWeave template service.
"""

import logging
import os
from pathlib import Path
from typing import Any

from autopr.templates.base import TemplateMetadata, TemplateProvider
from autopr.templates.providers.autoweave_provider import AutoWeaveProvider
from autopr.templates.providers.jinja2_provider import Jinja2TemplateProvider


# Set up logger
logger = logging.getLogger(__name__)

# Default template directories
DEFAULT_TEMPLATE_DIRS = [
    Path(__file__).parent / "templates",
    Path.cwd() / "templates",
    Path.home() / ".autopr" / "templates",
]


class TemplateSystem:
    """Main template system that manages multiple template providers.

    This class provides a unified interface to work with different template
    providers, with the ability to add, remove, and switch between providers.
    """

    def __init__(self, template_dirs=None, default_provider: str = "jinja2"):
        """Initialize the template system.

        Args:
            template_dirs: List of directories to search for templates.
                          If None, uses default template directories.
            default_provider: Default provider to use ('jinja2' or 'autoweave')
        """
        self.providers: dict[str, TemplateProvider] = {}
        self.default_provider = default_provider

        # Initialize default providers
        self._initialize_default_providers(template_dirs)

    def _initialize_default_providers(self, template_dirs):
        """Initialize the default template providers."""
        # Use provided template dirs or default ones
        if template_dirs is None:
            template_dirs = [d for d in DEFAULT_TEMPLATE_DIRS if d.exists()]

        # Add Jinja2 provider (always available)
        self.add_provider("jinja2", Jinja2TemplateProvider(template_dirs=template_dirs))

        # Try to add AutoWeave provider if configured
        autoweave_api_key = os.environ.get("AUTOWEAVE_API_KEY")
        if autoweave_api_key:
            try:
                self.add_provider(
                    "autoweave", AutoWeaveProvider(api_key=autoweave_api_key)
                )
            except Exception:
                logger.warning(
                    "Failed to initialize AutoWeave provider: %s", "autoweave"
                )

    def add_provider(self, name: str, provider: TemplateProvider) -> None:
        """Add a template provider.

        Args:
            name: Provider name (must be unique)
            provider: TemplateProvider instance
        """
        if not isinstance(provider, TemplateProvider):
            msg = "Provider must be an instance of TemplateProvider"
            raise ValueError(msg)
        self.providers[name] = provider
        logger.info("Added template provider: %s", name)

    def remove_provider(self, name: str) -> bool:
        """Remove a template provider.

        Args:
            name: Name of the provider to remove

        Returns:
            True if provider was removed, False if not found
        """
        if name in self.providers:
            del self.providers[name]
            logger.info("Removed template provider: %s", name)
            return True
        return False

    def get_provider(self, name: str | None = None) -> TemplateProvider:
        """Get a template provider by name.

        Args:
            name: Provider name, or None to use default provider

        Returns:
            TemplateProvider instance

        Raises:
            ValueError: If provider is not found
        """
        name = name or self.default_provider
        if name not in self.providers:
            msg = f"Template provider not found: {name}"
            raise ValueError(msg)
        return self.providers[name]

    def get_template(
        self, template_id: str, provider: str | None = None
    ) -> TemplateMetadata | None:
        """Get template metadata by ID.

        Args:
            template_id: Template identifier
            provider: Provider name, or None to use default provider

        Returns:
            TemplateMetadata if found, None otherwise
        """
        return self.get_provider(provider).get_template(template_id)

    def get_all_templates(self, provider: str | None = None) -> list[TemplateMetadata]:
        """Get all available templates.

        Args:
            provider: Provider name, or None to use default provider

        Returns:
            List of TemplateMetadata objects
        """
        return self.get_provider(provider).get_all_templates()

    def search_templates(
        self, query: str, provider: str | None = None
    ) -> list[TemplateMetadata]:
        """Search for templates matching the query.

        Args:
            query: Search query string
            provider: Provider name, or None to use default provider

        Returns:
            List of matching TemplateMetadata objects
        """
        return self.get_provider(provider).search_templates(query)

    def render_template(
        self,
        template_id: str,
        context: dict[str, Any],
        variant: str | None = None,
        provider: str | None = None,
    ) -> str:
        """Render a template with the given context and optional variant.

        Args:
            template_id: Template identifier
            context: Template variables
            variant: Optional variant name
            provider: Provider name, or None to use default provider

        Returns:
            Rendered template as a string

        Raises:
            ValueError: If template is not found or rendering fails
        """
        return self.get_provider(provider).render_template(
            template_id, context, variant
        )

    def render_to_file(
        self,
        template_id: str,
        output_path: str | Path,
        context: dict[str, Any],
        variant: str | None = None,
        provider: str | None = None,
        **kwargs,
    ) -> None:
        """Render a template to a file.

        Args:
            template_id: Template identifier
            output_path: Output file path
            context: Template variables
            variant: Optional variant name
            provider: Provider name, or None to use default provider
            **kwargs: Additional provider-specific arguments
        """
        return self.get_provider(provider).render_to_file(
            template_id, output_path, context, variant, **kwargs
        )


# Create a default instance for convenience
default_template_system = TemplateSystem()

# Export public API
__all__ = [
    "AutoWeaveProvider",
    "Jinja2TemplateProvider",
    "TemplateMetadata",
    "TemplateProvider",
    "TemplateSystem",
    "default_template_system",
]
