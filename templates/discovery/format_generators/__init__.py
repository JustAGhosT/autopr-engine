#!/usr/bin/env python3
"""
Format Generators Package
=========================

Modular format generators for documentation generation.
Provides specialized generators for different output formats (Markdown, HTML, JSON).
"""

from discovery.format_generators.base import BaseFormatGenerator

# Core components
from discovery.format_generators.config import DocumentationConfig

# Factory and utilities
from discovery.format_generators.factory import (
    FormatGeneratorFactory,
    generate_documentation_index,
    generate_platform_guide,
)
from discovery.format_generators.html import HTMLGenerator
from discovery.format_generators.json_generator import JSONGenerator

# Format generators
from discovery.format_generators.markdown import MarkdownGenerator


# Main exports
__all__ = [
    # Base class
    "BaseFormatGenerator",
    # Configuration
    "DocumentationConfig",
    # Factory and utilities
    "FormatGeneratorFactory",
    "HTMLGenerator",
    "JSONGenerator",
    # Format generators
    "MarkdownGenerator",
    "generate_documentation_index",
    "generate_platform_guide",
]

# Version and metadata
__version__ = "1.0.0"
__author__ = "AutoPR Engine"
__description__ = "Modular format generators for documentation generation"
