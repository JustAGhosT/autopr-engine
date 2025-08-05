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
from autopr.actions.platform_detection.detector import PlatformDetector
from autopr.actions.platform_detection.models import PlatformAnalysis, PlatformType, PlatformInfo


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
    analysis: PlatformAnalysis


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
                repo_path=repo_path,
                file_paths=file_paths,
                context=inputs.context or {}
            )
            
            # Extract the primary platform
            primary_platform = self._get_primary_platform(analysis)
            
            # Prepare the output
            return PlatformAnalysisOutputs(
                platforms=[(p.name, c) for p, c in analysis.platforms],
                primary_platform=(primary_platform.name, analysis.platforms[primary_platform]),
                tools=list(analysis.tools),
                frameworks=list(analysis.frameworks),
                languages=list(analysis.languages),
                config_files=[str(path) for path in analysis.config_files],
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
    
    def _get_primary_platform(self, analysis: PlatformAnalysis) -> PlatformType:
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
    
    def _get_platform_info(self, platform_type: PlatformType) -> Optional[PlatformInfo]:
        """Get information about a specific platform type.
        
        Args:
            platform_type: The platform type to get information for
            
        Returns:
            PlatformInfo object with details about the platform, or None if not found
        """
        return self.detector.get_platform_info(platform_type)
    
    def get_supported_platforms(self) -> List[PlatformInfo]:
        """Get a list of all supported platforms.
        
        Returns:
            A list of PlatformInfo objects for all supported platforms
        """
        return self.detector.get_supported_platforms()
