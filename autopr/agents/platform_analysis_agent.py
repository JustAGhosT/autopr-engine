"""
Platform Analysis Agent for AutoPR.

This module provides the PlatformAnalysisAgent class which is responsible for
analyzing codebases to detect the underlying platform, frameworks, and technologies.
"""
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from crewai import Agent as CrewAgent

from autopr.agents.base import BaseAgent, VolumeConfig
from autopr.actions.llm import get_llm_provider_manager
from autopr.actions.platform_detection.detector import PlatformDetector, PlatformDetectorOutputs
from autopr.actions.platform_detection.schema import PlatformType, PlatformConfig
from autopr.actions.platform_detection.config import PlatformConfigManager
from pydantic import BaseModel, Field

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
    file_paths: List[str] = None
    context: Dict[str, Any] = None


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
    platforms: List[Tuple[str, float]]  # (platform_name, confidence)
    primary_platform: Tuple[str, float]
    tools: List[str]
    frameworks: List[str]
    languages: List[str]
    config_files: List[str]
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
            primary_confidence = analysis.platforms.get(primary_platform, 0.0)
            
            # Prepare the platforms list with name-confidence pairs
            platforms_list = [(p.name, confidence) 
                            for p, confidence in analysis.platforms.items()]
            
            # Prepare the output with defensive programming
            return PlatformAnalysisOutputs(
                platforms=platforms_list,
                primary_platform=(primary_platform.name, primary_confidence),
                tools=list(analysis.tools) if analysis.tools else [],
                frameworks=list(analysis.frameworks) if analysis.frameworks else [],
                languages=list(analysis.languages) if analysis.languages else [],
                config_files=[str(path) for path in analysis.config_files] if analysis.config_files else [],
                analysis=analysis
            )
            
        except Exception as e:
            # Log the error and return a default response
            if self.verbose:
                print(f"Error in PlatformAnalysisAgent: {str(e)}")
            
            # Create a default analysis with error information
            error_analysis = PlatformAnalysis(
                platforms={PlatformType.UNKNOWN: 1.0},
                tools=set(),
                frameworks=set(),
                languages=set(),
                config_files=[],
                metadata={"error": str(e)}
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
    
    def _get_primary_platform(self, analysis: PlatformDetectorOutputs) -> PlatformType:
        """Get the primary platform from the analysis results.
        
        Args:
            analysis: The platform analysis results
            
        Returns:
            The primary platform type
        """
        if not analysis.platforms:
            return PlatformType.UNKNOWN
        
        # Get the platform with the highest confidence
        return max(analysis.platforms.items(), key=lambda x: x[1])[0]
    
    def _get_platform_info(self, platform_type: PlatformType) -> Optional[Dict[str, Any]]:
        """Get information about a specific platform type.
        
        Args:
            platform_type: The platform type to get information for
            
        Returns:
            Dictionary with details about the platform, or None if not found
        """
        config_manager = PlatformConfigManager()
        platform_config = config_manager.get_platform(platform_type.value)
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
        detection_rules = {}
        if platform_config and hasattr(platform_config, 'detection'):
            detection = platform_config.detection or {}
            detection_rules = {
                'files': detection.get('files', []),
                'dependencies': detection.get('dependencies', []),
                'folder_patterns': detection.get('folder_patterns', []),
                'commit_patterns': detection.get('commit_patterns', []),
                'content_patterns': detection.get('content_patterns', []),
                'package_scripts': detection.get('package_scripts', [])
            }
            
        return {
            'id': platform_config.id,
            'name': platform_config.name,
            'display_name': get_attr(platform_config, 'display_name') or platform_config.name,
            'description': platform_config.description,
            'type': get_enum_value(get_attr(platform_config, 'type')),
            'category': get_enum_value(get_attr(platform_config, 'category')),
            'subcategory': get_attr(platform_config, 'subcategory'),
            'tags': get_attr(platform_config, 'tags', []),
            'status': get_enum_value(get_attr(platform_config, 'status')),
            'documentation_url': get_attr(platform_config, 'documentation_url'),
            'is_active': get_attr(platform_config, 'is_active', True),
            'is_beta': get_attr(platform_config, 'is_beta', False),
            'is_deprecated': get_attr(platform_config, 'is_deprecated', False),
            'version': get_attr(platform_config, 'version'),
            'last_updated': get_attr(platform_config, 'last_updated'),
            'supported_languages': get_attr(platform_config, 'supported_languages', []),
            'supported_frameworks': get_attr(platform_config, 'supported_frameworks', []),
            'integrations': get_attr(platform_config, 'integrations', []),
            'detection_rules': detection_rules,
            'project_config': get_attr(platform_config, 'project_config', {})
        }
    
    def get_supported_platforms(self) -> List[dict]:
        """Get a list of all supported platforms.
        
        Returns:
            List of dictionaries with platform information for all supported platforms
        """
        return [
            platform_info
            for platform_type in PlatformType
            if (platform_info := self._get_platform_info(platform_type)) is not None
        ]
