#!/usr/bin/env python3
"""
HTML Format Generator Module
===========================

Generates documentation in HTML format.
"""

from typing import Any

from ..content_analyzer import TemplateAnalysis
from .base import BaseFormatGenerator
from .html_template_loader import YAMLHTMLTemplateLoader
from .markdown import MarkdownGenerator


class HTMLGenerator(BaseFormatGenerator):
    """Generates HTML documentation using YAML-based HTML templates.

    This class uses TemplateAnalysis objects from content_analyzer module.
    """

    def __init__(self, config: Any, template_loader: Any) -> None:
        """Initialize HTML generator with YAML template loader."""
        super().__init__(config, template_loader)
        self.html_template_loader = YAMLHTMLTemplateLoader()
        self.markdown_generator = MarkdownGenerator(config, template_loader)

    def generate_platform_guide(self, analysis: TemplateAnalysis) -> str:
        """Generate platform guide in HTML format using YAML template."""
        # Get markdown content and convert to HTML
        markdown_content = self.markdown_generator.generate_platform_guide(analysis)
        html_content = self._markdown_to_html(markdown_content)

        # Render using YAML template
        return self.html_template_loader.render_template(
            "platform_guide",
            platform_name=analysis.name.replace("_", " ").title(),
            content=html_content,
            custom_css=self.config.custom_css or "",
            platform_color=getattr(analysis, "primary_color", "#667eea"),
        )

    def generate_use_case_guide(self, analysis: TemplateAnalysis) -> str:
        """Generate use case guide in HTML format using YAML template."""
        markdown_content = self.markdown_generator.generate_use_case_guide(analysis)
        html_content = self._markdown_to_html(markdown_content)

        return self.html_template_loader.render_template(
            "use_case_guide",
            use_case_name=analysis.name.replace("_", " ").title(),
            content=html_content,
            custom_css=self.config.custom_css or "",
            use_case_category=getattr(analysis, "category", ""),
            complexity_level=getattr(analysis, "complexity", "Intermediate"),
        )

    def generate_integration_guide(self, analysis: TemplateAnalysis) -> str:
        """Generate integration guide in HTML format using YAML template."""
        markdown_content = self.markdown_generator.generate_integration_guide(analysis)
        html_content = self._markdown_to_html(markdown_content)

        return self.html_template_loader.render_template(
            "integration_guide",
            integration_name=analysis.name.replace("_", " ").title(),
            content=html_content,
            custom_css=self.config.custom_css or "",
            integration_type=getattr(analysis, "integration_type", "API"),
            difficulty_level=getattr(analysis, "difficulty", "Intermediate"),
        )

    def generate_main_index(self, analyses: list[TemplateAnalysis]) -> str:
        """Generate main documentation index in HTML format using YAML template."""
        markdown_content = self.markdown_generator.generate_main_index(analyses)
        html_content = self._markdown_to_html(markdown_content)

        # Calculate statistics for the template
        categories = {a.category for a in analyses}
        # Get platform analyses (templates with category 'platform')
        platform_analyses = [a for a in analyses if a.category == "platform"]
        platforms = {a.name for a in platform_analyses}

        return self.html_template_loader.render_template(
            "documentation_index",
            content=html_content,
            total_templates=len(analyses),
            total_categories=len(categories),
            total_platforms=len(platforms),
            custom_css=self.config.custom_css or "",
            last_updated=self._get_current_date(),
        )

    def generate_comparison_guide(self, platform_analyses: list[TemplateAnalysis]) -> str:
        """Generate platform comparison guide in HTML format using YAML template."""
        markdown_content = self.markdown_generator.generate_comparison_guide(platform_analyses)
        html_content = self._markdown_to_html(markdown_content)

        return self.html_template_loader.render_template(
            "base_layout",
            title="Platform Comparison Guide",
            content=html_content,
            custom_css=self.config.custom_css or "",
        )

    def _get_current_date(self) -> str:
        """Get current date in a readable format."""
        from datetime import datetime

        return datetime.now().strftime("%B %d, %Y")

    def _markdown_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML conversion."""
        # This is a simplified conversion - in production, use a proper markdown parser
        html = markdown

        # Headers
        html = html.replace("### ", "<h3>").replace("\n", "</h3>\n", html.count("### "))
        html = html.replace("## ", "<h2>").replace("\n", "</h2>\n", html.count("## "))
        html = html.replace("# ", "<h1>").replace("\n", "</h1>\n", html.count("# "))

        # Lists
        lines = html.split("\n")
        in_list = False
        result_lines = []

        for line in lines:
            if line.strip().startswith("- "):
                if not in_list:
                    result_lines.append("<ul>")
                    in_list = True
                result_lines.append(f"<li>{line.strip()[2:]}</li>")
            else:
                if in_list:
                    result_lines.append("</ul>")
                    in_list = False
                result_lines.append(line)

        if in_list:
            result_lines.append("</ul>")

        # Paragraphs
        html = "\n".join(result_lines)
        paragraphs = html.split("\n\n")
        html_paragraphs = []

        for p in paragraphs:
            p = p.strip()
            if p and not p.startswith("<"):
                html_paragraphs.append(f"<p>{p}</p>")
            else:
                html_paragraphs.append(p)

        return "\n\n".join(html_paragraphs)
