#!/usr/bin/env python3
"""
JSON Format Generator Module
===========================

Generates documentation in JSON format.
"""

import json
from datetime import datetime
from typing import Any

from ..content_analyzer import TemplateAnalysis
from .base import BaseFormatGenerator


class JSONGenerator(BaseFormatGenerator):
    """Generates JSON documentation."""

    def generate_platform_guide(self, analysis: TemplateAnalysis) -> str:
        """Generate platform guide in JSON format."""
        data = {
            "name": analysis.name,
            "title": analysis.name.replace("_", " ").title(),
            "category": analysis.category,
            "generated_at": datetime.now().isoformat(),
            "metadata": analysis.metadata,
            "platform_info": analysis.platform_info,
            "key_features": analysis.key_features,
            "variables": analysis.variables,
            "complexity": analysis.complexity,
            "estimated_time": analysis.estimated_time,
            "dependencies": analysis.dependencies,
            "best_practices": analysis.best_practices,
            "troubleshooting": analysis.troubleshooting,
            "examples": analysis.examples,
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def generate_use_case_guide(self, analysis: TemplateAnalysis) -> str:
        """Generate use case guide in JSON format."""
        data = {
            "name": analysis.name,
            "title": analysis.name.replace("_", " ").title(),
            "category": analysis.category,
            "generated_at": datetime.now().isoformat(),
            "metadata": analysis.metadata,
            "use_case_info": analysis.use_case_info,
            "key_features": analysis.key_features,
            "variables": analysis.variables,
            "complexity": analysis.complexity,
            "estimated_time": analysis.estimated_time,
            "dependencies": analysis.dependencies,
            "best_practices": analysis.best_practices,
            "troubleshooting": analysis.troubleshooting,
            "examples": analysis.examples,
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def generate_integration_guide(self, analysis: TemplateAnalysis) -> str:
        """Generate integration guide in JSON format."""
        data = {
            "name": analysis.name,
            "title": analysis.name.replace("_", " ").title(),
            "category": analysis.category,
            "generated_at": datetime.now().isoformat(),
            "metadata": analysis.metadata,
            "integration_info": analysis.integration_info,
            "key_features": analysis.key_features,
            "variables": analysis.variables,
            "complexity": analysis.complexity,
            "estimated_time": analysis.estimated_time,
            "dependencies": analysis.dependencies,
            "best_practices": analysis.best_practices,
            "troubleshooting": analysis.troubleshooting,
            "examples": analysis.examples,
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def generate_main_index(self, analyses: list[TemplateAnalysis]) -> str:
        """Generate main documentation index in JSON format."""
        return self.generate_summary_data(analyses)

    def generate_comparison_guide(self, platform_analyses: list[TemplateAnalysis]) -> str:
        """Generate platform comparison guide in JSON format."""
        comparison: dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "comparison_type": "platform_comparison",
            "total_platforms": len(platform_analyses),
            "platforms": [],
        }

        for analysis in platform_analyses:
            platform_data = {
                "name": analysis.name,
                "title": analysis.name.replace("_", " ").title(),
                "complexity": analysis.complexity,
                "estimated_time": analysis.estimated_time,
                "key_features": analysis.key_features,
                "platform_info": analysis.platform_info,
                "dependencies": analysis.dependencies,
            }
            comparison["platforms"].append(platform_data)

        return json.dumps(comparison, indent=2, ensure_ascii=False)

    def generate_summary_data(self, analyses: list[TemplateAnalysis]) -> str:
        """Generate summary data for all templates."""
        summary: dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "total_templates": len(analyses),
            "categories": {},
            "templates": [],
        }

        # Group by category
        for analysis in analyses:
            if analysis.category not in summary["categories"]:
                summary["categories"][analysis.category] = 0
            summary["categories"][analysis.category] += 1

            # Add template summary
            summary["templates"].append(
                {
                    "name": analysis.name,
                    "title": analysis.name.replace("_", " ").title(),
                    "category": analysis.category,
                    "complexity": analysis.complexity,
                    "estimated_time": analysis.estimated_time,
                    "key_features_count": len(analysis.key_features),
                    "variables_count": len(analysis.variables),
                    "has_examples": len(analysis.examples) > 0,
                }
            )

        return json.dumps(summary, indent=2, ensure_ascii=False)
