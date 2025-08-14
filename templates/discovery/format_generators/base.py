#!/usr/bin/env python3
"""
Base Format Generator Module
===========================

Abstract base class for format generators.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from discovery.content_analyzer import TemplateAnalysis
from discovery.template_loader import TemplateLoader

from .config import DocumentationConfig


class BaseFormatGenerator(ABC):
    """Base class for format generators."""

    def __init__(self, config: DocumentationConfig, template_loader: TemplateLoader) -> None:
        """Initialize the format generator."""
        self.config = config
        self.template_loader = template_loader

    def generate_content(self, template_name: str, **kwargs: Any) -> str:
        """Generate content using a template."""
        # Add common variables
        kwargs.setdefault("generation_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        kwargs.setdefault("config", self.config)

        return self.template_loader.render_template(template_name, **kwargs)

    @abstractmethod
    def generate_platform_guide(self, analysis: TemplateAnalysis) -> str:
        """Generate platform guide documentation."""

    @abstractmethod
    def generate_use_case_guide(self, analysis: TemplateAnalysis) -> str:
        """Generate use case guide documentation."""

    @abstractmethod
    def generate_integration_guide(self, analysis: TemplateAnalysis) -> str:
        """Generate integration guide documentation."""

    @abstractmethod
    def generate_main_index(self, analyses: list[TemplateAnalysis]) -> str:
        """Generate main documentation index."""

    @abstractmethod
    def generate_comparison_guide(self, platform_analyses: list[TemplateAnalysis]) -> str:
        """Generate platform comparison guide."""
