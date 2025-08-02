#!/usr/bin/env python3
"""
Format Generator Factory Module
==============================

Factory for creating format generators and convenience functions.
"""

from ..content_analyzer import TemplateAnalysis
from ..template_loader import TemplateLoader
from .base import BaseFormatGenerator
from .config import DocumentationConfig
from .html import HTMLGenerator
from .json_generator import JSONGenerator
from .markdown import MarkdownGenerator


class FormatGeneratorFactory:
    """Factory for creating format generators."""

    @staticmethod
    def create_generator(
        format_type: str, config: DocumentationConfig, template_loader: TemplateLoader
    ) -> BaseFormatGenerator:
        """Create a format generator based on the specified type.

        Args:
            format_type: Type of format ('markdown', 'html', 'json')
            config: Documentation configuration
            template_loader: Template loader instance

        Returns:
            Format generator instance
        """
        generators = {"markdown": MarkdownGenerator, "html": HTMLGenerator, "json": JSONGenerator}

        generator_class = generators.get(format_type.lower(), MarkdownGenerator)
        return generator_class(config, template_loader)  # type: ignore


# Convenience functions
def generate_platform_guide(
    analysis: TemplateAnalysis,
    format_type: str = "markdown",
    config: DocumentationConfig | None = None,
    template_loader: TemplateLoader | None = None,
) -> str:
    """Generate a platform guide in the specified format."""
    if config is None:
        config = DocumentationConfig(output_format=format_type)
    if template_loader is None:
        template_loader = TemplateLoader()

    generator = FormatGeneratorFactory.create_generator(format_type, config, template_loader)
    return generator.generate_platform_guide(analysis)


def generate_documentation_index(
    analyses: list[TemplateAnalysis],
    format_type: str = "markdown",
    config: DocumentationConfig | None = None,
    template_loader: TemplateLoader | None = None,
) -> str:
    """Generate a documentation index in the specified format."""
    if config is None:
        config = DocumentationConfig(output_format=format_type)
    if template_loader is None:
        template_loader = TemplateLoader()

    generator = FormatGeneratorFactory.create_generator(format_type, config, template_loader)

    # Handle JSON format specially for summary data
    if format_type.lower() == "json" and hasattr(generator, "generate_summary_data"):
        return generator.generate_summary_data(analyses)  # type: ignore
    return generator.generate_main_index(analyses)
