"""
Template Metadata Management for Hybrid YAML + Template Approach
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class TemplateVariable:
    """Represents a template variable configuration."""

    name: str
    type: str
    default: str | int | bool | None = None
    required: bool = False
    description: str = ""


@dataclass
class TemplateVariant:
    """Represents a template variant with modifications."""

    name: str
    description: str
    modifications: list[dict[str, Any]]


@dataclass
class TemplateMetadata:
    """Comprehensive template metadata from YAML files."""

    def __init__(self, metadata: dict[str, Any], yaml_path: Path):
        self.yaml_path = yaml_path
        self.name = metadata.get("name", "")
        self.description = metadata.get("description", "")
        self.category = metadata.get("category", "")
        self.platforms = metadata.get("platforms", [])
        self.file_extension = metadata.get("file_extension", "")
        self.usage = metadata.get("usage", [])
        self.dependencies = metadata.get("dependencies", {})
        self.notes = metadata.get("notes", [])
        self.examples = metadata.get("examples", {})

        # Parse variables
        self.variables = {}
        for var_name, var_config in metadata.get("variables", {}).items():
            if isinstance(var_config, dict):
                self.variables[var_name] = TemplateVariable(
                    name=var_name,
                    type=var_config.get("type", "string"),
                    default=var_config.get("default"),
                    required=var_config.get("required", False),
                    description=var_config.get("description", ""),
                )

        # Parse variants
        self.variants = {}
        for variant_name, variant_config in metadata.get("variants", {}).items():
            if isinstance(variant_config, dict):
                self.variants[variant_name] = TemplateVariant(
                    name=variant_config.get("name", variant_name),
                    description=variant_config.get("description", ""),
                    modifications=variant_config.get("modifications", []),
                )

    @property
    def template_file_path(self) -> Path:
        """Get the corresponding template file path."""
        # Remove .yml extension to get template file
        return self.yaml_path.with_suffix("")


class TemplateRegistry:
    """Registry for managing template metadata and files."""

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.metadata_cache: dict[str, TemplateMetadata] = {}
        self._load_all_metadata()

    def _load_all_metadata(self) -> None:
        """Load all template metadata from YAML files."""
        if not self.templates_dir.exists():
            return

        for yaml_file in self.templates_dir.rglob("*.yml"):
            try:
                template_key = self._get_template_key(yaml_file)
                with open(yaml_file, encoding="utf-8") as f:
                    metadata_dict = yaml.safe_load(f)
                    if metadata_dict:
                        self.metadata_cache[template_key] = TemplateMetadata(
                            metadata_dict, yaml_file
                        )
            except Exception:
                pass

    def _get_template_key(self, yaml_path: Path) -> str:
        """Generate template key from YAML file path."""
        relative_path = yaml_path.relative_to(self.templates_dir)
        # Remove .yml extension and convert to key
        return str(relative_path.with_suffix(""))

    def get_metadata(self, template_key: str) -> TemplateMetadata | None:
        """Get metadata for a specific template."""
        return self.metadata_cache.get(template_key)

    def list_templates(
        self, platform: str | None = None, category: str | None = None
    ) -> list[str]:
        """List available templates, optionally filtered."""
        templates = []
        for key, metadata in self.metadata_cache.items():
            if platform and platform not in metadata.platforms:
                continue
            if category and metadata.category != category:
                continue
            templates.append(key)
        return templates

    def get_template_content(self, template_key: str) -> str | None:
        """Get the raw content of a template file."""
        metadata = self.get_metadata(template_key)
        if not metadata:
            return None

        template_path = metadata.template_file_path
        if not template_path.exists():
            return None

        try:
            with open(template_path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    def generate_template(
        self,
        template_key: str,
        variables: dict[str, Any] | None = None,
        variants: list[str] | None = None,
    ) -> str | None:
        """Generate template content with variables and variants applied."""
        metadata = self.get_metadata(template_key)
        if not metadata:
            return None

        content = self.get_template_content(template_key)
        if not content:
            return None

        # Apply variables
        if variables:
            content = self._apply_variables(content, metadata, variables)

        # Apply variants
        if variants:
            content = self._apply_variants(content, metadata, variants)

        return content

    def _apply_variables(
        self, content: str, metadata: TemplateMetadata, variables: dict[str, Any]
    ) -> str:
        """Apply variable substitutions to template content."""
        # Merge with defaults and validate
        final_vars = {}

        for var_name, var_config in metadata.variables.items():
            if var_name in variables:
                final_vars[var_name] = variables[var_name]
            elif var_config.default is not None:
                final_vars[var_name] = var_config.default
            elif var_config.required:
                msg = f"Required variable missing: {var_name}"
                raise ValueError(msg)

        # Apply substitutions using {{variable_name}} format
        for var_name, value in final_vars.items():
            placeholder = f"{{{{{var_name}}}}}"
            content = content.replace(placeholder, str(value))

        return content

    def _apply_variants(
        self, content: str, metadata: TemplateMetadata, variants: list[str]
    ) -> str:
        """Apply variant modifications to template content."""
        lines = content.split("\n")

        for variant_name in variants:
            if variant_name not in metadata.variants:
                continue

            variant = metadata.variants[variant_name]

            for mod in variant.modifications:
                action = mod.get("action")
                line_num = mod.get("line", 1)
                mod_content = mod.get("content", "")

                # Handle negative line numbers (from end)
                if line_num < 0:
                    line_num = len(lines) + line_num + 1

                # Convert to 0-based index
                line_idx = line_num - 1

                if action == "add_after" and 0 <= line_idx < len(lines):
                    lines.insert(line_idx + 1, mod_content)
                elif action == "add_before" and 0 <= line_idx < len(lines):
                    lines.insert(line_idx, mod_content)
                elif action == "replace" and 0 <= line_idx < len(lines):
                    lines[line_idx] = mod_content

        return "\n".join(lines)

    def validate_template_structure(self, template_data: dict[str, Any]) -> None:
        """Validate template structure."""
        required_keys = [
            "name",
            "description",
            "category",
            "platforms",
            "file_extension",
        ]
        for key in required_keys:
            if key not in template_data:
                msg = f"Missing required key: {key}"
                raise ValueError(msg)

        if "variables" in template_data:
            for var_name, var_config in template_data["variables"].items():
                if not isinstance(var_config, dict):
                    msg = f"Invalid variable configuration: {var_name}"
                    raise ValueError(msg)
                if "type" not in var_config:
                    msg = f"Missing variable type: {var_name}"
                    raise ValueError(msg)

        if "variants" in template_data:
            for variant_name, variant_config in template_data["variants"].items():
                if not isinstance(variant_config, dict):
                    msg = f"Invalid variant configuration: {variant_name}"
                    raise ValueError(msg)
                if "modifications" not in variant_config:
                    msg = f"Missing variant modifications: {variant_name}"
                    raise ValueError(msg)

    def get_template_info(self, template_key: str) -> dict[str, Any]:
        """Get comprehensive information about a template."""
        metadata = self.get_metadata(template_key)
        if not metadata:
            return {}

        return {
            "name": metadata.name,
            "description": metadata.description,
            "category": metadata.category,
            "platforms": metadata.platforms,
            "file_extension": metadata.file_extension,
            "variables": {
                name: {
                    "type": var.type,
                    "default": var.default,
                    "required": var.required,
                    "description": var.description,
                }
                for name, var in metadata.variables.items()
            },
            "variants": {
                name: {
                    "name": variant.name,
                    "description": variant.description,
                    "modifications_count": len(variant.modifications),
                }
                for name, variant in metadata.variants.items()
            },
            "usage": metadata.usage,
            "dependencies": metadata.dependencies,
            "notes": metadata.notes,
            "examples": metadata.examples,
            "template_file": str(metadata.template_file_path),
            "metadata_file": str(metadata.yaml_path),
            "exists": metadata.template_file_path.exists(),
        }
