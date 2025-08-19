#!/usr/bin/env python3
"""
Platform Recommendations Module
===============================

Handles platform recommendations based on project requirements.
"""

import operator
from typing import Any

from discovery.template_models import PlatformRequirements, TemplateInfo


class PlatformRecommendationEngine:
    """Generates platform recommendations based on requirements."""

    def __init__(
        self, templates: list[TemplateInfo], platform_categories: dict[str, Any]
    ) -> None:
        """Initialize the recommendation engine."""
        self.templates = templates
        self.platform_categories = platform_categories

    def get_platform_recommendations(
        self, requirements: dict[str, Any]
    ) -> list[tuple[str, float, str]]:
        """Get platform recommendations based on project requirements."""
        # Convert dict to PlatformRequirements for type safety
        req = PlatformRequirements(
            project_type=requirements.get("project_type", ""),
            team_size=requirements.get("team_size", ""),
            technical_expertise=requirements.get("technical_expertise", ""),
            budget=requirements.get("budget", ""),
            timeline=requirements.get("timeline", ""),
            features=requirements.get("features", []),
        )

        platform_scores: dict[str, float] = {}
        platform_reasoning: dict[str, list[str]] = {}

        # Get all unique platforms from templates
        all_platforms = set()
        for template in self.templates:
            all_platforms.update(template.platforms)

        for platform in all_platforms:
            if platform == "unknown":
                continue

            score, reasons = self._score_platform(platform, req)
            platform_scores[platform] = score
            platform_reasoning[platform] = reasons

        # Sort by score and return top recommendations
        sorted_platforms = sorted(
            platform_scores.items(), key=operator.itemgetter(1), reverse=True
        )

        recommendations: list[tuple[str, float, str]] = []
        for platform, score in sorted_platforms[:5]:  # Top 5 recommendations
            reasoning = "; ".join(platform_reasoning[platform])
            recommendations.append((platform, score, reasoning))

        return recommendations

    def _score_platform(
        self, platform: str, requirements: PlatformRequirements
    ) -> tuple[float, list[str]]:
        """Score a platform based on requirements."""
        score = 0.0
        reasons: list[str] = []

        # Get platform templates
        platform_templates = [t for t in self.templates if platform in t.platforms]
        if not platform_templates:
            return 0.0, ["No templates available"]

        # Project type scoring
        if requirements.project_type:
            project_score = self._score_project_type(
                platform, requirements.project_type, platform_templates
            )
            score += project_score * 2.0  # High weight
            if project_score > 0.5:
                reasons.append(f"Good fit for {requirements.project_type}")

        # Team size scoring
        if requirements.team_size:
            team_score = self._score_team_size(platform, requirements.team_size)
            score += team_score * 1.5
            if team_score > 0.5:
                reasons.append(f"Suitable for {requirements.team_size} teams")

        # Technical expertise scoring
        if requirements.technical_expertise:
            expertise_score = self._score_technical_expertise(
                platform, requirements.technical_expertise
            )
            score += expertise_score * 1.5
            if expertise_score > 0.5:
                reasons.append(
                    f"Matches {requirements.technical_expertise} skill level"
                )

        # Budget scoring
        if requirements.budget:
            budget_score = self._score_budget(platform, requirements.budget)
            score += budget_score * 1.0
            if budget_score > 0.5:
                reasons.append(f"Fits {requirements.budget} budget")

        # Timeline scoring
        if requirements.timeline:
            timeline_score = self._score_timeline(platform, requirements.timeline)
            score += timeline_score * 1.0
            if timeline_score > 0.5:
                reasons.append(f"Good for {requirements.timeline} timeline")

        # Features scoring
        if requirements.features:
            feature_score = self._score_features(
                platform, requirements.features, platform_templates
            )
            score += feature_score * 1.5
            if feature_score > 0.5:
                reasons.append("Supports required features")

        # Template availability bonus
        template_count = len(platform_templates)
        availability_score = min(1.0, template_count / 10.0)  # Normalize to 0-1
        score += availability_score * 0.5
        if template_count > 5:
            reasons.append(f"{template_count} templates available")

        return min(10.0, score), reasons  # Cap at 10.0

    def _score_project_type(
        self, platform: str, project_type: str, templates: list[TemplateInfo]
    ) -> float:
        """Score platform based on project type compatibility."""
        type_mapping = {
            "web_app": ["bubble", "webflow", "framer", "wordpress", "squarespace"],
            "mobile_app": ["thunkable", "adalo", "glide", "bubble"],
            "ecommerce": ["shopify", "woocommerce", "squarespace", "webflow"],
            "blog": ["wordpress", "ghost", "medium", "substack"],
            "portfolio": ["framer", "webflow", "squarespace", "behance"],
            "business_site": ["wordpress", "squarespace", "webflow", "wix"],
            "automation": ["zapier", "integromat", "n8n", "automate.io"],
            "database": ["airtable", "notion", "google_sheets", "smartsuite"],
        }

        if project_type in type_mapping:
            if platform.lower() in [p.lower() for p in type_mapping[project_type]]:
                return 1.0

        # Check template use cases
        for template in templates:
            if any(project_type.lower() in uc.lower() for uc in template.use_cases):
                return 0.8

        return 0.2  # Default low score

    def _score_team_size(self, platform: str, team_size: str) -> float:
        """Score platform based on team size suitability."""
        team_mapping = {
            "solo": 0.9,  # Most platforms work well for solo developers
            "small": 0.8,
            "medium": 0.6,
            "large": 0.4,
            "enterprise": 0.2,
        }

        return team_mapping.get(team_size.lower(), 0.5)

    def _score_technical_expertise(self, platform: str, expertise: str) -> float:
        """Score platform based on technical expertise requirements."""
        # No-code platforms generally favor lower technical expertise
        expertise_mapping = {
            "beginner": 0.9,
            "intermediate": 0.7,
            "advanced": 0.5,
            "expert": 0.3,
        }

        return expertise_mapping.get(expertise.lower(), 0.5)

    def _score_budget(self, platform: str, budget: str) -> float:
        """Score platform based on budget constraints."""
        # Most no-code platforms have reasonable pricing
        budget_mapping = {
            "free": 0.6,  # Limited but possible
            "low": 0.8,
            "medium": 0.9,
            "high": 0.7,  # Might be overkill
            "unlimited": 0.5,
        }

        return budget_mapping.get(budget.lower(), 0.5)

    def _score_timeline(self, platform: str, timeline: str) -> float:
        """Score platform based on development timeline."""
        # No-code platforms generally favor faster timelines
        timeline_mapping = {
            "immediate": 0.9,
            "short": 0.8,
            "medium": 0.7,
            "long": 0.5,
            "extended": 0.3,
        }

        return timeline_mapping.get(timeline.lower(), 0.5)

    def _score_features(
        self, platform: str, required_features: list[str], templates: list[TemplateInfo]
    ) -> float:
        """Score platform based on feature availability."""
        if not required_features:
            return 0.5

        available_features: set[str] = set()
        for template in templates:
            available_features.update(f.lower() for f in template.key_features)

        required_lower = [f.lower() for f in required_features]
        # Count how many required features are available
        matched_features = 0
        for feature in required_lower:
            if any(feature in available for available in available_features):
                matched_features += 1

        return matched_features / len(required_features) if required_features else 0.0
