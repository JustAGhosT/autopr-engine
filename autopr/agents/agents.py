"""
Agent definitions for the AutoPR Agent Framework.

This module defines the specialized agents used in the AutoPR code analysis pipeline.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path

from crewai import Agent
from autopr.actions.llm import get_llm_provider_manager
from autopr.actions.quality_engine import QualityEngine
from autopr.actions.platform_detection import PlatformDetector
from autopr.actions.ai_linting_fixer import AILintingFixer

from .models import CodeIssue, PlatformAnalysis, CodeAnalysisReport


class BaseAgent(Agent):
    """Base agent with common configuration."""
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        llm_model: str = "gpt-4",
        **kwargs
    ):
        """Initialize the base agent with common settings."""
        llm = get_llm_provider_manager().get_llm(llm_model)
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            llm=llm,
            allow_delegation=True,
            **kwargs
        )


class CodeQualityAgent(BaseAgent):
    """Agent responsible for code quality analysis."""
    
    def __init__(self, **kwargs):
        """Initialize the code quality agent."""
        super().__init__(
            role="Senior Code Quality Engineer",
            goal="Analyze and improve code quality through comprehensive checks",
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
    """Agent responsible for platform and technology stack analysis."""
    
    def __init__(self, **kwargs):
        """Initialize the platform analysis agent."""
        super().__init__(
            role="Platform Architecture Specialist",
            goal="Identify and analyze the technology stack and platform architecture",
            backstory="""You have deep knowledge of various technology stacks, frameworks, 
            and platform architectures. You can detect platform-specific patterns and 
            provide optimization recommendations. You understand how different components 
            interact and can identify potential integration issues.""",
            **kwargs
        )
        self.platform_detector = PlatformDetector()
    
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
    """Agent responsible for code linting and style enforcement."""
    
    def __init__(self, **kwargs):
        """Initialize the linting agent."""
        super().__init__(
            role="Senior Linting Engineer",
            goal="Detect and fix code style and quality issues",
            backstory="""You are an expert in code style guides, best practices, and 
            automated code quality tools. You help maintain consistent code quality 
            across the codebase. You're meticulous about following style guides and 
            can spot even the most subtle style violations.""",
            **kwargs
        )
        self.linting_fixer = AILintingFixer()
    
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
