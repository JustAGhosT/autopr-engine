#!/usr/bin/env python3
"""
Documentation Generator Module
=============================

Generates comprehensive documentation for templates using various formats.
Provides a unified interface for documentation generation across different
template types and output formats.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

from discovery.content_analyzer import ContentAnalyzer, TemplateAnalysis
from discovery.format_generators import FormatGeneratorFactory
from discovery.format_generators.config import DocumentationConfig
from discovery.template_loader import TemplateLoader


class TemplateDocumentationGenerator:
    """Generates documentation for templates."""

    def __init__(self, template_name: str, **kwargs: Any) -> None:
        """Initialize the documentation generator.

        Args:
            template_name: Name of the template to generate documentation for
            **kwargs: Additional configuration options
        """
        self.template_name = template_name
        self.config = DocumentationConfig(**kwargs)

        # Initialize components
        self.template_loader = TemplateLoader()
        self.content_analyzer = ContentAnalyzer()
        self.format_factory = FormatGeneratorFactory()

        # Set output format
        self.output_format = kwargs.get("format", "markdown")
        self.output_dir = Path(kwargs.get("output_dir", "docs"))
        self.output_dir.mkdir(exist_ok=True)

    def generate(self) -> str:
        """Generate documentation for the template.

        Returns:
            Generated documentation content

        Raises:
            Exception: If template analysis or generation fails
        """
        try:
            # Find the template file
            template_file = self._find_template_file()
            if not template_file:
                raise FileNotFoundError(
                    f"Template file not found for '{self.template_name}'"
                )

            # Analyze the template
            analysis = self.content_analyzer.analyze_template(template_file)

            # Create format generator
            generator = self.format_factory.create_generator(
                self.output_format, self.config, self.template_loader
            )

            # Generate documentation based on template category
            if analysis.category == "platform":
                content = generator.generate_platform_guide(analysis)
            elif analysis.category == "use_case":
                content = generator.generate_use_case_guide(analysis)
            elif analysis.category == "integration":
                content = generator.generate_integration_guide(analysis)
            else:
                # Fallback to generic documentation
                content = self._generate_generic_documentation(analysis)

            # Write to file
            output_file = self.output_dir / f"{self.template_name}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            return content

        except Exception as e:
            # Preserve previous exception behavior
            error_content = (
                f"# {self.template_name.title()} Integration Guide\n\n"
                f"Error generating guide: {e}"
            )

            # Write error content to file
            output_file = self.output_dir / f"{self.template_name}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(error_content)

            raise

    def run(self) -> str:
        """Alias for generate() method for compatibility."""
        return self.generate()

    def _find_template_file(self) -> Optional[Path]:
        """Find the template file for the given template name."""
        # Look in common template directories
        search_dirs = [
            Path("templates"),
            Path("platforms"),
            Path("use_cases"),
            Path("integrations"),
            Path("."),
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Try different file extensions
            for ext in [".yml", ".yaml", ".json"]:
                template_file = search_dir / f"{self.template_name}{ext}"
                if template_file.exists():
                    return template_file

        return None

    def _generate_generic_documentation(self, analysis: TemplateAnalysis) -> str:
        """Generate generic documentation when category is unknown."""
        return f"""# {analysis.name.title()} Documentation

## Overview

This template provides functionality for {analysis.name}.

## Key Features

{chr(10).join(f"- {feature}" for feature in analysis.key_features)}

## Configuration

The following variables can be configured:

{chr(10).join(f"- **{key}**: {value}" for key, value in analysis.variables.items())}

## Dependencies

{chr(10).join(f"- {dep}" for dep in analysis.dependencies)}

## Best Practices

{chr(10).join(f"- {practice}" for practice in analysis.best_practices)}

## Troubleshooting

{chr(10).join(f"### {issue}\n{solution}" for issue, solution in analysis.troubleshooting.items())}

## Examples

{chr(10).join(f"### Example {i+1}\n{example.get('description', 'No description')}" for i, example in enumerate(analysis.examples))}

---
*Generated on {analysis.metadata.get('generation_date', 'Unknown date')}*
"""


def main() -> None:
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(description="Generate template documentation")
    parser.add_argument("template_name", help="Name of the template to document")
    parser.add_argument(
        "--format",
        default="markdown",
        choices=["markdown", "html", "json"],
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--output-dir", default="docs", help="Output directory (default: docs)"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        # Create generator
        generator = TemplateDocumentationGenerator(
            template_name=args.template_name,
            format=args.format,
            output_dir=args.output_dir,
            verbose=args.verbose,
        )

        # Generate documentation
        content = generator.generate()

        if args.verbose:
            print(f"Generated documentation for '{args.template_name}'")
            print(f"Output written to: {args.output_dir}/{args.template_name}.md")

        sys.exit(0)

    except Exception as e:
        print(f"Error generating documentation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
