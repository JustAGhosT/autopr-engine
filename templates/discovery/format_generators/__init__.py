#!/usr/bin/env python3
"""
Format Generators Package
=========================

Modular format generators for documentation generation.
Provides specialized generators for different output formats (Markdown, HTML, JSON).
"""

from .base import BaseFormatGenerator

# Core components
from .config import DocumentationConfig

# Factory and utilities
from .factory import FormatGeneratorFactory, generate_documentation_index, generate_platform_guide
from .html import HTMLGenerator
from .json_generator import JSONGenerator

# Format generators
from .markdown import MarkdownGenerator

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
