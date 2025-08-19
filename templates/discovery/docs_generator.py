#!/usr/bin/env python3
"""
Template Documentation Generator
===============================

Automatically generates comprehensive documentation for no-code platform templates
including user guides, API documentation, and integration tutorials.

This is the main orchestrator that coordinates the modular documentation generation system.

Features:
- Markdown documentation generation
- HTML documentation with styling
- Platform-specific guides
- Integration tutorials
- Code examples and snippets
- Interactive decision trees
- Modular architecture with template extraction
"""

from datetime import datetime
from pathlib import Path

from .content_analyzer import ContentAnalyzer, TemplateAnalysis
from .format_generators import DocumentationConfig, FormatGeneratorFactory

# Import modular components
from .template_loader import TemplateLoader


class TemplateDocumentationGenerator:
    """Generates comprehensive documentation for templates using modular architecture."""

    def __init__(
        self,
        templates_root: str | None = None,
        config: DocumentationConfig | None = None,
    ) -> None:
        """Initialize the documentation generator."""
        if templates_root is None:
            current_dir = Path(__file__).parent
            templates_root_path = current_dir.parent
        else:
            templates_root_path = Path(templates_root)

        self.templates_root = templates_root_path
        self.config = config or DocumentationConfig()
        self.output_dir = self.templates_root / "docs"
        self.output_dir.mkdir(exist_ok=True)

        # Initialize modular components
        self.template_loader = TemplateLoader(self.templates_root)
        self.content_analyzer = ContentAnalyzer(self.templates_root)
        self.format_generator = FormatGeneratorFactory.create_generator(
            self.config.output_format, self.config, self.template_loader
        )

    def _discover_templates(self) -> list[TemplateAnalysis]:
        """Discover and analyze all templates in the templates directory."""
        template_files: list[Path] = []

        # Find all template files
        for pattern in ["platforms/**/*.yml", "use-cases/*.yml", "integrations/*.yml"]:
            template_files.extend(self.templates_root.glob(pattern))

        # Exclude platform-categories.yml
        template_files = [
            f for f in template_files if f.name != "platform-categories.yml"
        ]

        # Analyze all templates
        analyses = self.content_analyzer.analyze_multiple_templates(template_files)
        return analyses or []

    def generate_all_documentation(self) -> dict[str, str]:
        """Generate complete documentation suite using modular architecture."""
        generated_files: dict[str, str] = {}

        # Discover and analyze all templates
        template_analyses = self._discover_templates()

        # Generate main index
        if self.config.generate_index:
            index_file = self.generate_main_index(template_analyses)
            generated_files["index"] = index_file

        # Group analyses by category
        platform_analyses = [a for a in template_analyses if a.category == "platform"]
        use_case_analyses = [a for a in template_analyses if a.category == "use_case"]
        integration_analyses = [
            a for a in template_analyses if a.category == "integration"
        ]

        # Generate platform guides
        if platform_analyses:
            guide_files = self.generate_platform_guides(platform_analyses)
            generated_files.update(guide_files)

        # Generate use case guides
        if use_case_analyses:
            guide_files = self.generate_use_case_guides(use_case_analyses)
            generated_files.update(guide_files)

        # Generate integration guides
        if integration_analyses:
            guide_files = self.generate_integration_guides(integration_analyses)
            generated_files.update(guide_files)

        # Generate comparison guide for platforms
        if platform_analyses:
            comparison_file = self.generate_comparison_guide(platform_analyses)
            generated_files["platform_comparison"] = comparison_file

        return generated_files

    def generate_main_index(self, template_analyses: list[TemplateAnalysis]) -> str:
        """Generate the main documentation index using modular approach."""
        try:
            # Use format generator to generate main index
            content = self.format_generator.generate_main_index(template_analyses)

            return self._save_file("index.md", content)

        except Exception as e:
            # Fallback content if template loading fails
            fallback_content = self._generate_header(
                "No-Code Platform Templates Documentation"
            )
            fallback_content += f"\n\nError loading template: {e}\n\nPlease check the template files and try again."
            return self._save_file("index.md", fallback_content)

    def generate_platform_guides(
        self, analyses: list[TemplateAnalysis]
    ) -> dict[str, str]:
        """Generate documentation for all platform templates using modular approach."""
        generated_files: dict[str, str] = {}

        try:
            for analysis in analyses:
                try:
                    # Use format generator to create platform guide
                    content = self.format_generator.generate_platform_guide(analysis)

                    # Save the generated documentation
                    template_name = analysis.name
                    doc_file = self._save_file(f"platforms/{template_name}.md", content)
                    generated_files[f"platform_{template_name}"] = doc_file

                except Exception as e:
                    # Generate error content for failed templates
                    template_name = analysis.name
                    error_content = f"# {template_name.title()} Platform Guide\n\nError generating guide: {e}"
                    doc_file = self._save_file(
                        f"platforms/{template_name}.md", error_content
                    )
                    generated_files[f"platform_{template_name}"] = doc_file

            return generated_files

        except Exception:
            # Return empty dict if discovery fails
            return generated_files

    def generate_use_case_guides(
        self, analyses: list[TemplateAnalysis]
    ) -> dict[str, str]:
        """Generate documentation for use case templates using modular approach."""
        generated_files: dict[str, str] = {}

        try:
            for analysis in analyses:
                try:
                    # Use format generator to create use case guide
                    content = self.format_generator.generate_use_case_guide(analysis)

                    # Save the generated documentation
                    template_name = analysis.name
                    doc_file = self._save_file(f"use-cases/{template_name}.md", content)
                    generated_files[f"use_case_{template_name}"] = doc_file

                except Exception as e:
                    # Generate error content for failed templates
                    template_name = analysis.name
                    error_content = f"# {template_name.title()} Use Case Guide\n\nError generating guide: {e}"
                    doc_file = self._save_file(
                        f"use-cases/{template_name}.md", error_content
                    )
                    generated_files[f"use_case_{template_name}"] = doc_file

            return generated_files

        except Exception:
            # Return empty dict if discovery fails
            return generated_files

    def generate_integration_guides(
        self, analyses: list[TemplateAnalysis]
    ) -> dict[str, str]:
        """Generate documentation for integration templates using modular approach."""
        generated_files: dict[str, str] = {}

        try:
            for analysis in analyses:
                try:
                    # Use format generator to create integration guide
                    content = self.format_generator.generate_integration_guide(analysis)

                    # Save the generated documentation
                    template_name = analysis.name
                    doc_file = self._save_file(
                        f"integrations/{template_name}.md", content
                    )
                    generated_files[f"integration_{template_name}"] = doc_file

                except Exception as e:
                    # Generate error content for failed templates
                    template_name = analysis.name
                    error_content = f"# {template_name.title()} Integration Guide\n\nError generating guide: {e}"
                    doc_file = self._save_file(
                        f"integrations/{template_name}.md", error_content
                    )
                    generated_files[f"integration_{template_name}"] = doc_file

            return generated_files

        except Exception:
            # Return empty dict if discovery fails
            return generated_files

    def generate_comparison_guide(
        self, platform_analyses: list[TemplateAnalysis]
    ) -> str:
        """Generate platform comparison documentation using modular approach."""
        try:
            # Use format generator to create comparison guide
            content = self.format_generator.generate_comparison_guide(platform_analyses)

            return self._save_file("platform_comparison.md", content)

        except Exception as e:
            # Fallback content if generation fails
            fallback_content = f"# Platform Comparison Guide\n\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nError generating comparison: {e}"
            return self._save_file("platform_comparison.md", fallback_content)

    def generate_getting_started_guide(self) -> str:
        """Generate a comprehensive getting started guide using modular approach."""
        try:
            # Use template loader to get getting started template
            self.template_loader.load_template("getting_started")

            # Prepare template variables
            template_vars = {
                "title": "Getting Started with No-Code Platform Templates",
                "generation_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Use format generator to render content
            content = self.format_generator.generate_content(
                "getting_started", **template_vars
            )

            return self._save_file("getting_started.md", content)

        except Exception as e:
            # Fallback content if template loading fails
            fallback_content = self._generate_header(
                "Getting Started with No-Code Platform Templates"
            )
            fallback_content += f"\n\nError loading template: {e}\n\nPlease check the template files and try again."
            return self._save_file("getting_started.md", fallback_content)

    def _generate_header(self, title: str) -> str:
        """Generate a standard header for documentation files."""
        return f"""# {title}

*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

"""

    def _save_file(self, filename: str, content: str) -> str:
        """Save content to a file and return the file path."""
        file_path = self.output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(file_path)


def main() -> None:
    """Generate all documentation."""
    generator = TemplateDocumentationGenerator()

    generated_files = generator.generate_all_documentation()

    for _doc_type, _file_path in generated_files.items():
        pass


if __name__ == "__main__":
    main()
