"""
Template Discovery System
========================

A modular system for discovering, analyzing, and generating documentation
for no-code platform templates.

Main Components:
- template_loader: Template loading and caching
- content_analyzer: Template content analysis and metadata extraction
- format_generators: Multiple output format generators
- template_validators: Template validation system
- quality_metrics: Quality scoring and analysis
- report_generators: Report generation in multiple formats
- qa_framework: Quality assurance framework
- docs_generator: Documentation generation system
- template_browser: Template discovery and browsing
"""

from .content_analyzer import ContentAnalyzer
from .docs_generator import TemplateDocumentationGenerator
from .format_generators import (
    BaseFormatGenerator,
    FormatGeneratorFactory,
    HTMLGenerator,
    JSONGenerator,
    MarkdownGenerator,
)
from .qa_framework import QualityAssuranceFramework

# Quality metrics have been moved to autopr.quality.template_metrics
# Import them directly from there when needed
from .report_generators import HTMLReportGenerator, JSONReportGenerator, MarkdownReportGenerator
from .report_generators import ReportGeneratorFactory as QAReportGeneratorFactory
from .template_browser import TemplateBrowser, TemplateInfo
from .template_loader import TemplateLoader
from .template_validators import ValidationIssue, ValidationSeverity, ValidatorRegistry
from .validation_rules import ValidationRuleLoader

__all__ = [
    # Format generators
    "BaseFormatGenerator",
    "ContentAnalyzer",
    "FormatGeneratorFactory",
    "HTMLGenerator",
    "HTMLReportGenerator",
    "JSONGenerator",
    # Report generators
    "JSONReportGenerator",
    "MarkdownGenerator",
    "MarkdownReportGenerator",
    "QAReportGeneratorFactory",
    "QualityAnalyzer",
    # Main systems
    "QualityAssuranceFramework",
    # Quality metrics
    "QualityMetrics",
    "QualityScorer",
    "TemplateBrowser",
    "TemplateDocumentationGenerator",
    "TemplateInfo",
    # Template loading and analysis
    "TemplateLoader",
    # Validation system
    "ValidationIssue",
    "ValidationRuleLoader",
    "ValidationSeverity",
    "ValidatorRegistry",
]
