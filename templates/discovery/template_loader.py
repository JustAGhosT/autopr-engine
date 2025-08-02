#!/usr/bin/env python3
"""
Template Loader Module
=====================

Handles loading and caching of documentation templates from external files.
Provides a clean interface for template management and supports multiple formats.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

try:
    from jinja2 import Environment, FileSystemLoader
    from jinja2 import Template as Jinja2Template

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

    # Fallback for when Jinja2 is not available
    class Jinja2Template:
        def __init__(self, template_str: str) -> None:
            self.template_str = template_str

        def render(self, **kwargs: Any) -> str:
            # Simple string replacement fallback
            result = self.template_str
            for key, value in kwargs.items():
                result = result.replace(f"{{ {key} }}", str(value))
            return result


class TemplateLoader:
    """Loads and manages documentation templates."""

    def __init__(self, templates_root: Path | None = None) -> None:
        """Initialize the template loader."""
        if templates_root is None:
            current_dir = Path(__file__).parent
            templates_root = current_dir.parent

        self.templates_root = templates_root
        self.doc_templates_dir = self.templates_root / "documentation"

        # Initialize Jinja2 environment if available
        if JINJA2_AVAILABLE and self.doc_templates_dir.exists():
            self.jinja_env: Environment | None = Environment(
                loader=FileSystemLoader(str(self.doc_templates_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
                autoescape=True,
            )
        else:
            self.jinja_env: Environment | None = None

    @lru_cache(maxsize=32)
    def load_template(self, template_name: str) -> str:
        """Load a template file content.

        Args:
            template_name: Name of the template file (without extension)

        Returns:
            Template content as string
        """
        # Try different extensions
        for ext in [".md", ".html", ".txt"]:
            template_path = self.doc_templates_dir / f"{template_name}{ext}"
            if template_path.exists():
                try:
                    with open(template_path, encoding="utf-8") as f:
                        return f.read()
                except Exception:
                    continue

        # Return fallback template
        return self._get_fallback_template(template_name)

    def render_template(self, template_name: str, **kwargs: Any) -> str:
        """Render a template with the given variables.

        Args:
            template_name: Name of the template file
            **kwargs: Variables to pass to the template

        Returns:
            Rendered template content
        """
        if self.jinja_env:
            try:
                # Try to load with Jinja2
                for ext in [".md", ".html", ".txt"]:
                    try:
                        template = self.jinja_env.get_template(f"{template_name}{ext}")
                        return template.render(**kwargs)
                    except Exception:
                        continue
            except Exception:
                pass

        # Fallback to simple string replacement
        template_content = self.load_template(template_name)
        template = Jinja2Template(template_content)
        return template.render(**kwargs)

    @lru_cache(maxsize=16)
    def load_template_metadata(self, template_name: str) -> dict[str, Any]:
        """Load metadata from a template file.

        Args:
            template_name: Name of the template file

        Returns:
            Dictionary containing template metadata
        """
        for ext in [".yml", ".yaml"]:
            metadata_path = self.doc_templates_dir / f"{template_name}_metadata{ext}"
            if metadata_path.exists():
                try:
                    with open(metadata_path, encoding="utf-8") as f:
                        metadata = yaml.safe_load(f)
                        return metadata if isinstance(metadata, dict) else {}
                except Exception:
                    pass

        return {}

    def _get_fallback_template(self, template_name: str) -> str:
        """Get a fallback template when the requested template is not found.

        Args:
            template_name: Name of the requested template

        Returns:
            Fallback template content
        """
        fallback_templates = {
            "platform_guide": """# {{ platform_name }} Platform Guide

*Generated on {{ generation_date }}*

## Overview

{{ platform_info.get('description', 'Platform description not available.') }}

### Key Features

{% for feature in key_features %}
- {{ feature }}
{% endfor %}

## Getting Started

1. Choose your template from the available options
2. Configure the required variables
3. Deploy using the platform's deployment process
4. Customize as needed for your specific use case

---

*Template not found. Using fallback template.*""",
            "use_case_guide": """# {{ use_case_name }} Use Case Guide

*Generated on {{ generation_date }}*

## Overview

{{ use_case_info.get('description', 'Use case description not available.') }}

## Implementation Steps

{% for step in implementation_steps %}
{{ loop.index }}. {{ step }}
{% endfor %}

## Getting Started

1. Review the implementation steps above
2. Choose your preferred platform
3. Follow the step-by-step guide
4. Test and iterate on your implementation

---

*Template not found. Using fallback template.*""",
            "integration_guide": """# {{ integration_name }} Integration Guide

*Generated on {{ generation_date }}*

## Overview

{{ integration_info.get('description', 'Integration description not available.') }}

## Setup Instructions

{% for step in setup_steps %}
{{ loop.index }}. {{ step }}
{% endfor %}

## Configuration

Review the configuration options and customize as needed for your specific requirements.

---

*Template not found. Using fallback template.*""",
        }

        return fallback_templates.get(
            template_name,
            f"""# {template_name.replace('_', ' ').title()}

*Generated on {{{{ generation_date }}}}*

## Content

Template content not available.

---

*Template not found: {template_name}*""",
        )

    def get_available_templates(self) -> list[str]:
        """Get list of available template files.

        Returns:
            List of template names (without extensions)
        """
        if not self.doc_templates_dir.exists():
            return []

        templates = set()
        templates.update(
            template_file.stem for template_file in self.doc_templates_dir.glob("*.md")
        )
        templates.update(
            template_file.stem for template_file in self.doc_templates_dir.glob("*.html")
        )
        templates.update(
            template_file.stem for template_file in self.doc_templates_dir.glob("*.txt")
        )

        return sorted(templates)

    def template_exists(self, template_name: str) -> bool:
        """Check if a template file exists.

        Args:
            template_name: Name of the template file

        Returns:
            True if template exists, False otherwise
        """
        for ext in [".md", ".html", ".txt"]:
            template_path = self.doc_templates_dir / f"{template_name}{ext}"
            if template_path.exists():
                return True
        return False


# Convenience functions for backward compatibility
def load_template(template_name: str, templates_root: Path | None = None) -> str:
    """Load a template file content."""
    loader = TemplateLoader(templates_root)
    return loader.load_template(template_name)


def render_template(template_name: str, templates_root: Path | None = None, **kwargs: Any) -> str:
    """Render a template with variables."""
    loader = TemplateLoader(templates_root)
    return loader.render_template(template_name, **kwargs)
