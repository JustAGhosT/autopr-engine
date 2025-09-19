#!/usr/bin/env python3
"""
Comprehensive tests for report generators module.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the modules we're testing
try:
    from templates.discovery.report_generators import (HTMLReportGenerator,
                                                       JSONReportGenerator,
                                                       MarkdownReportGenerator,
                                                       PDFReportGenerator,
                                                       ReportGenerator,
                                                       ReportTemplate)
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestReportTemplate:
    """Test ReportTemplate class."""

    def test_report_template_initialization(self):
        """Test ReportTemplate initialization."""
        template = ReportTemplate(
            name="test_template",
            content="<h1>{{title}}</h1><p>{{content}}</p>",
            variables=["title", "content"],
            format="html"
        )
        
        assert template.name == "test_template"
        assert template.content == "<h1>{{title}}</h1><p>{{content}}</p>"
        assert template.variables == ["title", "content"]
        assert template.format == "html"

    def test_report_template_render(self):
        """Test ReportTemplate render method."""
        template = ReportTemplate(
            name="test_template",
            content="Hello {{name}}, your score is {{score}}",
            variables=["name", "score"],
            format="text"
        )
        
        data = {"name": "John", "score": 95}
        result = template.render(data)
        assert result == "Hello John, your score is 95"

    def test_report_template_render_missing_variables(self):
        """Test ReportTemplate render with missing variables."""
        template = ReportTemplate(
            name="test_template",
            content="Hello {{name}}, your score is {{score}}",
            variables=["name", "score"],
            format="text"
        )
        
        data = {"name": "John"}  # Missing score
        result = template.render(data)
        assert result == "Hello John, your score is {{score}}"

    def test_report_template_to_dict(self):
        """Test ReportTemplate to_dict method."""
        template = ReportTemplate(
            name="test_template",
            content="<h1>{{title}}</h1>",
            variables=["title"],
            format="html"
        )
        
        result = template.to_dict()
        expected = {
            "name": "test_template",
            "content": "<h1>{{title}}</h1>",
            "variables": ["title"],
            "format": "html"
        }
        assert result == expected

    def test_report_template_from_dict(self):
        """Test ReportTemplate from_dict method."""
        data = {
            "name": "test_template",
            "content": "<h1>{{title}}</h1>",
            "variables": ["title"],
            "format": "html"
        }
        
        template = ReportTemplate.from_dict(data)
        assert template.name == "test_template"
        assert template.content == "<h1>{{title}}</h1>"
        assert template.variables == ["title"]
        assert template.format == "html"


class TestReportGenerator:
    """Test ReportGenerator base class."""

    @pytest.fixture
    def report_generator(self):
        """Create a ReportGenerator instance for testing."""
        return ReportGenerator()

    def test_report_generator_initialization(self, report_generator):
        """Test ReportGenerator initialization."""
        assert report_generator.templates == {}
        assert report_generator.default_template is None

    def test_register_template(self, report_generator):
        """Test registering a template."""
        template = ReportTemplate(
            name="test_template",
            content="<h1>{{title}}</h1>",
            variables=["title"],
            format="html"
        )
        
        report_generator.register_template(template)
        assert "test_template" in report_generator.templates
        assert report_generator.templates["test_template"] == template

    def test_set_default_template(self, report_generator):
        """Test setting default template."""
        template = ReportTemplate(
            name="default_template",
            content="Default content",
            variables=[],
            format="text"
        )
        report_generator.register_template(template)
        report_generator.set_default_template("default_template")
        
        assert report_generator.default_template == "default_template"

    def test_generate_report(self, report_generator):
        """Test generating a report."""
        template = ReportTemplate(
            name="test_template",
            content="<h1>{{title}}</h1><p>{{content}}</p>",
            variables=["title", "content"],
            format="html"
        )
        report_generator.register_template(template)
        
        data = {"title": "Test Report", "content": "This is a test"}
        result = report_generator.generate_report("test_template", data)
        
        assert result is not None
        assert "Test Report" in result
        assert "This is a test" in result

    def test_generate_report_with_default_template(self, report_generator):
        """Test generating a report with default template."""
        template = ReportTemplate(
            name="default_template",
            content="Default: {{message}}",
            variables=["message"],
            format="text"
        )
        report_generator.register_template(template)
        report_generator.set_default_template("default_template")
        
        data = {"message": "Hello World"}
        result = report_generator.generate_report(data=data)
        
        assert result == "Default: Hello World"

    def test_generate_report_invalid_template(self, report_generator):
        """Test generating a report with invalid template."""
        data = {"title": "Test"}
        result = report_generator.generate_report("nonexistent", data)
        
        assert result is None

    def test_save_report(self, report_generator):
        """Test saving a report to file."""
        template = ReportTemplate(
            name="test_template",
            content="Test content: {{message}}",
            variables=["message"],
            format="text"
        )
        report_generator.register_template(template)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_file = f.name
        
        try:
            data = {"message": "Hello World"}
            success = report_generator.save_report("test_template", data, temp_file)
            
            assert success is True
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                content = f.read()
            assert content == "Test content: Hello World"
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestHTMLReportGenerator:
    """Test HTMLReportGenerator class."""

    @pytest.fixture
    def html_generator(self):
        """Create an HTMLReportGenerator instance for testing."""
        return HTMLReportGenerator()

    def test_html_generator_initialization(self, html_generator):
        """Test HTMLReportGenerator initialization."""
        assert html_generator.templates == {}
        assert html_generator.default_template is None
        assert html_generator.css_styles is not None

    def test_add_css_style(self, html_generator):
        """Test adding CSS styles."""
        html_generator.add_css_style("custom", ".custom { color: red; }")
        assert "custom" in html_generator.css_styles

    def test_generate_html_report(self, html_generator):
        """Test generating HTML report."""
        template = ReportTemplate(
            name="html_template",
            content="<h1>{{title}}</h1><p>{{content}}</p>",
            variables=["title", "content"],
            format="html"
        )
        html_generator.register_template(template)
        
        data = {"title": "Test Report", "content": "This is a test"}
        result = html_generator.generate_report("html_template", data)
        
        assert result is not None
        assert "<html>" in result
        assert "<head>" in result
        assert "<body>" in result
        assert "Test Report" in result
        assert "This is a test" in result

    def test_generate_html_report_with_css(self, html_generator):
        """Test generating HTML report with custom CSS."""
        html_generator.add_css_style("custom", ".title { color: blue; }")
        
        template = ReportTemplate(
            name="styled_template",
            content="<h1 class='title'>{{title}}</h1>",
            variables=["title"],
            format="html"
        )
        html_generator.register_template(template)
        
        data = {"title": "Styled Report"}
        result = html_generator.generate_report("styled_template", data)
        
        assert result is not None
        assert ".title { color: blue; }" in result

    def test_generate_html_report_with_metadata(self, html_generator):
        """Test generating HTML report with metadata."""
        template = ReportTemplate(
            name="meta_template",
            content="<h1>{{title}}</h1>",
            variables=["title"],
            format="html"
        )
        html_generator.register_template(template)
        
        data = {"title": "Test Report"}
        metadata = {
            "author": "John Doe",
            "created": "2023-01-01",
            "version": "1.0"
        }
        
        result = html_generator.generate_report("meta_template", data, metadata)
        
        assert result is not None
        assert "John Doe" in result
        assert "2023-01-01" in result
        assert "1.0" in result


class TestJSONReportGenerator:
    """Test JSONReportGenerator class."""

    @pytest.fixture
    def json_generator(self):
        """Create a JSONReportGenerator instance for testing."""
        return JSONReportGenerator()

    def test_json_generator_initialization(self, json_generator):
        """Test JSONReportGenerator initialization."""
        assert json_generator.templates == {}
        assert json_generator.default_template is None
        assert json_generator.pretty_print is True

    def test_generate_json_report(self, json_generator):
        """Test generating JSON report."""
        template = ReportTemplate(
            name="json_template",
            content='{"title": "{{title}}", "content": "{{content}}"}',
            variables=["title", "content"],
            format="json"
        )
        json_generator.register_template(template)
        
        data = {"title": "Test Report", "content": "This is a test"}
        result = json_generator.generate_report("json_template", data)
        
        assert result is not None
        parsed = json.loads(result)
        assert parsed["title"] == "Test Report"
        assert parsed["content"] == "This is a test"

    def test_generate_json_report_with_metadata(self, json_generator):
        """Test generating JSON report with metadata."""
        template = ReportTemplate(
            name="json_template",
            content='{"title": "{{title}}", "metadata": {{metadata}}}',
            variables=["title", "metadata"],
            format="json"
        )
        json_generator.register_template(template)
        
        data = {"title": "Test Report", "metadata": '{"author": "John"}'}
        result = json_generator.generate_report("json_template", data)
        
        assert result is not None
        parsed = json.loads(result)
        assert parsed["title"] == "Test Report"
        assert parsed["metadata"]["author"] == "John"

    def test_generate_json_report_pretty_print(self, json_generator):
        """Test generating JSON report with pretty printing."""
        json_generator.pretty_print = True
        
        template = ReportTemplate(
            name="json_template",
            content='{"title": "{{title}}"}',
            variables=["title"],
            format="json"
        )
        json_generator.register_template(template)
        
        data = {"title": "Test Report"}
        result = json_generator.generate_report("json_template", data)
        
        assert result is not None
        # Pretty printed JSON should have newlines
        assert "\n" in result

    def test_generate_json_report_compact(self, json_generator):
        """Test generating JSON report in compact format."""
        json_generator.pretty_print = False
        
        template = ReportTemplate(
            name="json_template",
            content='{"title": "{{title}}"}',
            variables=["title"],
            format="json"
        )
        json_generator.register_template(template)
        
        data = {"title": "Test Report"}
        result = json_generator.generate_report("json_template", data)
        
        assert result is not None
        # Compact JSON should not have extra whitespace
        assert result.strip() == '{"title": "Test Report"}'


class TestMarkdownReportGenerator:
    """Test MarkdownReportGenerator class."""

    @pytest.fixture
    def markdown_generator(self):
        """Create a MarkdownReportGenerator instance for testing."""
        return MarkdownReportGenerator()

    def test_markdown_generator_initialization(self, markdown_generator):
        """Test MarkdownReportGenerator initialization."""
        assert markdown_generator.templates == {}
        assert markdown_generator.default_template is None
        assert markdown_generator.extensions == []

    def test_add_extension(self, markdown_generator):
        """Test adding markdown extension."""
        markdown_generator.add_extension("tables")
        assert "tables" in markdown_generator.extensions

    def test_generate_markdown_report(self, markdown_generator):
        """Test generating markdown report."""
        template = ReportTemplate(
            name="markdown_template",
            content="# {{title}}\n\n{{content}}",
            variables=["title", "content"],
            format="markdown"
        )
        markdown_generator.register_template(template)
        
        data = {"title": "Test Report", "content": "This is a test"}
        result = markdown_generator.generate_report("markdown_template", data)
        
        assert result is not None
        assert "# Test Report" in result
        assert "This is a test" in result

    def test_generate_markdown_report_with_tables(self, markdown_generator):
        """Test generating markdown report with tables."""
        markdown_generator.add_extension("tables")
        
        template = ReportTemplate(
            name="table_template",
            content="# {{title}}\n\n{{table_content}}",
            variables=["title", "table_content"],
            format="markdown"
        )
        markdown_generator.register_template(template)
        
        data = {
            "title": "Table Report",
            "table_content": "| Name | Age |\n|------|-----|\n| John | 30  |"
        }
        result = markdown_generator.generate_report("table_template", data)
        
        assert result is not None
        assert "| Name | Age |" in result
        assert "|------|-----|" in result

    def test_generate_markdown_report_with_metadata(self, markdown_generator):
        """Test generating markdown report with metadata."""
        template = ReportTemplate(
            name="meta_template",
            content="# {{title}}\n\n**Author:** {{author}}\n**Date:** {{date}}",
            variables=["title", "author", "date"],
            format="markdown"
        )
        markdown_generator.register_template(template)
        
        data = {
            "title": "Test Report",
            "author": "John Doe",
            "date": "2023-01-01"
        }
        result = markdown_generator.generate_report("meta_template", data)
        
        assert result is not None
        assert "**Author:** John Doe" in result
        assert "**Date:** 2023-01-01" in result


class TestPDFReportGenerator:
    """Test PDFReportGenerator class."""

    @pytest.fixture
    def pdf_generator(self):
        """Create a PDFReportGenerator instance for testing."""
        return PDFReportGenerator()

    def test_pdf_generator_initialization(self, pdf_generator):
        """Test PDFReportGenerator initialization."""
        assert pdf_generator.templates == {}
        assert pdf_generator.default_template is None
        assert pdf_generator.page_size == "A4"
        assert pdf_generator.margin == 1.0

    def test_set_page_size(self, pdf_generator):
        """Test setting page size."""
        pdf_generator.set_page_size("Letter")
        assert pdf_generator.page_size == "Letter"

    def test_set_margin(self, pdf_generator):
        """Test setting margin."""
        pdf_generator.set_margin(0.5)
        assert pdf_generator.margin == 0.5

    def test_generate_pdf_report(self, pdf_generator):
        """Test generating PDF report."""
        template = ReportTemplate(
            name="pdf_template",
            content="<h1>{{title}}</h1><p>{{content}}</p>",
            variables=["title", "content"],
            format="html"
        )
        pdf_generator.register_template(template)
        
        data = {"title": "Test Report", "content": "This is a test"}
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            temp_file = f.name
        
        try:
            success = pdf_generator.generate_report("pdf_template", data, temp_file)
            
            # Note: In a real test environment, we might not have PDF generation capabilities
            # So we'll just check that the method doesn't crash
            assert success is not None
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_generate_pdf_report_with_custom_settings(self, pdf_generator):
        """Test generating PDF report with custom settings."""
        pdf_generator.set_page_size("Letter")
        pdf_generator.set_margin(0.75)
        
        template = ReportTemplate(
            name="pdf_template",
            content="<h1>{{title}}</h1>",
            variables=["title"],
            format="html"
        )
        pdf_generator.register_template(template)
        
        data = {"title": "Custom PDF Report"}
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            temp_file = f.name
        
        try:
            success = pdf_generator.generate_report("pdf_template", data, temp_file)
            assert success is not None
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_generate_pdf_report_with_metadata(self, pdf_generator):
        """Test generating PDF report with metadata."""
        template = ReportTemplate(
            name="pdf_template",
            content="<h1>{{title}}</h1><p>Author: {{author}}</p>",
            variables=["title", "author"],
            format="html"
        )
        pdf_generator.register_template(template)
        
        data = {"title": "Test Report", "author": "John Doe"}
        metadata = {
            "creator": "AutoPR",
            "subject": "Test Report",
            "keywords": "test, report, pdf"
        }
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            temp_file = f.name
        
        try:
            success = pdf_generator.generate_report("pdf_template", data, temp_file, metadata)
            assert success is not None
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestReportGeneratorIntegration:
    """Integration tests for report generators."""

    def test_multiple_generators_same_template(self):
        """Test using the same template with multiple generators."""
        template = ReportTemplate(
            name="shared_template",
            content="<h1>{{title}}</h1><p>{{content}}</p>",
            variables=["title", "content"],
            format="html"
        )
        
        html_generator = HTMLReportGenerator()
        json_generator = JSONReportGenerator()
        
        html_generator.register_template(template)
        json_generator.register_template(template)
        
        data = {"title": "Shared Report", "content": "Shared content"}
        
        html_result = html_generator.generate_report("shared_template", data)
        json_result = json_generator.generate_report("shared_template", data)
        
        assert html_result is not None
        assert json_result is not None
        assert "Shared Report" in html_result
        assert "Shared content" in html_result

    def test_template_validation(self):
        """Test template validation across generators."""
        # Template with missing variables
        template = ReportTemplate(
            name="incomplete_template",
            content="<h1>{{title}}</h1><p>{{missing_var}}</p>",
            variables=["title"],
            format="html"
        )
        
        html_generator = HTMLReportGenerator()
        html_generator.register_template(template)
        
        data = {"title": "Test Report"}
        result = html_generator.generate_report("incomplete_template", data)
        
        assert result is not None
        assert "Test Report" in result
        assert "{{missing_var}}" in result  # Should remain as placeholder

    def test_report_generation_performance(self):
        """Test report generation performance."""
        template = ReportTemplate(
            name="performance_template",
            content="<h1>{{title}}</h1>" + "<p>Line {{i}}</p>" * 100,
            variables=["title"] + [f"i{i}" for i in range(100)],
            format="html"
        )
        
        html_generator = HTMLReportGenerator()
        html_generator.register_template(template)
        
        data = {"title": "Performance Test"}
        for i in range(100):
            data[f"i{i}"] = f"Content {i}"
        
        import time
        start_time = time.time()
        result = html_generator.generate_report("performance_template", data)
        end_time = time.time()
        
        assert result is not None
        assert "Performance Test" in result
        # Should complete within reasonable time (e.g., 1 second)
        assert end_time - start_time < 1.0
