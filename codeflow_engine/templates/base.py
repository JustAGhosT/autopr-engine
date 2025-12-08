"""
Base classes for template providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TemplateMetadata:
    """Metadata for a template."""

    template_id: str
    title: str
    description: str
    version: str
    author: str
    tags: list[str]
    category: str
    platforms: list[str]
    variables: dict[str, Any]
    variants: dict[str, dict[str, Any]] = field(default_factory=dict)
    documentation: str = ""
    discovery: dict[str, Any] = field(default_factory=dict)


class TemplateProvider(ABC):
    """Base class for template providers."""

    @abstractmethod
    def get_template(self, template_id: str) -> TemplateMetadata | None:
        """Get template metadata by ID."""

    @abstractmethod
    def get_all_templates(self) -> list[TemplateMetadata]:
        """Get all available templates."""

    @abstractmethod
    def search_templates(self, query: str) -> list[TemplateMetadata]:
        """Search for templates matching the query."""

    @abstractmethod
    def render_template(
        self, template_id: str, context: dict[str, Any], variant: str | None = None
    ) -> str:
        """Render a template with the given context and optional variant."""

    @abstractmethod
    def render_to_file(
        self,
        template_id: str,
        output_path: str | Path,
        context: dict[str, Any],
        variant: str | None = None,
        **kwargs,
    ) -> None:
        """Render a template to a file."""
