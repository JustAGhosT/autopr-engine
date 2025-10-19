"""
Platform Detector

Main platform detection logic and orchestration.
"""

from pathlib import Path
from typing import Any

from .models import PlatformDetectorInputs, PlatformDetectorOutputs
from .patterns import PlatformPatterns


class PlatformDetector:
    """Detects which rapid prototyping platform was used and routes accordingly."""

    def __init__(self) -> None:
        self.platform_signatures = PlatformPatterns.get_platform_signatures()
        self.advanced_patterns = PlatformPatterns.get_advanced_patterns()
        self._cache: dict[str, tuple[float, PlatformDetectorOutputs]] = {}  # Cache for results
        self._cache_max_age = 300  # 5 minutes cache expiry

    def _get_cache_key(self, inputs: PlatformDetectorInputs) -> str:
        """Generate a cache key based on the inputs."""
        # Create a hash of the key input parameters
        import hashlib
        key_data = f"{inputs.repository_url}:{inputs.workspace_path}:{hash(tuple(inputs.commit_messages))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cached result is still valid."""
        import time
        return (time.time() - timestamp) < self._cache_max_age

    def _get_cached_result(self, inputs: PlatformDetectorInputs) -> PlatformDetectorOutputs | None:
        """Get cached result if available and valid."""
        cache_key = self._get_cache_key(inputs)
        if cache_key in self._cache:
            timestamp, result = self._cache[cache_key]
            if self._is_cache_valid(timestamp):
                return result
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
        return None

    def _cache_result(self, inputs: PlatformDetectorInputs, result: PlatformDetectorOutputs) -> None:
        """Cache the result for future use."""
        import time
        cache_key = self._get_cache_key(inputs)
        self._cache[cache_key] = (time.time(), result)

    def detect_platform(self, inputs: PlatformDetectorInputs) -> PlatformDetectorOutputs:
        """Main platform detection method.

        Analyzes the repository to detect which rapid prototyping platform was used.
        """
        # Check cache first
        cached_result = self._get_cached_result(inputs)
        if cached_result:
            return cached_result

        # Analyze files for platform signatures
        file_analysis = self._analyze_files(inputs.workspace_path)

        # Analyze package.json if provided
        package_analysis = {}
        if inputs.package_json_content:
            package_analysis = self._analyze_package_json(inputs.package_json_content)

        # Analyze commit messages
        commit_analysis = self._analyze_commit_messages(inputs.commit_messages)

        # Combine all analysis results
        combined_scores = {}
        for platform_name, signatures in self.platform_signatures.items():
            score = self._calculate_platform_score(
                platform_name, signatures, file_analysis, package_analysis, commit_analysis
            )
            if score > 0:
                combined_scores[platform_name] = score

        # Determine the detected platform
        if combined_scores:
            detected_platform = max(combined_scores.items(), key=lambda x: x[1])[0]
            confidence_score = combined_scores[detected_platform]
        else:
            detected_platform = "unknown"
            confidence_score = 0.0

        # Generate platform-specific config and recommendations
        platform_specific_config = self._generate_platform_config(detected_platform)
        recommended_workflow = self._get_recommended_workflow(detected_platform)
        migration_suggestions = self._get_migration_suggestions(detected_platform)
        enhancement_opportunities = self._get_enhancement_opportunities(detected_platform)

        result = PlatformDetectorOutputs(
            detected_platform=detected_platform,
            confidence_score=confidence_score,
            platform_specific_config=platform_specific_config,
            recommended_workflow=recommended_workflow,
            migration_suggestions=migration_suggestions,
            enhancement_opportunities=enhancement_opportunities,
        )

        # Cache the result for future use
        self._cache_result(inputs, result)

        return result

    def _calculate_platform_score(
        self,
        platform_name: str,
        signatures: dict[str, Any],
        file_analysis: dict[str, Any],
        package_analysis: dict[str, Any],
        commit_analysis: dict[str, Any]
    ) -> float:
        """Calculate confidence score for a platform based on various signals."""
        score = 0.0

        # File-based scoring
        files = signatures.get("files", [])
        for file in files:
            if file_analysis.get(file, False):
                score += 0.3

        # Package script scoring
        package_scripts = signatures.get("package_scripts", [])
        for script in package_scripts:
            if package_analysis.get("scripts", {}).get(script):
                score += 0.2

        # Dependency scoring
        dependencies = signatures.get("dependencies", [])
        for dep in dependencies:
            if dep in package_analysis.get("dependencies", []):
                score += 0.25

        # Commit message scoring
        commit_patterns = signatures.get("commit_patterns", [])
        for pattern in commit_patterns:
            if commit_analysis.get(pattern, 0) > 0:
                score += 0.15

        # Content pattern scoring
        content_patterns = signatures.get("content_patterns", [])
        for pattern in content_patterns:
            if file_analysis.get(f"content_{pattern}", 0) > 0:
                score += 0.1

        return min(score, 1.0)  # Cap at 1.0

    def _analyze_files(self, workspace_path: str) -> dict[str, Any]:
        """Analyze files in the workspace for platform signatures."""
        analysis = {}

        try:
            workspace = Path(workspace_path)

            # Check for signature files
            for platform_name, signatures in self.platform_signatures.items():
                files = signatures.get("files", [])
                for file in files:
                    if (workspace / file).exists():
                        analysis[file] = True

            # Check for folder patterns
            for platform_name, signatures in self.platform_signatures.items():
                folder_patterns = signatures.get("folder_patterns", [])
                for pattern in folder_patterns:
                    if (workspace / pattern).exists():
                        analysis[f"folder_{pattern}"] = True

            # Check for content patterns (simplified - in real implementation would scan file contents)
            # For now, just check if README.md exists as a proxy for content analysis
            readme_path = workspace / "README.md"
            if readme_path.exists():
                analysis["readme_exists"] = True

        except Exception as e:
            # Log error but don't fail completely
            analysis["error"] = str(e)

        return analysis

    def _analyze_package_json(self, package_json_content: str | None) -> dict[str, Any]:
        """Analyze package.json content for platform indicators."""
        if not package_json_content:
            return {}

        try:
            import json
            package_data = json.loads(package_json_content)

            analysis = {
                "scripts": package_data.get("scripts", {}),
                "dependencies": list(package_data.get("dependencies", {}).keys()),
                "devDependencies": list(package_data.get("devDependencies", {}).keys()),
            }

            return analysis
        except json.JSONDecodeError:
            return {"error": "Invalid JSON"}

    def _analyze_commit_messages(self, commit_messages: list[str]) -> dict[str, Any]:
        """Analyze commit messages for platform patterns."""
        analysis = {}

        for message in commit_messages:
            message_lower = message.lower()

            # Check against all platform commit patterns
            for platform_name, signatures in self.platform_signatures.items():
                patterns = signatures.get("commit_patterns", [])
                for pattern in patterns:
                    if pattern.lower() in message_lower:
                        analysis[pattern] = analysis.get(pattern, 0) + 1

        return analysis

    def _generate_platform_config(self, platform: str) -> dict[str, Any]:
        """Generate platform-specific configuration."""
        # This would contain platform-specific settings and optimizations
        base_config = {
            "auto_fix": True,
            "max_issues": 100,
            "quality_modes": ["fast", "comprehensive"],
        }

        if platform != "unknown":
            # Add platform-specific optimizations
            base_config.update({
                "platform_optimized_tools": self._get_platform_tools(platform),
                "platform_specific_exclusions": self._get_platform_exclusions(platform),
            })

        return base_config

    def _get_recommended_workflow(self, platform: str) -> str:
        """Get recommended workflow for the platform."""
        workflows = {
            "replit": "replit_development",
            "lovable": "lovable_workflow",
            "bolt": "bolt_workflow",
            "same": "same_workflow",
            "emergent": "emergent_workflow",
            "unknown": "generic_workflow",
        }
        return workflows.get(platform, "generic_workflow")

    def _get_migration_suggestions(self, platform: str) -> list[str]:
        """Get migration suggestions for the platform."""
        if platform == "unknown":
            return ["Analyze repository structure to determine platform", "Check for platform-specific files"]

        suggestions = [
            f"Consider migrating from {platform} to a more standard development workflow",
            "Review platform-specific dependencies and scripts",
        ]

        return suggestions

    def _get_enhancement_opportunities(self, platform: str) -> list[str]:
        """Get enhancement opportunities for the platform."""
        if platform == "unknown":
            return ["Add platform detection capabilities", "Implement comprehensive file analysis"]

        opportunities = [
            f"Optimize quality checks for {platform} ecosystem",
            "Add platform-specific linting rules",
            "Implement platform-aware code generation",
        ]

        return opportunities

    def _get_platform_tools(self, platform: str) -> list[str]:
        """Get tools optimized for the platform."""
        platform_tools = {
            "replit": ["replit-linter", "replit-formatter"],
            "lovable": ["lovable-analyzer", "lovable-optimizer"],
            "bolt": ["bolt-validator", "bolt-enhancer"],
            "same": ["same-checker", "same-improver"],
            "emergent": ["emergent-scanner", "emergent-fixer"],
        }
        return platform_tools.get(platform, ["generic-linter", "generic-formatter"])

    def _get_platform_exclusions(self, platform: str) -> list[str]:
        """Get files/patterns to exclude for the platform."""
        platform_exclusions = {
            "replit": [".replit_modules", "replit.nix"],
            "lovable": [".lovable", "lovable.config.js"],
            "bolt": [".bolt", "bolt.config.json"],
            "same": [".same", "same.config.js"],
            "emergent": ["emergent.sh", ".emergent"],
        }
    async def analyze(
        self,
        repo_path: str,
        file_paths: list[str] | None = None,
        context: dict[str, Any] | None = None
    ) -> PlatformDetectorOutputs:
        """Analyze a repository to detect platforms and technologies.

        Args:
            repo_path: Path to the repository root
            file_paths: Optional list of specific file paths to analyze
            context: Additional context for the analysis

        Returns:
            PlatformDetectorOutputs containing the analysis results
        """
        # Convert to PlatformDetectorInputs format
        inputs = PlatformDetectorInputs(
            repository_url=f"file://{repo_path}",
            workspace_path=repo_path,
            commit_messages=[],  # Would be populated from git history in real implementation
        )

        # Call the synchronous detect_platform method
        result = self.detect_platform(inputs)

        # Convert the result to the expected format
        return PlatformDetectorOutputs(
            primary_platform=result.detected_platform,
            secondary_platforms=[],  # Could be populated with other high-confidence platforms
            confidence_scores={result.detected_platform: result.confidence_score},
            workflow_type=result.recommended_workflow,
            platform_specific_configs={result.detected_platform: result.platform_specific_config},
            recommended_enhancements=result.enhancement_opportunities,
            migration_opportunities=result.migration_suggestions,
            hybrid_workflow_analysis=None,
        )
