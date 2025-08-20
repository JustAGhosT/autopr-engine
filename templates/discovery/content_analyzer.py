#!/usr/bin/env python3
"""
Content Analyzer Module
======================

Analyzes template content and extracts metadata for documentation generation.
Provides structured data extraction from YAML templates and content analysis.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class TemplateAnalysis:
    """Results of template content analysis."""

    name: str
    category: str
    metadata: dict[str, Any]
    variables: dict[str, Any]
    key_features: list[str]
    complexity: str
    estimated_time: str
    dependencies: list[str]
    platform_info: dict[str, Any]
    use_case_info: dict[str, Any]
    integration_info: dict[str, Any]
    best_practices: list[str]
    troubleshooting: dict[str, str]
    examples: list[dict[str, Any]]


class ContentAnalyzer:
    """Analyzes template content and extracts structured information."""

    def __init__(self, templates_root: Path | None = None) -> None:
        """Initialize the content analyzer."""
        if templates_root is None:
            current_dir = Path(__file__).parent
            templates_root = current_dir.parent

        self.templates_root = templates_root
        self.platform_categories = self._load_platform_categories()

    def analyze_template(self, template_file: Path) -> TemplateAnalysis:
        """Analyze a template file and extract structured information.

        Args:
            template_file: Path to the template file

        Returns:
            TemplateAnalysis object with extracted information
        """
        try:
            with open(template_file, encoding="utf-8") as f:
                template_data = yaml.safe_load(f)
        except Exception:
            template_data = {}

        if not isinstance(template_data, dict):
            template_data = {}

        # Extract basic information
        name = template_file.stem
        category = self._determine_category(template_file)

        # Extract metadata
        metadata = template_data.get("metadata", {})

        # Extract variables and configuration
        variables = template_data.get("variables", {})

        # Extract key features
        key_features = self._extract_key_features(template_data)

        # Extract complexity and time estimates
        complexity = template_data.get("complexity", "medium")
        estimated_time = template_data.get("estimated_time", "unknown")

        # Extract dependencies
        dependencies = template_data.get("dependencies", [])
        if isinstance(dependencies, str):
            dependencies = [dependencies]

        # Extract platform-specific information
        platform_info = self._extract_platform_info(template_data, category)

        # Extract use case information
        use_case_info = self._extract_use_case_info(template_data, category)

        # Extract integration information
        integration_info = self._extract_integration_info(template_data, category)

        # Extract best practices
        best_practices = self._extract_best_practices(template_data)

        # Extract troubleshooting information
        troubleshooting = self._extract_troubleshooting(template_data)

        # Extract examples
        examples = self._extract_examples(template_data)

        return TemplateAnalysis(
            name=name,
            category=category,
            metadata=metadata,
            variables=variables,
            key_features=key_features,
            complexity=complexity,
            estimated_time=estimated_time,
            dependencies=dependencies,
            platform_info=platform_info,
            use_case_info=use_case_info,
            integration_info=integration_info,
            best_practices=best_practices,
            troubleshooting=troubleshooting,
            examples=examples,
        )

    def analyze_multiple_templates(self, template_files: list[Path]) -> list[TemplateAnalysis]:
        """Analyze multiple template files.

        Args:
            template_files: List of template file paths

        Returns:
            List of TemplateAnalysis objects
        """
        analyses = []
        for template_file in template_files:
            try:
                analysis = self.analyze_template(template_file)
                analyses.append(analysis)
            except Exception:
                continue

        return analyses

    def get_template_summary(self, analysis: TemplateAnalysis) -> dict[str, Any]:
        """Get a summary of template analysis.

        Args:
            analysis: TemplateAnalysis object

        Returns:
            Dictionary with template summary
        """
        return {
            "name": analysis.name,
            "category": analysis.category,
            "complexity": analysis.complexity,
            "estimated_time": analysis.estimated_time,
            "key_features_count": len(analysis.key_features),
            "variables_count": len(analysis.variables),
            "dependencies_count": len(analysis.dependencies),
            "has_examples": len(analysis.examples) > 0,
            "has_troubleshooting": len(analysis.troubleshooting) > 0,
        }

    def _determine_category(self, template_file: Path) -> str:
        """Determine the category of a template based on its path.

        Args:
            template_file: Path to the template file

        Returns:
            Category string
        """
        path_parts = template_file.parts

        if "platforms" in path_parts:
            return "platform"
        if "use-cases" in path_parts:
            return "use_case"
        if "integrations" in path_parts:
            return "integration"
        return "general"

    def _extract_key_features(self, template_data: dict[str, Any]) -> list[str]:
        """Extract key features from template data.

        Args:
            template_data: Template data dictionary

        Returns:
            List of key features
        """
        features = []

        # Check various possible locations for features
        if "key_features" in template_data:
            features.extend(template_data["key_features"])

        if "features" in template_data:
            features.extend(template_data["features"])

        if "metadata" in template_data and "features" in template_data["metadata"]:
            features.extend(template_data["metadata"]["features"])

        # Extract features from platform info
        if "platform_info" in template_data and "key_features" in template_data["platform_info"]:
            features.extend(template_data["platform_info"]["key_features"])

        return list(set(features))  # Remove duplicates

    def _extract_platform_info(
        self, template_data: dict[str, Any], category: str
    ) -> dict[str, Any]:
        """Extract platform-specific information.

        Args:
            template_data: Template data dictionary
            category: Template category

        Returns:
            Platform information dictionary
        """
        platform_info: dict[str, Any] = template_data.get("platform_info", {})

        # Add category-specific information
        if category == "platform":
            # Extract platform-specific details
            if "metadata" in template_data:
                metadata = template_data["metadata"]
                platform_info.update(
                    {
                        "description": metadata.get("description", ""),
                        "documentation_url": metadata.get("documentation_url", ""),
                        "community_url": metadata.get("community_url", ""),
                        "pricing": metadata.get("pricing", {}),
                    }
                )

        return platform_info

    def _extract_use_case_info(
        self, template_data: dict[str, Any], category: str
    ) -> dict[str, Any]:
        """Extract use case information.

        Args:
            template_data: Template data dictionary
            category: Template category

        Returns:
            Use case information dictionary
        """
        use_case_info: dict[str, Any] = template_data.get("use_case_info", {})

        if category == "use_case":
            # Extract use case-specific details
            if "metadata" in template_data:
                metadata = template_data["metadata"]
                use_case_info.update(
                    {
                        "description": metadata.get("description", ""),
                        "target_audience": metadata.get("target_audience", ""),
                        "complexity_description": metadata.get("complexity_description", ""),
                    }
                )

            # Extract implementation steps
            if "implementation_steps" in template_data:
                use_case_info["implementation_steps"] = template_data["implementation_steps"]

        return use_case_info

    def _extract_integration_info(
        self, template_data: dict[str, Any], category: str
    ) -> dict[str, Any]:
        """Extract integration information.

        Args:
            template_data: Template data dictionary
            category: Template category

        Returns:
            Integration information dictionary
        """
        integration_info: dict[str, Any] = template_data.get("integration_info", {})

        if category == "integration":
            # Extract integration-specific details
            if "metadata" in template_data:
                metadata = template_data["metadata"]
                integration_info.update(
                    {
                        "description": metadata.get("description", ""),
                        "service_type": metadata.get("service_type", ""),
                        "api_version": metadata.get("api_version", ""),
                    }
                )

            # Extract setup steps
            if "setup_steps" in template_data:
                integration_info["setup_steps"] = template_data["setup_steps"]

        return integration_info

    def _extract_best_practices(self, template_data: dict[str, Any]) -> list[str]:
        """Extract best practices from template data.

        Args:
            template_data: Template data dictionary

        Returns:
            List of best practices
        """
        practices = []

        if "best_practices" in template_data:
            bp = template_data["best_practices"]
            if isinstance(bp, list):
                practices.extend(bp)
            elif isinstance(bp, dict):
                for category_practices in bp.values():
                    if isinstance(category_practices, list):
                        practices.extend(category_practices)
                    else:
                        practices.append(str(category_practices))

        return practices

    def _extract_troubleshooting(self, template_data: dict[str, Any]) -> dict[str, str]:
        """Extract troubleshooting information.

        Args:
            template_data: Template data dictionary

        Returns:
            Dictionary of troubleshooting issues and solutions
        """
        troubleshooting = {}

        if "troubleshooting" in template_data:
            ts = template_data["troubleshooting"]
            if isinstance(ts, dict):
                troubleshooting.update(ts)

        return troubleshooting

    def _extract_examples(self, template_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract examples from template data.

        Args:
            template_data: Template data dictionary

        Returns:
            List of example dictionaries
        """
        examples = []

        if "examples" in template_data:
            ex = template_data["examples"]
            if isinstance(ex, list):
                examples.extend(ex)
            elif isinstance(ex, dict):
                for name, example in ex.items():
                    if isinstance(example, dict):
                        example["name"] = name
                        examples.append(example)
                    else:
                        examples.append({"name": name, "description": str(example)})

        return examples

    def _load_platform_categories(self) -> dict[str, Any]:
        """Load platform categories configuration.

        Returns:
            Platform categories dictionary
        """
        categories_file = self.templates_root / "platforms" / "platform-categories.yml"

        if not categories_file.exists():
            return {}

        try:
            with open(categories_file, encoding="utf-8") as f:
                categories = yaml.safe_load(f)
                return categories if isinstance(categories, dict) else {}
        except Exception:
            return {}


# Convenience functions
def analyze_template_file(
    template_file: Path, templates_root: Path | None = None
) -> TemplateAnalysis:
    """Analyze a single template file."""
    analyzer = ContentAnalyzer(templates_root)
    return analyzer.analyze_template(template_file)


def analyze_template_directory(
    directory: Path, templates_root: Path | None = None
) -> list[TemplateAnalysis]:
    """Analyze all templates in a directory."""
    analyzer = ContentAnalyzer(templates_root)
    template_files = list(directory.glob("*.yml")) + list(directory.glob("*.yaml"))
    return analyzer.analyze_multiple_templates(template_files)
