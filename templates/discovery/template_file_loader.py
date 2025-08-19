#!/usr/bin/env python3
"""
Template File Loader Module
===========================

Handles loading and parsing of template files from the filesystem.
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from discovery.template_models import TemplateInfo


class TemplateFileLoader:
    """Loads template files from filesystem and parses metadata."""

    def __init__(self, templates_root: Path) -> None:
        """Initialize the template file loader."""
        self.templates_root = templates_root
        self.platform_categories: dict[str, Any] = {}
        self._load_platform_categories()

    def _load_platform_categories(self) -> None:
        """Load platform categories configuration."""
        categories_file = self.templates_root / "platforms" / "platform-categories.yml"
        if categories_file.exists():
            try:
                with open(categories_file, encoding="utf-8") as f:
                    self.platform_categories = yaml.safe_load(f) or {}
            except Exception as e:
                logging.warning(f"Failed to load platform categories: {e}")
                self.platform_categories = {}

    def load_all_templates(self) -> list[TemplateInfo]:
        """Load all templates from the templates directory structure."""
        templates: list[TemplateInfo] = []

        # Load platform templates
        platforms_dir = self.templates_root / "platforms"
        if platforms_dir.exists():
            for platform_dir in platforms_dir.iterdir():
                if platform_dir.is_dir():
                    templates.extend(self._load_platform_templates(platform_dir))

        # Load use case templates
        use_cases_dir = self.templates_root / "use-cases"
        if use_cases_dir.exists():
            for template_file in use_cases_dir.glob("*.yml"):
                template = self._load_template_file(template_file, "use_case")
                if template:
                    templates.append(template)

        # Load integration templates
        integrations_dir = self.templates_root / "integrations"
        if integrations_dir.exists():
            for template_file in integrations_dir.glob("*.yml"):
                template = self._load_template_file(template_file, "integration")
                if template:
                    templates.append(template)

        return templates

    def _load_platform_templates(self, platform_dir: Path) -> list[TemplateInfo]:
        """Load templates from a platform directory."""
        templates: list[TemplateInfo] = []
        for template_file in platform_dir.glob("*.yml"):
            if template_file.name != "platform-categories.yml":
                template = self._load_template_file(template_file, "platform")
                if template:
                    templates.append(template)
        return templates

    def _load_template_file(
        self, template_file: Path, default_category: str
    ) -> TemplateInfo | None:
        """Load a single template file and extract metadata."""
        try:
            with open(template_file, encoding="utf-8") as f:
                template_data: dict[str, Any] = yaml.safe_load(f) or {}

            if not template_data:
                return None

            # Extract basic information
            name = template_data.get("name", template_file.stem)
            description = template_data.get("description", "")
            category = template_data.get("category", default_category)

            # Extract platforms
            platforms: list[str] = []
            if "platform" in template_data:
                if isinstance(template_data["platform"], str):
                    platforms = [template_data["platform"]]
                elif isinstance(template_data["platform"], list):
                    platforms = template_data["platform"]

            if "platforms" in template_data:
                if isinstance(template_data["platforms"], list):
                    platforms.extend(template_data["platforms"])
                elif isinstance(template_data["platforms"], str):
                    platforms.append(template_data["platforms"])

            # Remove duplicates and ensure we have at least one platform
            platforms = list(set(platforms))
            if not platforms:
                platforms = ["unknown"]

            # Extract other metadata
            complexity = template_data.get("complexity", "medium")
            estimated_time = template_data.get("estimated_time", "unknown")

            # Extract use cases
            use_cases: list[str] = []
            if "use_cases" in template_data:
                if isinstance(template_data["use_cases"], list):
                    use_cases = template_data["use_cases"]
                elif isinstance(template_data["use_cases"], str):
                    use_cases = [template_data["use_cases"]]

            # Extract key features
            key_features: list[str] = []
            if "key_features" in template_data:
                if isinstance(template_data["key_features"], list):
                    key_features = template_data["key_features"]
            elif "features" in template_data:
                if isinstance(template_data["features"], list):
                    key_features = template_data["features"]

            # Extract variables
            variables: dict[str, Any] = template_data.get("variables", {})
            if not isinstance(variables, dict):
                variables = {}

            # Extract variants
            variants: dict[str, Any] = template_data.get("variants", {})
            if not isinstance(variants, dict):
                variants = {}

            # Extract dependencies
            dependencies: list[str] = []
            if "dependencies" in template_data:
                if isinstance(template_data["dependencies"], list):
                    dependencies = template_data["dependencies"]
                elif isinstance(template_data["dependencies"], str):
                    dependencies = [template_data["dependencies"]]

            return TemplateInfo(
                name=name,
                description=description,
                category=category,
                platforms=platforms,
                file_path=str(template_file),
                complexity=complexity,
                estimated_time=estimated_time,
                use_cases=use_cases,
                key_features=key_features,
                variables=variables,
                variants=variants,
                dependencies=dependencies,
            )

        except Exception as e:
            logging.exception(f"Error loading template {template_file}: {e}")
            return None

    def get_platform_categories(self) -> dict[str, Any]:
        """Get the loaded platform categories."""
        return self.platform_categories.copy()
