#!/usr/bin/env python3
"""
Template Reports Module
=======================

Handles template report generation and export functionality.
"""

import json
import operator
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .template_models import TemplateInfo


class TemplateReportGenerator:
    """Generates comprehensive reports about templates."""

    def __init__(self, templates: list[TemplateInfo], platform_categories: dict[str, Any]) -> None:
        """Initialize the report generator."""
        self.templates = templates
        self.platform_categories = platform_categories

    def generate_template_report(self) -> dict[str, Any]:
        """Generate a comprehensive report of all templates."""
        report: dict[str, Any] = {
            "summary": {
                "total_templates": len(self.templates),
                "generated_at": datetime.now().isoformat(),
                "categories": {},
                "platforms": {},
                "complexity_distribution": {},
            },
            "templates_by_category": {},
            "platform_coverage": {},
            "recommendations": {},
        }

        # Count by category
        for template in self.templates:
            category = template.category
            if category not in report["summary"]["categories"]:
                report["summary"]["categories"][category] = 0
            report["summary"]["categories"][category] += 1

            if category not in report["templates_by_category"]:
                report["templates_by_category"][category] = []
            report["templates_by_category"][category].append(
                {
                    "name": template.name,
                    "platforms": template.platforms,
                    "complexity": template.complexity,
                }
            )

        # Count by platform
        platform_counts: dict[str, int] = defaultdict(int)
        for template in self.templates:
            for platform in template.platforms:
                platform_counts[platform] += 1
        report["summary"]["platforms"] = dict(platform_counts)

        # Complexity distribution
        complexity_counts: dict[str, int] = defaultdict(int)
        for template in self.templates:
            complexity_counts[template.complexity] += 1
        report["summary"]["complexity_distribution"] = dict(complexity_counts)

        # Platform coverage analysis
        for platform in platform_counts:
            platform_templates = [t for t in self.templates if platform in t.platforms]
            report["platform_coverage"][platform] = {
                "total_templates": len(platform_templates),
                "categories": list({t.category for t in platform_templates}),
                "use_cases": list({uc for t in platform_templates for uc in t.use_cases}),
            }

        return report

    def generate_platform_summary(self) -> dict[str, Any]:
        """Generate a summary of platform coverage and capabilities."""
        platform_summary: dict[str, Any] = {}

        # Group templates by platform
        platform_templates: dict[str, list[TemplateInfo]] = defaultdict(list)
        for template in self.templates:
            for platform in template.platforms:
                platform_templates[platform].append(template)

        for platform, templates in platform_templates.items():
            if platform == "unknown":
                continue

            # Calculate platform metrics
            categories = list({t.category for t in templates})
            use_cases = list({uc for t in templates for uc in t.use_cases})
            features = list({f for t in templates for f in t.key_features})

            complexity_dist: dict[str, int] = defaultdict(int)
            for template in templates:
                complexity_dist[template.complexity] += 1

            platform_summary[platform] = {
                "template_count": len(templates),
                "categories": categories,
                "use_cases": use_cases[:10],  # Top 10 use cases
                "key_features": features[:15],  # Top 15 features
                "complexity_distribution": dict(complexity_dist),
                "avg_complexity_score": self._calculate_avg_complexity(templates),
            }

        return platform_summary

    def generate_category_analysis(self) -> dict[str, Any]:
        """Generate analysis of template categories."""
        category_analysis: dict[str, Any] = {}

        # Group templates by category
        category_templates: dict[str, list[TemplateInfo]] = defaultdict(list)
        for template in self.templates:
            category_templates[template.category].append(template)

        for category, templates in category_templates.items():
            platforms = list({p for t in templates for p in t.platforms})
            use_cases = list({uc for t in templates for uc in t.use_cases})

            category_analysis[category] = {
                "template_count": len(templates),
                "platforms": platforms,
                "use_cases": use_cases,
                "avg_complexity_score": self._calculate_avg_complexity(templates),
                "most_common_features": self._get_most_common_features(templates),
            }

        return category_analysis

    def export_templates_json(
        self, output_file: str | None = None, templates_root: Path | None = None
    ) -> str:
        """Export all template metadata to JSON format."""
        if output_file is None:
            if templates_root:
                output_file = str(templates_root / "templates_metadata.json")
            else:
                output_file = "templates_metadata.json"

        templates_data = [asdict(template) for template in self.templates]

        export_data = {
            "metadata": {
                "total_templates": len(self.templates),
                "generated_at": datetime.now().isoformat(),
                "version": "1.0.0",
            },
            "platform_categories": self.platform_categories,
            "templates": templates_data,
            "summary": self.generate_template_report()["summary"],
            "platform_summary": self.generate_platform_summary(),
            "category_analysis": self.generate_category_analysis(),
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return output_file

    def export_templates_csv(
        self, output_file: str | None = None, templates_root: Path | None = None
    ) -> str:
        """Export template metadata to CSV format."""
        if output_file is None:
            if templates_root:
                output_file = str(templates_root / "templates_metadata.csv")
            else:
                output_file = "templates_metadata.csv"

        import csv

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "Name",
                    "Description",
                    "Category",
                    "Platforms",
                    "Complexity",
                    "Estimated Time",
                    "Use Cases",
                    "Key Features",
                    "Dependencies",
                ]
            )

            # Write template data
            for template in self.templates:
                writer.writerow(
                    [
                        template.name,
                        template.description,
                        template.category,
                        "; ".join(template.platforms),
                        template.complexity,
                        template.estimated_time,
                        "; ".join(template.use_cases),
                        "; ".join(template.key_features),
                        "; ".join(template.dependencies),
                    ]
                )

        return output_file

    def _calculate_avg_complexity(self, templates: list[TemplateInfo]) -> float:
        """Calculate average complexity score for templates."""
        if not templates:
            return 0.0

        complexity_mapping = {
            "beginner": 1,
            "easy": 1,
            "simple": 1,
            "medium": 2,
            "intermediate": 3,
            "advanced": 4,
            "expert": 5,
            "complex": 5,
        }

        total_score = sum(complexity_mapping.get(t.complexity.lower(), 2) for t in templates)
        return total_score / len(templates)

    def _get_most_common_features(
        self, templates: list[TemplateInfo], limit: int = 10
    ) -> list[str]:
        """Get most common features across templates."""
        feature_counts: dict[str, int] = defaultdict(int)

        for template in templates:
            for feature in template.key_features:
                feature_counts[feature.lower()] += 1

        # Sort by frequency and return top features
        sorted_features = sorted(feature_counts.items(), key=operator.itemgetter(1), reverse=True)
        return [feature for feature, _ in sorted_features[:limit]]
