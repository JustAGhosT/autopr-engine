#!/usr/bin/env python3
"""
Template Search Module
======================

Handles template search, filtering, and discovery functionality.
"""

import operator

from .template_models import TemplateInfo


class TemplateSearchEngine:
    """Handles template search and filtering operations."""

    def __init__(self, templates: list[TemplateInfo]) -> None:
        """Initialize the search engine with templates."""
        self.templates = templates

    def search_templates(
        self,
        query: str | None = None,
        category: str | None = None,
        platform: str | None = None,
        complexity: str | None = None,
        use_case: str | None = None,
    ) -> list[TemplateInfo]:
        """Search templates based on various criteria."""
        results = self.templates.copy()

        # Filter by query (search in name, description, features)
        if query:
            query_lower = query.lower()
            results = [
                t
                for t in results
                if (
                    query_lower in t.name.lower()
                    or query_lower in t.description.lower()
                    or any(query_lower in feature.lower() for feature in t.key_features)
                    or any(query_lower in uc.lower() for uc in t.use_cases)
                )
            ]

        # Filter by category
        if category:
            results = [t for t in results if t.category.lower() == category.lower()]

        # Filter by platform
        if platform:
            platform_lower = platform.lower()
            results = [t for t in results if any(platform_lower in p.lower() for p in t.platforms)]

        # Filter by complexity
        if complexity:
            results = [t for t in results if t.complexity.lower() == complexity.lower()]

        # Filter by use case
        if use_case:
            use_case_lower = use_case.lower()
            results = [
                t for t in results if any(use_case_lower in uc.lower() for uc in t.use_cases)
            ]

        return results

    def search_by_features(self, required_features: list[str]) -> list[TemplateInfo]:
        """Search templates that have all required features."""
        if not required_features:
            return self.templates.copy()

        required_lower = [f.lower() for f in required_features]
        results: list[TemplateInfo] = []

        for template in self.templates:
            template_features_lower = [f.lower() for f in template.key_features]
            if all(req in " ".join(template_features_lower) for req in required_lower):
                results.append(template)

        return results

    def search_by_dependencies(self, dependencies: list[str]) -> list[TemplateInfo]:
        """Search templates that have specific dependencies."""
        if not dependencies:
            return self.templates.copy()

        deps_lower = [d.lower() for d in dependencies]
        results: list[TemplateInfo] = []

        for template in self.templates:
            template_deps_lower = [d.lower() for d in template.dependencies]
            if any(dep in template_deps_lower for dep in deps_lower):
                results.append(template)

        return results

    def get_templates_by_category(self) -> dict[str, list[TemplateInfo]]:
        """Group templates by category."""
        categories: dict[str, list[TemplateInfo]] = {}

        for template in self.templates:
            if template.category not in categories:
                categories[template.category] = []
            categories[template.category].append(template)

        return categories

    def get_templates_by_platform(self) -> dict[str, list[TemplateInfo]]:
        """Group templates by platform."""
        platforms: dict[str, list[TemplateInfo]] = {}

        for template in self.templates:
            for platform in template.platforms:
                if platform not in platforms:
                    platforms[platform] = []
                platforms[platform].append(template)

        return platforms

    def get_templates_by_complexity(self) -> dict[str, list[TemplateInfo]]:
        """Group templates by complexity level."""
        complexity_groups: dict[str, list[TemplateInfo]] = {}

        for template in self.templates:
            complexity = template.complexity
            if complexity not in complexity_groups:
                complexity_groups[complexity] = []
            complexity_groups[complexity].append(template)

        return complexity_groups

    def find_similar_templates(self, template: TemplateInfo, limit: int = 5) -> list[TemplateInfo]:
        """Find templates similar to the given template."""
        if not template:
            return []

        similar: list[tuple[TemplateInfo, float]] = []

        for other in self.templates:
            if other.name == template.name:
                continue

            similarity_score = self._calculate_similarity(template, other)
            if similarity_score > 0.1:  # Minimum similarity threshold
                similar.append((other, similarity_score))

        # Sort by similarity score (descending) and return top results
        similar.sort(key=operator.itemgetter(1), reverse=True)
        return [t for t, _ in similar[:limit]]

    def _calculate_similarity(self, template1: TemplateInfo, template2: TemplateInfo) -> float:
        """Calculate similarity score between two templates."""
        score = 0.0

        # Category similarity (high weight)
        if template1.category == template2.category:
            score += 0.3

        # Platform overlap
        platform_overlap = len(set(template1.platforms) & set(template2.platforms))
        if platform_overlap > 0:
            score += 0.2 * (
                platform_overlap / max(len(template1.platforms), len(template2.platforms))
            )

        # Use case overlap
        use_case_overlap = len(set(template1.use_cases) & set(template2.use_cases))
        if use_case_overlap > 0:
            score += 0.2 * (
                use_case_overlap / max(len(template1.use_cases), len(template2.use_cases))
            )

        # Feature overlap
        feature_overlap = len(set(template1.key_features) & set(template2.key_features))
        if feature_overlap > 0:
            score += 0.2 * (
                feature_overlap / max(len(template1.key_features), len(template2.key_features))
            )

        # Complexity similarity
        if template1.complexity == template2.complexity:
            score += 0.1

        return min(1.0, score)  # Cap at 1.0
