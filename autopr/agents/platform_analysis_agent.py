"""
Platform Analysis Agent for AutoPR.

This module provides the PlatformAnalysisAgent class which is responsible for
analyzing codebases to detect the underlying platform, frameworks, and technologies.
"""
from typing import Any, Optional
from dataclasses import dataclass
from pathlib import Path

from autopr.agents.base import BaseAgent
from autopr.actions.platform_detection.detector import (
    PlatformDetector,
    PlatformDetectorOutputs,
)
from autopr.actions.platform_detection.schema import PlatformType
from autopr.actions.platform_detection.config import PlatformConfigManager

# PlatformAnalysis is now imported from platform_detection.detector as PlatformDetectorOutputs


@dataclass
class PlatformAnalysisInputs:
    """Inputs for the PlatformAnalysisAgent.

    Attributes:
        repo_path: Path to the repository root
        file_paths: List of file paths to analyze (relative to repo_path)
        context: Additional context for the analysis
    """
    repo_path: str
    file_paths: list[str] | None = None
    context: dict[str, Any] | None = None


@dataclass
class PlatformAnalysisOutputs:
    """Outputs from the PlatformAnalysisAgent.

    Attributes:
        platforms: List of detected platforms with confidence scores
        primary_platform: The primary platform with highest confidence
        tools: List of detected development tools
        frameworks: List of detected frameworks
        languages: List of detected programming languages
        config_files: List of detected configuration files
        analysis: The raw PlatformAnalysis object
    """
    platforms: list[tuple[str, float]]  # (platform_name, confidence)
    primary_platform: tuple[str, float]
    tools: list[str]
    frameworks: list[str]
    languages: list[str]
    config_files: list[str]
    analysis: PlatformDetectorOutputs


class PlatformAnalysisAgent(BaseAgent[PlatformAnalysisInputs, PlatformAnalysisOutputs]):
    """Agent for analyzing codebases to detect platforms and technologies.

    This agent analyzes a codebase to detect the underlying platform, frameworks,
    and technologies being used. It uses a combination of file pattern matching
    and LLM-based analysis to provide accurate detection.
    """

    def __init__(
        self,
        volume: int = 500,  # Default to moderate level (500/1000)
        *,
        verbose: bool = False,
        allow_delegation: bool = False,
        max_iter: int = 3,
        max_rpm: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        """Initialize the PlatformAnalysisAgent.

        Args:
            volume: Volume level (0-1000) for analysis depth
            verbose: Whether to enable verbose logging
            allow_delegation: Whether to allow task delegation
            max_iter: Maximum number of iterations for the agent
            max_rpm: Maximum requests per minute for the agent
            **kwargs: Additional keyword arguments passed to the base class
        """
        super().__init__(
            name="Platform Analyst",
            role="Analyze codebases to detect platforms, frameworks, and technologies.",
            backstory=(
                "You are an expert in software platforms and frameworks with a keen eye "
                "for identifying technologies from code patterns, file structures, and "
                "configuration files. Your goal is to accurately detect the underlying "
                "platform and technologies used in a codebase to enable better tooling "
                "and automation."
            ),
            volume=volume,
            verbose=verbose,
            allow_delegation=allow_delegation,
            max_iter=max_iter,
            max_rpm=max_rpm,
            **kwargs
        )

        # Initialize the platform detector
        self.detector = PlatformDetector()

    async def _execute(self, inputs: PlatformAnalysisInputs) -> PlatformAnalysisOutputs:
        """Analyze a codebase to detect platforms and technologies.

        Args:
            inputs: The input data for the agent

        Returns:
            PlatformAnalysisOutputs containing the analysis results
        """
        try:
            # Convert repo_path to Path object
            repo_path = Path(inputs.repo_path)

            # If no specific file paths provided, analyze the entire repository
            if not inputs.file_paths:
                file_paths = None
            else:
                file_paths = [repo_path / path for path in inputs.file_paths]

            # Perform the platform analysis
            analysis = await self.detector.analyze(
                repo_path=str(repo_path),
                file_paths=[str(p) for p in file_paths] if file_paths else None,
                context=inputs.context or {}
            )

            # Extract the primary platform safely
            primary_platform = self._get_primary_platform(analysis)

            # Safely get the primary platform's confidence score
            primary_confidence = analysis.confidence_scores.get(primary_platform, 0.0)

            # Prepare the platforms list with name-confidence pairs
            platforms_list = [
                (platform_name, confidence)
                for platform_name, confidence in analysis.confidence_scores.items()
            ]

            # Aggregate config files from platform-specific configs
            config_files: list[str] = []
            for cfg in analysis.platform_specific_configs.values():
                files = cfg.get("config_files", [])
                if isinstance(files, list):
                    config_files.extend(str(f) for f in files)
            # De-duplicate while preserving order
            seen: set[str] = set()
            unique_config_files: list[str] = []
            for f in config_files:
                if f not in seen:
                    unique_config_files.append(f)
                    seen.add(f)

            # Prepare the output with defensive programming
            return PlatformAnalysisOutputs(
                platforms=platforms_list,
                primary_platform=(primary_platform, primary_confidence),
                tools=[],
                frameworks=[],
                languages=[],
                config_files=unique_config_files,
                analysis=analysis
            )

        except Exception:
            # Log the error and return a default response
            # Prefer logging in real code; keeping minimal message only if verbose is set
            _ = self.verbose

            # Create a default analysis with error information
            error_analysis = PlatformDetectorOutputs(
                primary_platform=PlatformType.UNKNOWN.value,
                secondary_platforms=[],
                confidence_scores={PlatformType.UNKNOWN.value: 1.0},
                workflow_type="unknown",
                platform_specific_configs={},
                recommended_enhancements=[],
                migration_opportunities=[],
                hybrid_workflow_analysis=None,
            )

            return PlatformAnalysisOutputs(
                platforms=[("unknown", 1.0)],
                primary_platform=("unknown", 1.0),
                tools=[],
                frameworks=[],
                languages=[],
                config_files=[],
                analysis=error_analysis
            )

    def _get_primary_platform(self, analysis: PlatformDetectorOutputs) -> str:
        """Get the primary platform from the analysis results.

        Args:
            analysis: The platform analysis results

        Returns:
            The primary platform identifier as a string
        """
        if analysis.primary_platform:
            return analysis.primary_platform
        # Fallback to max confidence if primary not set
        if analysis.confidence_scores:
            return max(analysis.confidence_scores.items(), key=lambda x: x[1])[0]
        return PlatformType.UNKNOWN.value

    def _get_platform_info(self, platform_id: str) -> Optional[dict[str, Any]]:
        """Get information about a specific platform by ID.

        Args:
            platform_id: The platform ID to get information for

        Returns:
            Dictionary with details about the platform, or None if not found
        """
        config_manager = PlatformConfigManager()
        platform_config = config_manager.get_platform(platform_id)
        if not platform_config:
            return None

        # Safely get enum values with fallback to string representation
        def get_enum_value(enum_obj):
            if enum_obj is None:
                return None
            if hasattr(enum_obj, 'value'):
                return enum_obj.value
            return str(enum_obj)

        # Safely get attributes with defaults
        def get_attr(obj, attr, default=None):
            return getattr(obj, attr, default) if hasattr(obj, attr) else default

        # Safely get detection rules with defaults
        detection_rules: dict[str, list[str]] = {}
        if platform_config and 'detection' in platform_config:
            detection = platform_config.get('detection') or {}
            detection_rules = {
                'files': detection.get('files', []),
                'dependencies': detection.get('dependencies', []),
                'folder_patterns': detection.get('folder_patterns', []),
                'commit_patterns': detection.get('commit_patterns', []),
                'content_patterns': detection.get('content_patterns', []),
                'package_scripts': detection.get('package_scripts', [])
            }

        return {
            'id': platform_config.get('id'),
            'name': platform_config.get('name'),
            'display_name': platform_config.get('name'),
            'description': platform_config.get('description'),
            'type': None,
            'category': platform_config.get('category'),
            'subcategory': None,
            'tags': [],
            'status': None,
            'documentation_url': None,
            'is_active': platform_config.get('is_active', True),
            'is_beta': False,
            'is_deprecated': False,
            'version': None,
            'last_updated': None,
            'supported_languages': [],
            'supported_frameworks': [],
            'integrations': [],
            'detection_rules': detection_rules,
            'project_config': platform_config.get('project_config', {})
        }

    def get_supported_platforms(self) -> list[dict]:
        """Get a list of all supported platforms.

        Returns:
            List of dictionaries with platform information for all supported platforms
        """
        config_manager = PlatformConfigManager()
        all_platforms = config_manager.get_all_platforms()
        results: list[dict] = []
        for platform_id in all_platforms.keys():
            info = self._get_platform_info(platform_id)
            if info is not None:
                results.append(info)
        return results
