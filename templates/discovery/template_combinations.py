#!/usr/bin/env python3
"""
Template Combinations Module
============================

Handles template combinations and use case recommendations.
"""

from typing import TypedDict

from .template_models import TemplateCombination, TemplateInfo


class CombinationDict(TypedDict):
    platform: str
    main_template: str
    recommended_integrations: list[str]
    estimated_total_time: str
    complexity_score: int


class TemplateCombinationEngine:
    """Generates template combinations for specific use cases."""

    def __init__(self, templates: list[TemplateInfo]) -> None:
        """Initialize the combination engine."""
        self.templates = templates

    def get_template_combinations(self, use_case: str) -> list[CombinationDict]:
        """Get recommended template combinations for a specific use case."""
        combinations: list[CombinationDict] = []

        # Find use case templates
        use_case_templates = [
            t
            for t in self.templates
            if t.category == "use_case_template" and use_case.lower() in t.name.lower()
        ]

        if not use_case_templates:
            return combinations

        main_template = use_case_templates[0]

        # Find relevant integration templates
        integration_templates = [t for t in self.templates if t.category == "integration_template"]

        # Create combinations for each platform
        for platform in main_template.platforms:
            combination_data: CombinationDict = {
                "platform": platform,
                "main_template": main_template.name,
                "recommended_integrations": [],
                "estimated_total_time": main_template.estimated_time,
                "complexity_score": self._complexity_to_score(main_template.complexity),
            }

            # Add relevant integrations based on use case
            if "ecommerce" in use_case.lower():
                auth_template = next(
                    (t for t in integration_templates if "auth" in t.name.lower()), None
                )
                payment_template = next(
                    (t for t in integration_templates if "payment" in t.name.lower()), None
                )

                if auth_template and platform in auth_template.platforms:
                    combination_data["recommended_integrations"].append(auth_template.name)
                if payment_template and platform in payment_template.platforms:
                    combination_data["recommended_integrations"].append(payment_template.name)

            elif "social" in use_case.lower():
                auth_template = next(
                    (t for t in integration_templates if "auth" in t.name.lower()), None
                )
                if auth_template and platform in auth_template.platforms:
                    combination_data["recommended_integrations"].append(auth_template.name)

            combinations.append(combination_data)

        return combinations

    def get_integration_recommendations(self, template: TemplateInfo) -> list[TemplateInfo]:
        """Get integration recommendations for a specific template."""
        if not template:
            return []

        integration_templates = [t for t in self.templates if t.category == "integration"]

        # Prefer comprehension for performance and clarity
        recommendations: list[TemplateInfo] = [
            integration
            for integration in integration_templates
            if any(platform in integration.platforms for platform in template.platforms)
            and self._has_compatible_features(template, integration)
        ]

        return recommendations[:5]  # Return top 5 recommendations

    def get_workflow_templates(self, main_template: TemplateInfo) -> list[TemplateInfo]:
        """Get workflow templates that complement the main template."""
        if not main_template:
            return []

        workflow_templates: list[TemplateInfo] = []

        # Find templates in the same category or related categories
        for template in self.templates:
            if template.name == main_template.name:
                continue

            # Check if templates are complementary
            if self._are_templates_complementary(main_template, template):
                workflow_templates.append(template)

        return workflow_templates[:3]  # Return top 3 workflow templates

    def create_template_combination(
        self, main_template: TemplateInfo, integrations: list[TemplateInfo], platform: str
    ) -> TemplateCombination:
        """Create a structured template combination."""
        integration_names = [t.name for t in integrations]

        # Calculate combined complexity
        complexity_scores = [self._complexity_to_score(main_template.complexity)]
        complexity_scores.extend(self._complexity_to_score(t.complexity) for t in integrations)
        avg_complexity = int(sum(complexity_scores) / len(complexity_scores))

        return TemplateCombination(
            platform=platform,
            main_template=main_template.name,
            recommended_integrations=integration_names,
            estimated_total_time=self._estimate_total_time(main_template, integrations),
            complexity_score=avg_complexity,
        )

    def _complexity_to_score(self, complexity: str) -> int:
        """Convert complexity string to numeric score."""
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
        return complexity_mapping.get(complexity.lower(), 2)

    def _has_compatible_features(self, template1: TemplateInfo, template2: TemplateInfo) -> bool:
        """Check if two templates have compatible features."""
        # Check for complementary features
        template1_features = [f.lower() for f in template1.key_features]
        template2_features = [f.lower() for f in template2.key_features]

        # Look for common themes or complementary functionality
        common_themes = ["auth", "payment", "database", "api", "storage", "notification"]

        for theme in common_themes:
            if any(theme in f for f in template1_features) and any(
                theme in f for f in template2_features
            ):
                return True

        return False

    def _are_templates_complementary(
        self, template1: TemplateInfo, template2: TemplateInfo
    ) -> bool:
        """Check if templates are complementary for workflow purposes."""
        # Check platform compatibility
        if not any(p in template2.platforms for p in template1.platforms):
            return False

        # Check if they serve different but related purposes
        category_combinations = [
            ("platform", "integration"),
            ("use_case", "integration"),
            ("platform", "use_case"),
        ]

        for cat1, cat2 in category_combinations:
            if (template1.category == cat1 and template2.category == cat2) or (
                template1.category == cat2 and template2.category == cat1
            ):
                return True

        return False

    def _estimate_total_time(
        self, main_template: TemplateInfo, integrations: list[TemplateInfo]
    ) -> str:
        """Estimate total time for template combination."""
        # Simple time estimation logic
        time_mapping = {
            "minutes": 1,
            "hour": 2,
            "hours": 3,
            "day": 4,
            "days": 5,
            "week": 6,
            "weeks": 7,
        }

        main_time = 3  # Default
        for time_unit, score in time_mapping.items():
            if time_unit in main_template.estimated_time.lower():
                main_time = score
                break

        integration_time = sum(2 for _ in integrations)  # 2 points per integration
        total_score = main_time + integration_time

        thresh_2 = 2
        thresh_4 = 4
        thresh_6 = 6
        thresh_8 = 8
        if total_score <= thresh_2:
            return "1-2 hours"
        if total_score <= thresh_4:
            return "3-6 hours"
        if total_score <= thresh_6:
            return "1-2 days"
        if total_score <= thresh_8:
            return "3-5 days"
        return "1-2 weeks"
