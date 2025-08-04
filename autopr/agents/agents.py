"""
Agent definitions for the AutoPR Agent Framework.

This module defines the specialized agents used in the AutoPR code analysis pipeline.
"""
from typing import Dict, Any, List, Optional, Type, TypeVar, Generic
from pathlib import Path
from dataclasses import dataclass

from crewai import Agent
from autopr.actions.llm import get_llm_provider_manager
from autopr.actions.quality_engine import QualityEngine, QualityMode
from autopr.actions.platform_detection import PlatformDetector
from autopr.actions.ai_linting_fixer import AILintingFixer
from autopr.actions.quality_engine.volume_mapping import (
    get_quality_mode_from_volume,
    get_quality_config_from_volume,
    get_volume_level_name
)

from .models import CodeIssue, PlatformAnalysis, CodeAnalysisReport

T = TypeVar('T')

@dataclass
class VolumeConfig:
    """Configuration for volume-based quality control."""
    volume: int = 500  # Default to moderate level
    quality_mode: Optional[QualityMode] = None
    config: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize volume-based configuration."""
        if self.quality_mode is None or self.config is None:
            self.quality_mode = get_quality_mode_from_volume(self.volume)
            self.config = get_quality_config_from_volume(self.volume)


class BaseAgent(Agent):
    """Base agent with common configuration and volume control."""
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        llm_model: str = "gpt-4",
        volume: int = 500,  # Default to moderate level
        **kwargs
    ):
        """Initialize the base agent with common settings.
        
        Args:
            role: The role of the agent
            goal: The goal of the agent
            backstory: The backstory of the agent
            llm_model: The LLM model to use (default: 'gpt-4')
            volume: Volume level (0-1000) controlling quality strictness
            **kwargs: Additional arguments to pass to the base Agent
        """
        llm = get_llm_provider_manager().get_llm(llm_model)
        self.volume = max(0, min(1000, volume))  # Clamp to 0-1000 range
        self.volume_config = VolumeConfig(volume=self.volume)
        
        # Add volume context to the agent's description
        volume_level = get_volume_level_name(self.volume)
        backstory = f"""{backstory}
        
        You are currently operating at volume level {self.volume} ({volume_level}). 
        This affects the strictness of your analysis and the depth of your checks.
        """
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            llm=llm,
            allow_delegation=True,
            **kwargs
        )
        
    def get_volume_context(self) -> Dict[str, Any]:
        """Get context about the current volume level for agent tasks."""
        return {
            "volume": self.volume,
            "volume_level": get_volume_level_name(self.volume),
            "quality_mode": self.volume_config.quality_mode.value if self.volume_config.quality_mode else None,
            "quality_config": self.volume_config.config or {}
        }


class CodeQualityAgent(BaseAgent):
    """Agent responsible for code quality analysis with volume-aware strictness."""
    
    def __init__(self, **kwargs):
        """Initialize the code quality agent with volume control.
        
        Args:
            **kwargs: Additional arguments including 'volume' (0-1000)
        """
        super().__init__(
            role="Senior Code Quality Engineer",
            goal="Analyze and improve code quality through comprehensive checks with configurable strictness",
            backstory="""You are an expert in static code analysis, code smells detection, 
            and quality metrics. You excel at identifying potential issues and suggesting 
            improvements. You have a keen eye for detail and a deep understanding of 
            software engineering best practices.""",
            **kwargs
        )
        self.quality_engine = QualityEngine()
    
    async def analyze_code_quality(self, repo_path: str) -> Dict[str, Any]:
        """Analyze code quality for the given repository."""
        # Delegate to the quality engine
        return await self.quality_engine.analyze_code(repo_path)


class PlatformAnalysisAgent(BaseAgent):
    """Agent responsible for platform and technology stack analysis with volume-aware depth."""
    
    def __init__(self, **kwargs):
        """Initialize the platform analysis agent with volume control.
        
        Args:
            **kwargs: Additional arguments including 'volume' (0-1000)
        """
        super().__init__(
            role="Platform Architecture Specialist",
            goal="Identify and analyze the technology stack and platform architecture with configurable depth",
            backstory="""You have deep knowledge of various technology stacks, frameworks, 
            and platform architectures. You can detect platform-specific patterns and 
            provide optimization recommendations. You understand how different components 
            interact and can identify potential integration issues.
            
            Your analysis depth and thoroughness are adjusted based on the current volume level.""",
            **kwargs
        )
        self.platform_detector = PlatformDetector()
        
        # Configure platform detector based on volume
        if self.volume_config.config and "platform_scan_depth" in self.volume_config.config:
            self.platform_detector.scan_depth = self.volume_config.config["platform_scan_depth"]
    
    async def analyze_platform(self, repo_path: str) -> PlatformAnalysis:
        """Analyze the platform and technology stack."""
        # Delegate to the platform detector
        detection_result = await self.platform_detector.detect_platform(repo_path)
        
        # Convert to our model
        components = [
            PlatformComponent(
                name=comp["name"],
                version=comp.get("version"),
                confidence=comp["confidence"],
                evidence=comp.get("evidence", [])
            )
            for comp in detection_result.get("components", [])
        ]
        
        return PlatformAnalysis(
            platform=detection_result["platform"],
            confidence=detection_result["confidence"],
            components=components,
            recommendations=detection_result.get("recommendations", [])
        )


class LintingAgent(BaseAgent):
    """Agent responsible for code linting and style enforcement with volume-aware strictness."""
    
    def __init__(self, **kwargs):
        """Initialize the linting agent with volume control.
        
        Args:
            **kwargs: Additional arguments including 'volume' (0-1000)
        """
        super().__init__(
            role="Senior Linting Engineer",
            goal="Detect and fix code style and quality issues with configurable strictness",
            backstory="""You are an expert in code style guides, best practices, and 
            automated code quality tools. You help maintain consistent code quality 
            across the codebase. You're meticulous about following style guides and 
            can spot even the most subtle style violations.
            
            Your strictness and thoroughness are adjusted based on the current volume level.""",
            **kwargs
        )
        
        # Configure linting fixer based on volume
        linting_config = {}
        if self.volume_config.config:
            linting_config.update({
                k: v for k, v in self.volume_config.config.items()
                if k.startswith("linting_")
            })
            
        self.linting_fixer = AILintingFixer(**linting_config)
        
        # Adjust verbosity based on volume
        if self.volume_config.quality_mode:
            self.verbose = (self.volume_config.quality_mode != QualityMode.ULTRA_FAST)
    
    async def fix_code_issues(self, file_path: str) -> List[CodeIssue]:
        """Fix code style and quality issues in the specified file."""
        # Delegate to the linting fixer
        fix_results = await self.linting_fixer.fix_issues(file_path)
        
        # Convert to our model
        return [
            CodeIssue(
                file_path=issue["file"],
                line_number=issue["line"],
                column=issue.get("column", 0),
                message=issue["message"],
                severity=issue["severity"],
                rule_id=issue["rule_id"],
                category=issue.get("category", "style"),
                fix=issue.get("fix")
            )
            for issue in fix_results.get("issues", [])
        ]
