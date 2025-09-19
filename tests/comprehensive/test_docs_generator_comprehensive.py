#!/usr/bin/env python3
"""
Comprehensive tests for docs generator module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the modules we're testing
try:
    from autopr.actions.docs_generator import (DocConfig, DocExporter,
                                               DocFormatter, DocRenderer,
                                               DocsGenerator, DocTemplate,
                                               DocValidator)
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestDocConfig:
    """Test DocConfig class."""

    def test_doc_config_initialization(self):
        """Test DocConfig initialization."""
        config = DocConfig(
            output_format="markdown",
            template_path="/templates",
            output_dir="/docs",
            include_toc=True,
            include_metadata=True,
            auto_generate=True,
            validate_output=True
        )
        
        assert config.output_format == "markdown"
        assert config.template_path == "/templates"
        assert config.output_dir == "/docs"
        assert config.include_toc is True
        assert config.include_metadata is True
        assert config.auto_generate is True
        assert config.validate_output is True

    def test_doc_config_defaults(self):
        """Test DocConfig with default values."""
        config = DocConfig()
        
        assert config.output_format == "html"
        assert config.template_path == "./templates"
        assert config.output_dir == "./docs"
        assert config.include_toc is True
        assert config.include_metadata is False
        assert config.auto_generate is False
        assert config.validate_output is True

    def test_doc_config_to_dict(self):
        """Test DocConfig to_dict method."""
        config = DocConfig(
            output_format="pdf",
            template_path="/custom/templates",
            output_dir="/custom/docs",
            include_toc=False
        )
        
        result = config.to_dict()
        assert result["output_format"] == "pdf"
        assert result["template_path"] == "/custom/templates"
        assert result["output_dir"] == "/custom/docs"
        assert result["include_toc"] is False

    def test_doc_config_from_dict(self):
        """Test DocConfig from_dict method."""
        data = {
            "output_format": "rst",
            "template_path": "/rst/templates",
            "output_dir": "/rst/docs",
            "include_toc": True,
            "include_metadata": True,
            "auto_generate": True,
            "validate_output": False
        }
        
        config = DocConfig.from_dict(data)
        assert config.output_format == "rst"
        assert config.template_path == "/rst/templates"
        assert config.output_dir == "/rst/docs"
        assert config.include_toc is True
        assert config.include_metadata is True
        assert config.auto_generate is True
        assert config.validate_output is False

    def test_doc_config_validation(self):
        """Test DocConfig validation."""
        # Valid config
        valid_config = DocConfig(output_format="markdown", template_path="/templates")
        assert valid_config.is_valid() is True
        
        # Invalid config
        invalid_config = DocConfig(output_format="invalid", template_path="")
        assert invalid_config.is_valid() is False


class TestDocTemplate:
    """Test DocTemplate class."""

    def test_doc_template_initialization(self):
        """Test DocTemplate initialization."""
        template = DocTemplate(
            name="api_docs",
            content="# {{title}}\n\n{{content}}",
            variables=["title", "content"],
            format="markdown"
        )
        
        assert template.name == "api_docs"
        assert template.content == "# {{title}}\n\n{{content}}"
        assert template.variables == ["title", "content"]
        assert template.format == "markdown"

    def test_doc_template_defaults(self):
        """Test DocTemplate with default values."""
        template = DocTemplate(name="default_template")
        
        assert template.name == "default_template"
        assert template.content == ""
        assert template.variables == []
        assert template.format == "html"

    def test_doc_template_render(self):
        """Test DocTemplate render method."""
        template = DocTemplate(
            name="test_template",
            content="Hello {{name}}, your score is {{score}}",
            variables=["name", "score"]
        )
        
        data = {"name": "John", "score": 95}
        result = template.render(data)
        
        assert result == "Hello John, your score is 95"

    def test_doc_template_render_missing_variables(self):
        """Test DocTemplate render with missing variables."""
        template = DocTemplate(
            name="test_template",
            content="Hello {{name}}, your score is {{score}}",
            variables=["name", "score"]
        )
        
        data = {"name": "John"}  # Missing score
        result = template.render(data)
        
        assert "Hello John, your score is {{score}}" in result

    def test_doc_template_to_dict(self):
        """Test DocTemplate to_dict method."""
        template = DocTemplate(
            name="api_template",
            content="# API Documentation\n\n{{api_content}}",
            variables=["api_content"],
            format="markdown"
        )
        
        result = template.to_dict()
        assert result["name"] == "api_template"
        assert result["content"] == "# API Documentation\n\n{{api_content}}"
        assert result["variables"] == ["api_content"]
        assert result["format"] == "markdown"

    def test_doc_template_from_dict(self):
        """Test DocTemplate from_dict method."""
        data = {
            "name": "readme_template",
            "content": "# {{project_name}}\n\n{{description}}",
            "variables": ["project_name", "description"],
            "format": "markdown"
        }
        
        template = DocTemplate.from_dict(data)
        assert template.name == "readme_template"
        assert template.content == "# {{project_name}}\n\n{{description}}"
        assert template.variables == ["project_name", "description"]
        assert template.format == "markdown"

    def test_doc_template_validate(self):
        """Test DocTemplate validation."""
        # Valid template
        valid_template = DocTemplate(
            name="valid_template",
            content="Valid content",
            variables=["var1", "var2"]
        )
        assert valid_template.is_valid() is True
        
        # Invalid template
        invalid_template = DocTemplate(name="", content="")
        assert invalid_template.is_valid() is False


class TestDocFormatter:
    """Test DocFormatter class."""

    @pytest.fixture
    def doc_formatter(self):
        """Create a DocFormatter instance for testing."""
        return DocFormatter()

    def test_doc_formatter_initialization(self, doc_formatter):
        """Test DocFormatter initialization."""
        assert doc_formatter.formatters == {}
        assert doc_formatter.default_format == "html"

    def test_add_formatter(self, doc_formatter):
        """Test adding a custom formatter."""
        def markdown_formatter(content):
            return f"# {content}"
        
        doc_formatter.add_formatter("markdown", markdown_formatter)
        assert "markdown" in doc_formatter.formatters

    def test_format_markdown(self, doc_formatter):
        """Test formatting as markdown."""
        content = "Test content"
        result = doc_formatter.format_markdown(content)
        
        assert isinstance(result, str)
        assert content in result

    def test_format_html(self, doc_formatter):
        """Test formatting as HTML."""
        content = "Test content"
        result = doc_formatter.format_html(content)
        
        assert isinstance(result, str)
        assert "<html>" in result
        assert content in result

    def test_format_rst(self, doc_formatter):
        """Test formatting as RST."""
        content = "Test content"
        result = doc_formatter.format_rst(content)
        
        assert isinstance(result, str)
        assert content in result

    def test_format_pdf(self, doc_formatter):
        """Test formatting as PDF."""
        content = "Test content"
        result = doc_formatter.format_pdf(content)
        
        assert isinstance(result, bytes) or isinstance(result, str)

    def test_format_with_custom_formatter(self, doc_formatter):
        """Test formatting with custom formatter."""
        def custom_formatter(content):
            return f"CUSTOM: {content.upper()}"
        
        doc_formatter.add_formatter("custom", custom_formatter)
        
        content = "test content"
        result = doc_formatter.format(content, "custom")
        
        assert result == "CUSTOM: TEST CONTENT"

    def test_format_with_metadata(self, doc_formatter):
        """Test formatting with metadata."""
        content = "Test content"
        metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "date": "2023-01-01"
        }
        
        result = doc_formatter.format_with_metadata(content, "html", metadata)
        
        assert isinstance(result, str)
        assert "Test Document" in result
        assert "Test Author" in result
        assert "2023-01-01" in result


class TestDocValidator:
    """Test DocValidator class."""

    @pytest.fixture
    def doc_validator(self):
        """Create a DocValidator instance for testing."""
        return DocValidator()

    def test_doc_validator_initialization(self, doc_validator):
        """Test DocValidator initialization."""
        assert doc_validator.validation_rules == []
        assert doc_validator.error_messages == []

    def test_add_validation_rule(self, doc_validator):
        """Test adding a validation rule."""
        def length_rule(content):
            return len(content) > 0
        
        doc_validator.add_validation_rule(length_rule)
        assert len(doc_validator.validation_rules) == 1

    def test_validate_content(self, doc_validator):
        """Test validating document content."""
        # Valid content
        valid_content = "This is valid content with sufficient length."
        result = doc_validator.validate_content(valid_content)
        assert result.is_valid is True
        
        # Invalid content
        invalid_content = ""
        result = doc_validator.validate_content(invalid_content)
        assert result.is_valid is False

    def test_validate_template(self, doc_validator):
        """Test validating document template."""
        # Valid template
        valid_template = DocTemplate(
            name="valid_template",
            content="Valid template content",
            variables=["var1", "var2"]
        )
        result = doc_validator.validate_template(valid_template)
        assert result.is_valid is True
        
        # Invalid template
        invalid_template = DocTemplate(name="", content="")
        result = doc_validator.validate_template(invalid_template)
        assert result.is_valid is False

    def test_validate_format(self, doc_validator):
        """Test validating document format."""
        # Valid formats
        assert doc_validator.validate_format("html") is True
        assert doc_validator.validate_format("markdown") is True
        assert doc_validator.validate_format("rst") is True
        assert doc_validator.validate_format("pdf") is True
        
        # Invalid format
        assert doc_validator.validate_format("invalid") is False

    def test_validate_metadata(self, doc_validator):
        """Test validating document metadata."""
        # Valid metadata
        valid_metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "version": "1.0"
        }
        result = doc_validator.validate_metadata(valid_metadata)
        assert result.is_valid is True
        
        # Invalid metadata
        invalid_metadata = {"title": "", "author": None}
        result = doc_validator.validate_metadata(invalid_metadata)
        assert result.is_valid is False


class TestDocRenderer:
    """Test DocRenderer class."""

    @pytest.fixture
    def doc_renderer(self):
        """Create a DocRenderer instance for testing."""
        return DocRenderer()

    def test_doc_renderer_initialization(self, doc_renderer):
        """Test DocRenderer initialization."""
        assert doc_renderer.renderers == {}
        assert doc_renderer.default_renderer is None

    def test_add_renderer(self, doc_renderer):
        """Test adding a custom renderer."""
        def custom_renderer(template, data):
            return f"Rendered: {template.content}"
        
        doc_renderer.add_renderer("custom", custom_renderer)
        assert "custom" in doc_renderer.renderers

    def test_render_template(self, doc_renderer):
        """Test rendering a template."""
        template = DocTemplate(
            name="test_template",
            content="Hello {{name}}, welcome to {{project}}",
            variables=["name", "project"]
        )
        
        data = {"name": "John", "project": "AutoPR"}
        result = doc_renderer.render_template(template, data)
        
        assert result == "Hello John, welcome to AutoPR"

    def test_render_with_default_renderer(self, doc_renderer):
        """Test rendering with default renderer."""
        def default_renderer(template, data):
            return template.content.replace("{{name}}", data.get("name", "Unknown"))
        
        doc_renderer.set_default_renderer(default_renderer)
        
        template = DocTemplate(
            name="test_template",
            content="Hello {{name}}",
            variables=["name"]
        )
        
        data = {"name": "John"}
        result = doc_renderer.render_template(template, data)
        
        assert result == "Hello John"

    def test_render_with_custom_renderer(self, doc_renderer):
        """Test rendering with custom renderer."""
        def custom_renderer(template, data):
            return f"CUSTOM: {template.content}"
        
        doc_renderer.add_renderer("custom", custom_renderer)
        
        template = DocTemplate(
            name="test_template",
            content="Hello {{name}}",
            variables=["name"]
        )
        
        data = {"name": "John"}
        result = doc_renderer.render_template(template, data, "custom")
        
        assert result == "CUSTOM: Hello {{name}}"

    def test_render_multiple_templates(self, doc_renderer):
        """Test rendering multiple templates."""
        templates = [
            DocTemplate(name="t1", content="Template 1: {{var}}", variables=["var"]),
            DocTemplate(name="t2", content="Template 2: {{var}}", variables=["var"])
        ]
        
        data = {"var": "test"}
        results = doc_renderer.render_multiple_templates(templates, data)
        
        assert len(results) == 2
        assert results[0] == "Template 1: test"
        assert results[1] == "Template 2: test"


class TestDocExporter:
    """Test DocExporter class."""

    @pytest.fixture
    def doc_exporter(self):
        """Create a DocExporter instance for testing."""
        return DocExporter()

    def test_doc_exporter_initialization(self, doc_exporter):
        """Test DocExporter initialization."""
        assert doc_exporter.exporters == {}
        assert doc_exporter.default_exporter is None

    def test_add_exporter(self, doc_exporter):
        """Test adding a custom exporter."""
        def custom_exporter(content, file_path):
            with open(file_path, 'w') as f:
                f.write(f"CUSTOM: {content}")
            return True
        
        doc_exporter.add_exporter("custom", custom_exporter)
        assert "custom" in doc_exporter.exporters

    def test_export_to_file(self, doc_exporter):
        """Test exporting to file."""
        content = "Test document content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_file = f.name
        
        try:
            result = doc_exporter.export_to_file(content, temp_file)
            assert result is True
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                exported_content = f.read()
            assert exported_content == content
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_export_markdown(self, doc_exporter):
        """Test exporting as markdown."""
        content = "# Test Document\n\nThis is test content."
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            temp_file = f.name
        
        try:
            result = doc_exporter.export_markdown(content, temp_file)
            assert result is True
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                exported_content = f.read()
            assert exported_content == content
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_export_html(self, doc_exporter):
        """Test exporting as HTML."""
        content = "<html><body><h1>Test Document</h1></body></html>"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            temp_file = f.name
        
        try:
            result = doc_exporter.export_html(content, temp_file)
            assert result is True
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                exported_content = f.read()
            assert exported_content == content
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_export_pdf(self, doc_exporter):
        """Test exporting as PDF."""
        content = "Test document content for PDF"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pdf') as f:
            temp_file = f.name
        
        try:
            result = doc_exporter.export_pdf(content, temp_file)
            assert result is True
            assert os.path.exists(temp_file)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_export_with_custom_exporter(self, doc_exporter):
        """Test exporting with custom exporter."""
        def custom_exporter(content, file_path):
            with open(file_path, 'w') as f:
                f.write(f"CUSTOM_EXPORT: {content}")
            return True
        
        doc_exporter.add_exporter("custom", custom_exporter)
        
        content = "Test content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_file = f.name
        
        try:
            result = doc_exporter.export_with_exporter(content, temp_file, "custom")
            assert result is True
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                exported_content = f.read()
            assert exported_content == "CUSTOM_EXPORT: Test content"
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_export_multiple_formats(self, doc_exporter):
        """Test exporting in multiple formats."""
        content = "Test document content"
        base_path = "/tmp/test_doc"
        
        results = doc_exporter.export_multiple_formats(content, base_path, ["html", "markdown"])
        
        assert len(results) == 2
        assert all(result is True for result in results.values())


class TestDocsGenerator:
    """Test DocsGenerator class."""

    @pytest.fixture
    def docs_generator(self):
        """Create a DocsGenerator instance for testing."""
        config = DocConfig(output_format="markdown", output_dir="./docs")
        return DocsGenerator(config)

    def test_docs_generator_initialization(self, docs_generator):
        """Test DocsGenerator initialization."""
        assert docs_generator.config is not None
        assert docs_generator.formatter is not None
        assert docs_generator.validator is not None
        assert docs_generator.renderer is not None
        assert docs_generator.exporter is not None

    def test_generate_documentation(self, docs_generator):
        """Test generating documentation."""
        template = DocTemplate(
            name="api_docs",
            content="# {{title}}\n\n{{description}}",
            variables=["title", "description"]
        )
        
        data = {
            "title": "API Documentation",
            "description": "This is the API documentation for AutoPR."
        }
        
        result = docs_generator.generate_documentation(template, data)
        
        assert result is not None
        assert "API Documentation" in result
        assert "AutoPR" in result

    def test_generate_from_template_file(self, docs_generator):
        """Test generating documentation from template file."""
        # Create a temporary template file
        template_content = {
            "name": "test_template",
            "content": "# {{title}}\n\n{{content}}",
            "variables": ["title", "content"],
            "format": "markdown"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(template_content, f)
            template_file = f.name
        
        try:
            data = {
                "title": "Test Document",
                "content": "This is test content."
            }
            
            result = docs_generator.generate_from_template_file(template_file, data)
            
            assert result is not None
            assert "Test Document" in result
            assert "test content" in result
            
        finally:
            if os.path.exists(template_file):
                os.unlink(template_file)

    def test_generate_and_save(self, docs_generator):
        """Test generating and saving documentation."""
        template = DocTemplate(
            name="readme",
            content="# {{project_name}}\n\n{{description}}",
            variables=["project_name", "description"]
        )
        
        data = {
            "project_name": "AutoPR Engine",
            "description": "Automated PR generation engine."
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            output_file = f.name
        
        try:
            result = docs_generator.generate_and_save(template, data, output_file)
            
            assert result is True
            assert os.path.exists(output_file)
            
            with open(output_file, 'r') as f:
                content = f.read()
            assert "AutoPR Engine" in content
            assert "Automated PR generation engine" in content
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_generate_multiple_docs(self, docs_generator):
        """Test generating multiple documents."""
        templates = [
            DocTemplate(name="readme", content="# {{title}}", variables=["title"]),
            DocTemplate(name="api", content="API: {{title}}", variables=["title"])
        ]
        
        data = {"title": "Test Project"}
        
        results = docs_generator.generate_multiple_docs(templates, data)
        
        assert len(results) == 2
        assert results[0] == "# Test Project"
        assert results[1] == "API: Test Project"

    def test_generate_with_metadata(self, docs_generator):
        """Test generating documentation with metadata."""
        template = DocTemplate(
            name="doc_with_metadata",
            content="# {{title}}\n\n{{content}}",
            variables=["title", "content"]
        )
        
        data = {
            "title": "Test Document",
            "content": "Test content"
        }
        
        metadata = {
            "author": "Test Author",
            "version": "1.0",
            "date": "2023-01-01"
        }
        
        result = docs_generator.generate_with_metadata(template, data, metadata)
        
        assert result is not None
        assert "Test Document" in result
        assert "Test content" in result

    def test_validate_generated_docs(self, docs_generator):
        """Test validating generated documentation."""
        content = "Valid documentation content with sufficient length."
        
        result = docs_generator.validate_generated_docs(content)
        assert result.is_valid is True

    def test_get_generation_summary(self, docs_generator):
        """Test getting generation summary."""
        summary = docs_generator.get_generation_summary()
        
        assert "total_docs_generated" in summary
        assert "successful_generations" in summary
        assert "failed_generations" in summary
        assert "output_format" in summary

    def test_clear_generation_history(self, docs_generator):
        """Test clearing generation history."""
        # Generate some docs first
        template = DocTemplate(name="test", content="Test", variables=[])
        data = {}
        docs_generator.generate_documentation(template, data)
        
        # Clear history
        docs_generator.clear_generation_history()
        
        summary = docs_generator.get_generation_summary()
        assert summary["total_docs_generated"] == 0
