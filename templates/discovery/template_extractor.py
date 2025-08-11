#!/usr/bin/env python3
"""
Template Extractor Module
========================

Extracts and analyzes YAML templates from the template directory.
Provides comprehensive template discovery, parsing, and categorization.
"""

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class TemplateInfo:
    """Information about a discovered template."""

    name: str
    description: str
    category: str
    platforms: list[str]
    file_path: Path
    variables: dict[str, Any]
    platform_info: dict[str, Any]
    metadata: dict[str, Any]


class TemplateExtractor:
    """Extracts and analyzes YAML templates."""

    def __init__(self, templates_root: Path):
        """Initialize the template extractor.

        Args:
            templates_root: Root directory containing templates
        """
        self.templates_root = Path(templates_root)
        self.templates: list[TemplateInfo] = []
        self.categories: dict[str, list[TemplateInfo]] = defaultdict(list)

    def discover_templates(self) -> list[TemplateInfo]:
        """Discover all YAML templates in the directory structure.

        Returns:
            List of discovered template information
        """
        self.templates.clear()
        self.categories.clear()

        # Find all YAML files
        yaml_files = []
        for pattern in ["**/*.yml", "**/*.yaml"]:
            yaml_files.extend(self.templates_root.glob(pattern))

        # Parse each template
        for yaml_file in yaml_files:
            try:
                template_info = self._parse_template(yaml_file)
                if template_info:
                    self.templates.append(template_info)
                    self.categories[template_info.category].append(template_info)
            except Exception:
                continue

        return self.templates

    def _parse_template(self, yaml_file: Path) -> TemplateInfo | None:
        """Parse a single YAML template file.

        Args:
            yaml_file: Path to the YAML file

        Returns:
            TemplateInfo object or None if parsing fails
        """
        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict):
                return None

            # Extract required fields
            name = data.get("name", yaml_file.stem)
            description = data.get("description", "")
            category = data.get("category", "unknown")
            platforms = data.get("platforms", [])
            variables = data.get("variables", {})
            platform_info = data.get("platform_info", {})

            # Extract additional metadata
            metadata = {
                k: v
                for k, v in data.items()
                if k
                not in {
                    "name",
                    "description",
                    "category",
                    "platforms",
                    "variables",
                    "platform_info",
                }
            }

            return TemplateInfo(
                name=name,
                description=description,
                category=category,
                platforms=platforms,
                file_path=yaml_file,
                variables=variables,
                platform_info=platform_info,
                metadata=metadata,
            )

        except Exception:
            return None

    def get_templates_by_category(self) -> dict[str, list[TemplateInfo]]:
        """Get templates grouped by category.

        Returns:
            Dictionary mapping categories to template lists
        """
        return dict(self.categories)

    def get_templates_by_platform(self) -> dict[str, list[TemplateInfo]]:
        """Get templates grouped by platform.

        Returns:
            Dictionary mapping platforms to template lists
        """
        platform_templates = defaultdict(list)
        for template in self.templates:
            for platform in template.platforms:
                platform_templates[platform].append(template)
        return dict(platform_templates)

    def search_templates(self, query: str) -> list[TemplateInfo]:
        """Search templates by name or description.

        Args:
            query: Search query

        Returns:
            List of matching templates
        """
        query_lower = query.lower()

        return [
            template
            for template in self.templates
            if query_lower in template.name.lower()
            or query_lower in template.description.lower()
            or any(query_lower in platform.lower() for platform in template.platforms)
        ]

    def export_template_catalog(self, output_file: Path, format: str = "json") -> None:
        """Export template catalog to file.

        Args:
            output_file: Output file path
            format: Export format ('json', 'yaml', 'markdown')
        """
        if format == "json":
            self._export_json(output_file)
        elif format == "yaml":
            self._export_yaml(output_file)
        elif format == "markdown":
            self._export_markdown(output_file)
        else:
            msg = f"Unsupported format: {format}"
            raise ValueError(msg)

    def _export_json(self, output_file: Path) -> None:
        """Export catalog as JSON."""
        catalog = {
            "total_templates": len(self.templates),
            "categories": {cat: len(templates) for cat, templates in self.categories.items()},
            "templates": [],
        }

        for template in self.templates:
            catalog["templates"].append(
                {
                    "name": template.name,
                    "description": template.description,
                    "category": template.category,
                    "platforms": template.platforms,
                    "file_path": str(template.file_path.relative_to(self.templates_root)),
                    "variables_count": len(template.variables),
                    "has_platform_info": bool(template.platform_info),
                    "metadata_keys": list(template.metadata.keys()),
                }
            )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)

    def _export_yaml(self, output_file: Path) -> None:
        """Export catalog as YAML."""
        catalog = {
            "total_templates": len(self.templates),
            "categories": dict(self.categories),
            "templates": [
                {
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "platforms": t.platforms,
                    "file_path": str(t.file_path.relative_to(self.templates_root)),
                }
                for t in self.templates
            ],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(catalog, f, default_flow_style=False, allow_unicode=True)

    def _export_markdown(self, output_file: Path) -> None:
        """Export catalog as Markdown."""
        content = f"""# Template Catalog

Total Templates: {len(self.templates)}
Categories: {len(self.categories)}

## Categories

"""

        for category, templates in self.categories.items():
            content += f"### {category.replace('_', ' ').title()} ({len(templates)} templates)\n\n"

            for template in sorted(templates, key=lambda t: t.name):
                platforms_str = ", ".join(template.platforms) if template.platforms else "N/A"
                content += f"- **{template.name}**\n"
                content += f"  - Description: {template.description}\n"
                content += f"  - Platforms: {platforms_str}\n"
                content += f"  - Variables: {len(template.variables)}\n"
                content += f"  - File: `{template.file_path.relative_to(self.templates_root)}`\n\n"

        content += "\n## Platform Distribution\n\n"
        platform_templates = self.get_templates_by_platform()
        for platform, templates in sorted(platform_templates.items()):
            content += f"- **{platform}**: {len(templates)} templates\n"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

    def get_template_statistics(self) -> dict[str, Any]:
        """Get comprehensive template statistics.

        Returns:
            Dictionary with various statistics
        """
        stats = {
            "total_templates": len(self.templates),
            "categories": {cat: len(templates) for cat, templates in self.categories.items()},
            "platforms": {},
            "variables_stats": {
                "total_variables": 0,
                "avg_variables_per_template": 0,
                "most_common_variables": {},
            },
            "file_distribution": {},
        }

        # Platform statistics
        platform_templates = self.get_templates_by_platform()
        stats["platforms"] = {
            platform: len(templates) for platform, templates in platform_templates.items()
        }

        # Variable statistics
        all_variables = []
        for template in self.templates:
            all_variables.extend(template.variables.keys())

        stats["variables_stats"]["total_variables"] = len(all_variables)
        if self.templates:
            stats["variables_stats"]["avg_variables_per_template"] = len(all_variables) / len(
                self.templates
            )

        # Most common variables
        from collections import Counter

        variable_counts = Counter(all_variables)
        stats["variables_stats"]["most_common_variables"] = dict(variable_counts.most_common(10))

        # File distribution by directory
        file_dirs = defaultdict(int)
        for template in self.templates:
            parent_dir = template.file_path.parent.name
            file_dirs[parent_dir] += 1
        stats["file_distribution"] = dict(file_dirs)

        return stats


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract and analyze YAML templates")
    parser.add_argument("templates_dir", help="Path to templates directory")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument(
        "--format", "-f", choices=["json", "yaml", "markdown"], default="json", help="Output format"
    )
    parser.add_argument("--search", "-s", help="Search query")
    parser.add_argument("--category", "-c", help="Filter by category")
    parser.add_argument("--platform", "-p", help="Filter by platform")

    args = parser.parse_args()

    # Initialize extractor
    extractor = TemplateExtractor(Path(args.templates_dir))
    templates = extractor.discover_templates()

    # Apply filters
    filtered_templates = templates

    if args.search:
        filtered_templates = extractor.search_templates(args.search)

    if args.category:
        filtered_templates = [t for t in filtered_templates if t.category == args.category]

    if args.platform:
        filtered_templates = [t for t in filtered_templates if args.platform in t.platforms]

    # Display results
    if not args.output:
        # Print to console
        for _template in filtered_templates:
            pass
    else:
        # Export to file
        extractor.templates = filtered_templates  # Update templates list for export
        extractor.export_template_catalog(Path(args.output), args.format)

    # Show statistics
    extractor.get_template_statistics()


if __name__ == "__main__":
    main()
