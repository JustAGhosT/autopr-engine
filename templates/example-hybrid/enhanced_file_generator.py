"""
Enhanced File Generator with YAML metadata support.
Demonstrates hybrid approach for template management.
"""

import contextlib
import os
from pathlib import Path
from typing import Any

import yaml


class TemplateMetadata:
    """Represents template metadata from YAML files."""

    def __init__(self, metadata: dict[str, Any]):
        self.name = metadata.get("name", "")
        self.description = metadata.get("description", "")
        self.category = metadata.get("category", "")
        self.platforms = metadata.get("platforms", [])
        self.file_extension = metadata.get("file_extension", "")
        self.variables = metadata.get("variables", {})
        self.variants = metadata.get("variants", {})
        self.usage = metadata.get("usage", [])
        self.dependencies = metadata.get("dependencies", {})
        self.notes = metadata.get("notes", [])
        self.examples = metadata.get("examples", {})


class EnhancedFileGenerator:
    """Enhanced file generator with YAML metadata support."""

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.template_cache: dict[str, TemplateMetadata] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all template metadata from YAML files."""
        for yaml_file in self.templates_dir.rglob("*.yml"):
            if yaml_file.name.endswith(".yml"):
                template_key = self._get_template_key(yaml_file)
                with open(yaml_file, encoding="utf-8") as f:
                    metadata = yaml.safe_load(f)
                    self.template_cache[template_key] = TemplateMetadata(metadata)

    def _get_template_key(self, yaml_path: Path) -> str:
        """Generate template key from file path."""
        relative_path = yaml_path.relative_to(self.templates_dir)
        # Remove .yml extension and convert to key
        return str(relative_path.with_suffix(""))

    def get_template_file_path(self, template_key: str) -> Path:
        """Get the actual template file path from template key."""
        yaml_path = self.templates_dir / f"{template_key}.yml"
        # Template file is same name but without .yml extension
        return yaml_path.with_suffix("")

    def list_templates(self, platform: str | None = None, category: str | None = None) -> list[str]:
        """List available templates, optionally filtered by platform/category."""
        templates = []
        for key, metadata in self.template_cache.items():
            if platform and platform not in metadata.platforms:
                continue
            if category and metadata.category != category:
                continue
            templates.append(key)
        return templates

    def get_template_metadata(self, template_key: str) -> TemplateMetadata | None:
        """Get metadata for a specific template."""
        return self.template_cache.get(template_key)

    def generate_file(
        self,
        template_key: str,
        output_path: str,
        variables: dict[str, Any] | None = None,
        variants: list[str] | None = None,
    ) -> str:
        """Generate a file from template with variables and variants."""
        metadata = self.get_template_metadata(template_key)
        if not metadata:
            msg = f"Template not found: {template_key}"
            raise ValueError(msg)

        template_path = self.get_template_file_path(template_key)
        if not template_path.exists():
            msg = f"Template file not found: {template_path}"
            raise FileNotFoundError(msg)

        # Read template content
        with open(template_path, encoding="utf-8") as f:
            content = f.read()

        # Apply variables
        if variables:
            content = self._apply_variables(content, metadata, variables)

        # Apply variants
        if variants:
            content = self._apply_variants(content, metadata, variants)

        # Write output file
        os.makedirs(Path(output_path).parent, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return content

    def _apply_variables(
        self, content: str, metadata: TemplateMetadata, variables: dict[str, Any]
    ) -> str:
        """Apply variable substitutions to template content."""
        # Merge with defaults
        final_vars = {}
        for var_name, var_config in metadata.variables.items():
            if isinstance(var_config, dict):
                default_value = var_config.get("default")
                if var_name in variables:
                    final_vars[var_name] = variables[var_name]
                elif default_value is not None:
                    final_vars[var_name] = default_value
                elif var_config.get("required", False):
                    msg = f"Required variable missing: {var_name}"
                    raise ValueError(msg)

        # Apply substitutions
        for var_name, value in final_vars.items():
            placeholder = f"{{{{{var_name}}}}}"
            content = content.replace(placeholder, str(value))

        return content

    def _apply_variants(self, content: str, metadata: TemplateMetadata, variants: list[str]) -> str:
        """Apply variant modifications to template content."""
        lines = content.split("\n")

        for variant_name in variants:
            if variant_name not in metadata.variants:
                continue

            variant = metadata.variants[variant_name]
            modifications = variant.get("modifications", [])

            for mod in modifications:
                action = mod.get("action")
                line_num = mod.get("line", 1) - 1  # Convert to 0-based
                mod_content = mod.get("content", "")

                if action == "add_after" and 0 <= line_num < len(lines):
                    lines.insert(line_num + 1, mod_content)
                elif action == "add_before" and 0 <= line_num < len(lines):
                    lines.insert(line_num, mod_content)
                elif action == "replace" and 0 <= line_num < len(lines):
                    lines[line_num] = mod_content

        return "\n".join(lines)

    def get_template_info(self, template_key: str) -> dict[str, Any]:
        """Get comprehensive information about a template."""
        metadata = self.get_template_metadata(template_key)
        if not metadata:
            return {}

        template_path = self.get_template_file_path(template_key)

        return {
            "name": metadata.name,
            "description": metadata.description,
            "category": metadata.category,
            "platforms": metadata.platforms,
            "file_extension": metadata.file_extension,
            "variables": metadata.variables,
            "variants": list(metadata.variants.keys()),
            "usage": metadata.usage,
            "dependencies": metadata.dependencies,
            "notes": metadata.notes,
            "examples": metadata.examples,
            "template_file": str(template_path),
            "exists": template_path.exists(),
        }


# Example usage
if __name__ == "__main__":
    generator = EnhancedFileGenerator("templates")

    # List all templates
    for _template in generator.list_templates():
        pass

    # List React templates
    for _template in generator.list_templates(platform="lovable"):
        pass

    # Get template info
    info = generator.get_template_info("example-hybrid/react.dockerfile")

    # Generate a file
    with contextlib.suppress(Exception):
        content = generator.generate_file(
            "example-hybrid/react.dockerfile",
            "output/Dockerfile",
            variables={"node_version": "20", "build_command": "npm run build:prod"},
            variants=["with_nginx_config"],
        )
