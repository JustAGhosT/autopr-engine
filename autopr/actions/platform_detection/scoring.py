"""
Scoring Engine Module

Handles confidence calculation and platform ranking for detection results.
"""

import operator
from typing import Any


class PlatformScoringEngine:
    """Calculates confidence scores for platform detection."""

    def __init__(self) -> None:
        self.scoring_weights = {
            "files": 3.0,  # Platform-specific files are strong indicators
            "dependencies": 2.5,  # Dependencies are reliable indicators
            "scripts": 2.0,  # Package scripts indicate usage patterns
            "folders": 1.5,  # Folder patterns show structure
            "content": 1.0,  # Content patterns are weaker but useful
            "commits": 0.8,  # Commit messages can be misleading
        }

    def calculate_platform_scores(
        self,
        platform_configs: dict[str, dict[str, Any]],
        detection_results: dict[str, Any],
    ) -> dict[str, float]:
        """Calculate confidence scores for all platforms."""
        scores = {}

        for platform in platform_configs:
            score = self._calculate_single_platform_score(
                platform, platform_configs[platform], detection_results
            )
            if score > 0:
                scores[platform] = score

        return self._normalize_scores(scores)

    def rank_platforms(
        self, scores: dict[str, float], threshold: float = 0.1
    ) -> tuple[str, list[str]]:
        """Rank platforms by confidence score."""
        # Filter platforms above threshold
        valid_platforms = {k: v for k, v in scores.items() if v >= threshold}

        if not valid_platforms:
            return "unknown", []

        # Sort by score descending
        sorted_platforms = sorted(
            valid_platforms.items(), key=operator.itemgetter(1), reverse=True
        )

        primary_platform = sorted_platforms[0][0]
        secondary_platforms = [platform for platform, _ in sorted_platforms[1:]]

        return primary_platform, secondary_platforms

    def determine_workflow_type(self, scores: dict[str, float]) -> str:
        """Determine the type of workflow based on platform scores."""
        high_confidence_platforms = [
            platform for platform, score in scores.items() if score >= 0.7
        ]
        medium_confidence_platforms = [
            platform for platform, score in scores.items() if 0.3 <= score < 0.7
        ]

        if (
            len(high_confidence_platforms) == 1
            and len(medium_confidence_platforms) == 0
        ):
            return "single_platform"
        if (
            len(high_confidence_platforms) >= 1
            and len(medium_confidence_platforms) >= 1
        ):
            return "hybrid_workflow"
        if len(high_confidence_platforms) + len(medium_confidence_platforms) >= 2:
            return "multi_platform"
        return "single_platform"

    def analyze_hybrid_workflow(
        self, scores: dict[str, float], platform_configs: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze hybrid workflow patterns."""
        categories = {
            "rapid_prototyping": ["replit", "lovable", "bolt", "cursor", "v0"],
            "ai_assisted": ["github_copilot", "codeium", "tabnine"],
            "cloud_deployment": ["vercel", "netlify", "railway"],
        }

        detected_categories = {}
        for category, platforms in categories.items():
            category_scores = {p: scores.get(p, 0) for p in platforms if p in scores}
            if category_scores:
                max_score = max(category_scores.values())
                if max_score >= 0.3:
                    detected_categories[category] = {
                        "primary_platform": max(category_scores, key=category_scores.get),  # type: ignore[arg-type]
                        "confidence": max_score,
                        "all_platforms": category_scores,
                    }

        return {
            "detected_categories": detected_categories,
            "workflow_complexity": len(detected_categories),
            "integration_opportunities": self._identify_integration_opportunities(
                detected_categories
            ),
        }

    def generate_recommendations(
        self,
        primary_platform: str,
        secondary_platforms: list[str],
        scores: dict[str, float],
        workflow_type: str,
    ) -> list[str]:
        """Generate enhancement recommendations based on detection results."""
        recommendations = []

        # Platform-specific recommendations
        platform_recommendations = {
            "replit": [
                "Add Replit-specific deployment configuration",
                "Optimize for Replit's collaborative features",
                "Configure Replit database integration",
            ],
            "lovable": [
                "Enhance component library integration",
                "Add Lovable-specific styling optimizations",
                "Configure automated deployment pipeline",
            ],
            "vercel": [
                "Optimize for Vercel's edge functions",
                "Configure automatic deployments",
                "Add Vercel Analytics integration",
            ],
            "github_copilot": [
                "Add Copilot-friendly code comments",
                "Configure Copilot workspace settings",
                "Optimize code structure for AI assistance",
            ],
        }

        # Add primary platform recommendations
        if primary_platform in platform_recommendations:
            recommendations.extend(platform_recommendations[primary_platform])

        # Add workflow-specific recommendations
        if workflow_type == "hybrid_workflow":
            recommendations.extend(
                [
                    "Configure cross-platform compatibility",
                    "Add environment-specific configurations",
                    "Implement unified deployment strategy",
                ]
            )
        elif workflow_type == "multi_platform":
            recommendations.extend(
                [
                    "Standardize development environments",
                    "Add platform detection scripts",
                    "Configure conditional deployments",
                ]
            )

        # Add general recommendations based on confidence
        max_confidence = max(scores.values()) if scores else 0
        if max_confidence < 0.5:
            recommendations.extend(
                [
                    "Add platform-specific configuration files",
                    "Improve project structure clarity",
                    "Add deployment documentation",
                ]
            )

        return recommendations

    def identify_migration_opportunities(
        self, scores: dict[str, float], platform_configs: dict[str, dict[str, Any]]
    ) -> list[str]:
        """Identify potential migration opportunities."""
        opportunities = []

        # Check for outdated platforms
        legacy_indicators = {
            "heroku": "Consider migrating to Railway or Vercel for better performance",
            "now": "Migrate to Vercel (Now.sh is deprecated)",
            "surge": "Consider Netlify or Vercel for better features",
        }

        for platform, message in legacy_indicators.items():
            if platform in scores and scores[platform] > 0.3:
                opportunities.append(message)

        # Check for platform synergies
        if "replit" in scores and scores["replit"] > 0.5 and "vercel" not in scores:
            opportunities.append(
                "Consider Vercel for production deployment from Replit"
            )

        if "github_copilot" in scores and "cursor" not in scores:
            opportunities.append(
                "Consider Cursor IDE for enhanced AI-assisted development"
            )

        return opportunities

    def _calculate_single_platform_score(
        self,
        platform: str,
        platform_config: dict[str, Any],
        detection_results: dict[str, Any],
    ) -> float:
        """Calculate confidence score for a single platform.

        Args:
            platform: The platform ID to calculate score for
            platform_config: The platform configuration dictionary
            detection_results: Results from the detection analysis

        Returns:
            A confidence score between 0.0 and 1.0
        """
        score = 0.0
        max_possible = 0.0

        # File-based scoring
        if platform in detection_results.get("found_files", {}):
            file_matches = len(detection_results["found_files"][platform])
            score += self.scoring_weights["files"] * min(
                file_matches, 3
            )  # Cap at 3 files
            max_possible += self.scoring_weights["files"] * 3

        # Folder-based scoring
        if platform in detection_results.get("found_folders", {}):
            folder_matches = len(detection_results["found_folders"][platform])
            score += self.scoring_weights["folders"] * min(
                folder_matches, 2
            )  # Cap at 2 folders
            max_possible += self.scoring_weights["folders"] * 2

        # Dependency-based scoring
        platform_deps = set(
            platform_config.get("dependencies", [])
            + platform_config.get("devDependencies", [])
        )
        found_deps = set(detection_results.get("dependencies", []))
        matching_deps = platform_deps.intersection(found_deps)
        score += self.scoring_weights["dependencies"] * min(
            len(matching_deps), 3
        )  # Cap at 3 deps
        max_possible += self.scoring_weights["dependencies"] * 3

        # Script-based scoring
        platform_scripts = set(platform_config.get("package_scripts", []))
        found_scripts = set(detection_results.get("scripts", {}).values())
        matching_scripts = sum(
            1 for script in platform_scripts if any(script in s for s in found_scripts)
        )
        score += self.scoring_weights["scripts"] * min(
            matching_scripts, 2
        )  # Cap at 2 scripts
        max_possible += self.scoring_weights["scripts"] * 2

        # Content-based scoring
        if platform in detection_results.get("content_matches", {}):
            content_matches = len(detection_results["content_matches"][platform])
            score += self.scoring_weights["content"] * min(
                content_matches, 5
            )  # Cap at 5 matches
            max_possible += self.scoring_weights["content"] * 5

        # Commit message scoring
        if platform in detection_results.get("commit_matches", {}):
            commit_matches = detection_results["commit_matches"][platform]
            score += self.scoring_weights["commits"] * min(
                commit_matches, 5
            )  # Cap at 5 commits
            max_possible += self.scoring_weights["commits"] * 5

        # Apply any custom scoring rules from the platform config
        custom_score = float(platform_config.get("scoring", {}).get("base_score", 0.0))
        if custom_score > 0:
            score = max(score, custom_score * max_possible)

        # Normalize the score to 0-1 range based on max possible
        if max_possible > 0:
            score = min(score / max_possible, 1.0)

        return score

    def _normalize_scores(self, scores: dict[str, float]) -> dict[str, float]:
        """Normalize scores to 0-1 range."""
        if not scores:
            return {}

        max_score = max(scores.values())
        if max_score == 0:
            return scores

        # Calculate theoretical maximum score
        max_possible = sum(self.scoring_weights.values())

        # Normalize to 0-1 range
        normalized = {}
        for platform, score in scores.items():
            normalized[platform] = min(score / max_possible, 1.0)

        return normalized

    def _identify_integration_opportunities(
        self, detected_categories: dict[str, Any]
    ) -> list[str]:
        """Identify integration opportunities between detected platforms."""
        opportunities = []

        categories = list(detected_categories.keys())

        if "rapid_prototyping" in categories and "cloud_deployment" in categories:
            opportunities.append("Integrate prototyping platform with cloud deployment")

        if "ai_assisted" in categories and "rapid_prototyping" in categories:
            opportunities.append("Enhance AI assistance in prototyping workflow")

        if len(categories) >= 3:
            opportunities.append(
                "Create unified development pipeline across all platforms"
            )

        return opportunities
