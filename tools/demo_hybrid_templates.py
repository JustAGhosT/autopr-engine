#!/usr/bin/env python3
"""
Demonstration of Hybrid YAML + Template Approach
Shows how the enhanced FileGenerator works with metadata-driven templates.
"""

from pathlib import Path
import sys

# Add the autopr package to the path
sys.path.insert(0, str(Path(__file__).parent))

from autopr.actions.prototype_enhancement.file_generators import FileGenerator


def demo_hybrid_templates() -> None:
    """Demonstrate the hybrid YAML + template approach."""

    # Initialize the enhanced FileGenerator
    generator = FileGenerator()

    # List all available templates
    all_templates = generator.list_available_templates()
    for _template in sorted(all_templates):
        pass

    # Show platform-specific templates

    platforms = ["replit", "lovable", "bolt"]
    for platform in platforms:
        templates = generator.list_available_templates(platform=platform)
        for _template in templates[:3]:  # Show first 3
            pass
        if len(templates) > 3:
            pass

    # Show category-specific templates

    categories = ["docker", "typescript", "testing"]
    for category in categories:
        templates = generator.list_available_templates(category=category)

    # Demonstrate template info

    template_key = "docker/react.dockerfile"
    info = generator.get_template_info(template_key)
    if info:
        pass

    # Demonstrate basic generation

    # Generate a basic React Dockerfile
    dockerfile_content = generator.generate_from_template(
        "docker/react.dockerfile",
        variables={"node_version": "20", "build_command": "npm run build"},
    )

    if dockerfile_content:
        lines = dockerfile_content.split("\n")
        for _i, _line in enumerate(lines[:10], 1):
            pass
        if len(lines) > 10:
            pass

    # Demonstrate variant generation

    dockerfile_with_variants = generator.generate_from_template(
        "docker/react.dockerfile",
        variables={"node_version": "20"},
        variants=["with_nginx_config", "with_env_vars"],
    )

    if dockerfile_with_variants:
        lines = dockerfile_with_variants.split("\n")
        for _i, _line in enumerate(lines[:15], 1):
            pass

    # Demonstrate platform-specific generation

    platforms_to_test = ["replit", "lovable", "bolt"]
    for platform in platforms_to_test:
        # Generate Dockerfile
        generator.generate_dockerfile(platform, variables={"node_version": "18"})

        # Generate TypeScript config
        generator.generate_typescript_config(platform, variables={"target": "ES2020"})

        # Generate testing files
        testing_files = generator.generate_testing_files(
            platform, variables={"coverage_threshold": 85}
        )
        for _filename in testing_files:
            pass

    # Demonstrate fallback behavior

    # Disable hybrid templates to show fallback
    generator.use_hybrid_templates = False
    generator.generate_dockerfile("replit")

    # Re-enable hybrid templates
    generator.use_hybrid_templates = True
    generator.generate_dockerfile("replit")


def demo_template_creation() -> None:
    """Demonstrate how to create new templates."""

    # Example of creating a new template metadata file


if __name__ == "__main__":
    try:
        demo_hybrid_templates()
        demo_template_creation()
    except Exception:
        import traceback

        traceback.print_exc()
