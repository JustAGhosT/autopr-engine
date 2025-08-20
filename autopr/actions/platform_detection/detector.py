"""
Platform Detector - Refactored Main Module

Orchestrates platform detection using modular components for better maintainability.
"""

import re
from typing import Any

from autopr.actions.platform_detection.config import PlatformConfigManager
from autopr.actions.platform_detection.file_analyzer import FileAnalyzer
from autopr.actions.platform_detection.inputs import (
    PlatformDetectorInputs,
    PlatformDetectorOutputs,
)


__all__ = ["PlatformDetector", "PlatformDetectorInputs", "PlatformDetectorOutputs"]
from autopr.actions.platform_detection.scoring import PlatformScoringEngine


class PlatformDetector:
    """Platform detector with modular architecture."""

    def __init__(self) -> None:
        self.config = PlatformConfigManager()
        self.scoring_engine = PlatformScoringEngine()

    async def run(self, inputs: PlatformDetectorInputs) -> PlatformDetectorOutputs:
        """Main detection workflow."""
        # Initialize file analyzer
        file_analyzer = FileAnalyzer(inputs.workspace_path)

        # Get platform configurations
        platform_configs = self.config.get_all_platforms()

        # Perform detection analysis
        detection_results = await self._perform_detection_analysis(
            file_analyzer, platform_configs, inputs
        )

        # Calculate confidence scores
        confidence_scores = self.scoring_engine.calculate_platform_scores(
            platform_configs, detection_results
        )

        # Rank platforms
        primary_platform, secondary_platforms = self.scoring_engine.rank_platforms(
            confidence_scores
        )

        # Determine workflow type
        workflow_type = self.scoring_engine.determine_workflow_type(confidence_scores)

        # Generate recommendations
        recommendations = self.scoring_engine.generate_recommendations(
            primary_platform, secondary_platforms, confidence_scores, workflow_type
        )

        # Identify migration opportunities
        migration_opportunities = self.scoring_engine.identify_migration_opportunities(
            confidence_scores, platform_configs
        )

        # Analyze hybrid workflows if applicable
        hybrid_analysis = None
        if workflow_type in {"hybrid_workflow", "multi_platform"}:
            hybrid_analysis = self.scoring_engine.analyze_hybrid_workflow(
                confidence_scores, platform_configs
            )

        # Extract platform-specific configurations
        platform_specific_configs = self._extract_platform_configs(
            primary_platform, secondary_platforms, detection_results
        )

        return PlatformDetectorOutputs(
            primary_platform=primary_platform,
            secondary_platforms=secondary_platforms,
            confidence_scores=confidence_scores,
            workflow_type=workflow_type,
            platform_specific_configs=platform_specific_configs,
            recommended_enhancements=recommendations,
            migration_opportunities=migration_opportunities,
            hybrid_workflow_analysis=hybrid_analysis,
        )

    # Compatibility shim for older call sites/tests expecting 'analyze' with repo_path
    async def analyze(
        self,
        repo_path: str,
        file_paths: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> PlatformDetectorOutputs:
        """Analyze repository path by building inputs and delegating to run().
        This method preserves compatibility with tests that call detector.analyze(repo_path).
        """
        inputs = PlatformDetectorInputs(
            repository_url="",
            commit_messages=context.get("commit_messages", []) if context else [],
            workspace_path=repo_path,
            package_json_content=None,
            git_log_depth=50,
        )
        return await self.run(inputs)

    async def _perform_detection_analysis(
        self,
        file_analyzer: FileAnalyzer,
        platform_configs: dict[str, dict[str, Any]],
        inputs: PlatformDetectorInputs,
    ) -> dict[str, Any]:
        """Perform comprehensive detection analysis."""

        # File-based detection
        found_files = file_analyzer.scan_for_platform_files(platform_configs)
        found_folders = file_analyzer.scan_for_folder_patterns(platform_configs)

        # Package analysis
        package_data = file_analyzer.analyze_package_json()
        python_deps = file_analyzer.analyze_requirements_txt()
        docker_analysis = file_analyzer.analyze_dockerfile()

        # Content pattern scanning
        content_matches = file_analyzer.scan_content_for_patterns(platform_configs)

        # Commit message analysis
        commit_matches = self._analyze_commit_messages(inputs.commit_messages, platform_configs)

        # Combine all dependencies
        all_dependencies = []
        all_dependencies.extend(python_deps)
        all_dependencies.extend(list(package_data.get("dependencies", {}).keys()))
        all_dependencies.extend(list(package_data.get("devDependencies", {}).keys()))

        return {
            "found_files": found_files,
            "found_folders": found_folders,
            "dependencies": all_dependencies,
            "scripts": package_data.get("scripts", {}),
            "content_matches": content_matches,
            "commit_matches": commit_matches,
            "package_data": package_data,
            "python_deps": python_deps,
            "docker_analysis": docker_analysis,
        }

    def _analyze_commit_messages(
        self, commit_messages: list[str], platform_configs: dict[str, dict[str, Any]]
    ) -> dict[str, int]:
        """Analyze commit messages for platform indicators."""
        commit_matches = {}

        for platform, config in platform_configs.items():
            match_count = 0
            patterns = config.get("commit_patterns", [])

            for message in commit_messages:
                for pattern in patterns:
                    if re.search(pattern, message, re.IGNORECASE):
                        match_count += 1

            if match_count > 0:
                commit_matches[platform] = match_count

        return commit_matches

    def _extract_platform_configs(
        self,
        primary_platform: str,
        secondary_platforms: list[str],
        detection_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract platform-specific configuration details."""
        configs = {}

        all_platforms = [primary_platform, *secondary_platforms]

        for platform in all_platforms:
            platform_config = {}

            # Add found files
            if platform in detection_results.get("found_files", {}):
                platform_config["config_files"] = detection_results["found_files"][platform]

            # Add found folders
            if platform in detection_results.get("found_folders", {}):
                platform_config["platform_folders"] = detection_results["found_folders"][platform]

            # Add relevant dependencies
            platform_deps = []
            all_deps = detection_results.get("dependencies", [])
            platform_patterns = (
                self.config.get_all_platforms().get(platform, {}).get("dependencies", [])
            )

            for dep in all_deps:
                platform_deps.extend(dep for pattern in platform_patterns if pattern in dep)

            if platform_deps:
                platform_config["dependencies"] = platform_deps

            # Add relevant scripts
            platform_scripts = {}
            all_scripts = detection_results.get("scripts", {})
            script_patterns = (
                self.config.get_all_platforms().get(platform, {}).get("package_scripts", [])
            )

            for script_name, script_value in all_scripts.items():
                for pattern in script_patterns:
                    if pattern in script_name or pattern in script_value:
                        platform_scripts[script_name] = script_value

            if platform_scripts:
                platform_config["scripts"] = platform_scripts

            if platform_config:
                configs[platform] = platform_config

        return configs

    # Compatibility shim for very old usage expecting synchronous detect_platform()
    def detect_platform(self, repo_path: str) -> dict[str, Any]:
        """Synchronous compatibility method returning a minimal dict.

        Legacy code/tests may expect a quick detection dictionary.
        We map our structured outputs into a simple dict.
        """
        import asyncio

        async def _run() -> PlatformDetectorOutputs:
            return await self.analyze(repo_path)

        outputs = asyncio.get_event_loop().run_until_complete(_run())

        # Convert to minimal legacy dict
        primary = outputs.primary_platform
        score = outputs.confidence_scores.get(primary, 0.0)
        return {
            "platform": primary,
            "confidence": score,
            "components": [],
            "recommendations": outputs.recommended_enhancements,
        }
