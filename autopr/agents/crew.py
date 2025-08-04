"""
Crew orchestration for the AutoPR Agent Framework.

This module defines the main crew that coordinates the code analysis agents.
"""
import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, cast

from crewai import Crew, Process, Task
from autopr.actions.llm import get_llm_provider_manager
from autopr.actions.quality_engine import QualityEngine
from autopr.actions.quality_engine.models import QualityMode, QualityInputs
from autopr.actions.quality_engine.volume_mapping import (
    get_volume_config,
    get_quality_mode_from_volume,
    get_quality_config_from_volume,
    get_volume_level_name
)

from .models import (
    CodeIssue,
    PlatformAnalysis,
    CodeAnalysisReport,
    PlatformComponent
)
from .agents import (
    CodeQualityAgent,
    PlatformAnalysisAgent,
    LintingAgent
)

# Set up logging
logger = logging.getLogger(__name__)


class AutoPRCrew:
    """Main crew for orchestrating code analysis agents."""
    
    def __init__(
        self, 
        llm_model: str = "gpt-4",
        volume: int = 500,  # Default to moderate volume (500/1000)
        **kwargs
    ):
        """Initialize the AutoPR crew with specialized agents.
        
        Args:
            llm_model: The LLM model to use for all agents
            volume: Volume level (0-1000) controlling quality strictness and verbosity
            **kwargs: Additional arguments passed to agent constructors
        """
        self.llm_model = llm_model
        self.volume = max(0, min(1000, volume))  # Clamp to 0-1000 range
        self.llm_provider = get_llm_provider_manager()
        
        # Get volume-based configuration
        self.volume_config = get_volume_config(self.volume)
        logger.info(
            f"Initializing AutoPRCrew with volume={self.volume} "
            f"(mode={self.volume_config['mode'].name})"
        )
        
        # Initialize agents with volume context
        agent_kwargs = {
            **kwargs,
            "volume": self.volume,
            "llm_model": llm_model
        }
        
        self.code_quality_agent = CodeQualityAgent(**agent_kwargs)
        self.platform_agent = PlatformAnalysisAgent(**agent_kwargs)
        self.linting_agent = LintingAgent(**agent_kwargs)
        
        # Initialize the crew with volume context
        self.crew = Crew(
            agents=[
                self.code_quality_agent,
                self.platform_agent,
                self.linting_agent
            ],
            process=Process.hierarchical,
            manager_llm=self.llm_provider.get_llm(llm_model),
            verbose=self.volume > 500,  # More verbose at higher volumes
            **kwargs
        )
    
    def _get_volume_context(self, volume_override: Optional[int] = None) -> Dict[str, Any]:
        """Get context about the current volume level for tasks.
        
        Args:
            volume_override: Optional volume level (0-1000) to override instance volume
            
        Returns:
            Dict containing volume context information
        """
        volume = volume_override if volume_override is not None else self.volume
        quality_mode = get_quality_mode_from_volume(volume)
        config = get_quality_config_from_volume(volume)
        
        return {
            "volume": volume,
            "volume_level": get_volume_level_name(volume),
            "quality_mode": quality_mode.value,
            "quality_config": config
        }
        
    def _create_quality_inputs(self, volume: int) -> QualityInputs:
        """Create QualityInputs with volume-based configuration.
        
        Args:
            volume: Volume level (0-1000)
            
        Returns:
            QualityInputs configured according to volume settings
        """
        quality_mode = get_quality_mode_from_volume(volume)
        config = get_quality_config_from_volume(volume)
        
        # Create base inputs with volume-based mode
        inputs = QualityInputs(
            mode=quality_mode,
            max_fixes=config.get("max_fixes", 50),
            max_issues=config.get("max_issues", 100),
            enable_ai=config.get("enable_ai", True),
            volume=volume
        )
        
        # Apply any additional volume-based configuration
        if "quality_overrides" in config:
            for key, value in config["quality_overrides"].items():
                if hasattr(inputs, key):
                    setattr(inputs, key, value)
                    
        return inputs

    async def analyze_repository(
        self, 
        repo_path: Union[str, Path],
        volume: Optional[int] = None,
        **analysis_kwargs
    ) -> CodeAnalysisReport:
        """
        Run a full analysis of the repository with volume-based quality control.
        
        Args:
            repo_path: Path to the repository to analyze
            volume: Optional volume level (0-1000) to override instance volume
            **analysis_kwargs: Additional arguments to pass to analysis tasks
            
        Returns:
            CodeAnalysisReport: Comprehensive analysis report
            
        Raises:
            ValueError: If volume is outside 0-1000 range
        """
        if isinstance(repo_path, str):
            repo_path = Path(repo_path)
            
        # Use instance volume if not overridden
        current_volume = volume if volume is not None else self.volume
        current_volume = max(0, min(1000, current_volume))  # Ensure in range
        
        # Get volume context and quality inputs
        volume_context = self._get_volume_context(current_volume)
        quality_inputs = self._create_quality_inputs(current_volume)
        
        logger.info(
            f"Starting repository analysis with volume={current_volume} "
            f"(mode={quality_inputs.mode.value})"
        )
        
        # Create context with volume information
        context = {
            "repo_path": str(repo_path.absolute()),
            "volume": current_volume,
            "volume_context": volume_context,
            "quality_inputs": quality_inputs.dict(),
            **analysis_kwargs
        }
        
        # Create tasks for each analysis type with volume context
        tasks = [
            self._create_code_quality_task(repo_path, context),
            self._create_platform_analysis_task(repo_path, context),
            self._create_linting_task(repo_path, context)
        ]
        
        # Execute tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        code_quality = {}
        platform_analysis = None
        linting_issues = []
        
        for result in results:
            if isinstance(result, Exception):
                # Log the error but continue with other results
                print(f"Error during analysis: {result}")
                continue
                
            if isinstance(result, dict) and "metrics" in result:
                code_quality = result
            elif isinstance(result, PlatformAnalysis):
                platform_analysis = result
            elif isinstance(result, list) and all(isinstance(x, CodeIssue) for x in result):
                linting_issues = result
        
        # Generate a summary
        summary = self._generate_summary(code_quality, platform_analysis, linting_issues)
        
        # Create the final report
        return CodeAnalysisReport(
            issues=linting_issues,
            metrics=code_quality.get("metrics", {}),
            summary=summary,
            platform_analysis=platform_analysis or PlatformAnalysis(
                platform="unknown",
                confidence=0.0,
                components=[],
                recommendations=[]
            )
        )
    
    def _create_code_quality_task(
        self, 
        repo_path: Path, 
        context: Dict[str, Any]
    ) -> Task:
        """Create a task for code quality analysis with volume-based configuration.
        
        Args:
            repo_path: Path to the repository to analyze
            context: Context dictionary containing volume and other settings
            
        Returns:
            Task: Configured task for code quality analysis
        """
        volume = context.get("volume", 500)
        volume_context = context.get("volume_context", {})
        quality_inputs = context.get("quality_inputs", {})
        
        # Adjust analysis depth based on volume
        analysis_depth = "thorough" if volume > 700 else "standard" if volume > 300 else "quick"
        detail_level = "exhaustive" if volume > 800 else "detailed" if volume > 500 else "focused"
        
        return Task(
            description=f"""Analyze the codebase at {repo_path} for quality issues with the following parameters:
            
            Volume Context:
            - Level: {volume_context.get('volume_level', 'Moderate')} ({volume}/1000)
            - Quality Mode: {quality_inputs.get('mode', 'smart')}
            - Max Issues: {quality_inputs.get('max_issues', 100)}
            - Enable AI: {quality_inputs.get('enable_ai', True)}
            
            Analysis Guidelines:
            - Perform a {analysis_depth} analysis of the codebase
            - Focus on {detail_level} examination of code quality
            - Prioritize critical and high-impact issues
            - Include specific code examples and improvement suggestions
            - Adjust depth based on volume level (current: {volume}/1000)
            
            Areas to analyze:
            - Code smells and anti-patterns
            - Performance bottlenecks
            - Security vulnerabilities
            - Test coverage gaps
            - Documentation quality
            - Error handling patterns
            - Code organization and modularity""",
            agent=self.code_quality_agent,
            expected_output=(
                f"A {detail_level} code quality report with identified issues, "
                f"severity levels, and recommended fixes. Analysis performed at "
                f"volume level {volume} ({analysis_depth} depth)."
            ),
            output_json=dict,
            context=context
        )
    
    def _create_platform_analysis_task(
        self, 
        repo_path: Path, 
        context: Dict[str, Any]
    ) -> Task:
        """Create a task for platform and technology stack analysis with volume-based configuration.
        
        Args:
            repo_path: Path to the repository to analyze
            context: Context dictionary containing volume and other settings
            
        Returns:
            Task: Configured task for platform analysis
        """
        volume = context.get("volume", 500)
        volume_context = context.get("volume_context", {})
        quality_inputs = context.get("quality_inputs", {})
        
        # Adjust analysis depth based on volume
        analysis_depth = "deep" if volume > 700 else "moderate" if volume > 300 else "light"
        include_deps = volume > 200  # Only include dependency analysis at higher volumes
        
        return Task(
            description=f"""Analyze the technology stack and platform architecture of the repository at {repo_path}.
            
            Volume Context:
            - Level: {volume_context.get('volume_level', 'Moderate')} ({volume}/1000)
            - Quality Mode: {quality_inputs.get('mode', 'smart')}
            - Analysis Depth: {analysis_depth}
            - Dependency Analysis: {'Enabled' if include_deps else 'Basic only'}
            
            Analysis Guidelines:
            - Perform a {analysis_depth} analysis of the technology stack
            - Identify core frameworks, libraries, and architectural patterns
            - Analyze dependencies {'in detail' if include_deps else 'at a high level'}
            - Look for version mismatches and potential security issues
            - Provide optimization and modernization recommendations
            - Include specific examples and migration paths where applicable
            - Adjust depth based on volume level (current: {volume}/1000)
            
            Focus areas:
            - Framework and library identification
            - Architectural patterns and design decisions
            - Performance characteristics and bottlenecks
            - Security considerations and vulnerabilities
            - Modernization opportunities
            - Integration points and dependencies""",
            agent=self.platform_agent,
            expected_output=(
                f"A {analysis_depth} platform analysis report with technology stack, "
                f"architecture assessment, and recommendations. Analysis performed at "
                f"volume level {volume}."
            ),
            output_json=PlatformAnalysis.schema(),
            context={
                **context,
                "include_dependency_analysis": include_deps
            }
        )
    
    def _create_linting_task(
        self, 
        repo_path: Path, 
        context: Dict[str, Any]
    ) -> Task:
        """Create a task for code linting and style enforcement with volume-based configuration.
        
        Args:
            repo_path: Path to the repository to analyze
            context: Context dictionary containing volume and other settings
            
        Returns:
            Task: Configured task for linting
        """
        volume = context.get("volume", 500)
        volume_context = context.get("volume_context", {})
        quality_inputs = context.get("quality_inputs", {})
        
        # Adjust linting strictness based on volume
        strictness = "strict" if volume > 700 else "moderate" if volume > 300 else "relaxed"
        auto_fix = volume > 500  # Enable auto-fixes at higher volumes
        
        return Task(
            description=f"""Perform static code analysis on the repository at {repo_path}.
            
            Volume Context:
            - Level: {volume_context.get('volume_level', 'Moderate')} ({volume}/1000)
            - Quality Mode: {quality_inputs.get('mode', 'smart')}
            - Max Fixes: {quality_inputs.get('max_fixes', 50)}
            - Auto-fix: {'Enabled' if auto_fix else 'Disabled'}
            
            Linting Guidelines:
            - Apply {strictness} linting rules
            - Focus on critical and high-priority issues
            - Include detailed explanations for each finding
            - Provide specific code suggestions for fixes
            - Consider project context and patterns
            - Adjust strictness based on volume level (current: {volume}/1000)
            
            Focus areas:
            - Code style consistency and best practices
            - Potential bugs and anti-patterns
            - Documentation completeness and quality
            - Security best practices and vulnerabilities
            - Performance optimizations and inefficiencies
            - Error handling and edge cases""",
            agent=self.linting_agent,
            expected_output=(
                f"A comprehensive linting report with {strictness} enforcement, "
                f"including found issues, severity levels, and suggested fixes. "
                f"Analysis performed at volume level {volume}."
            ),
            output_json=List[CodeIssue].__annotations__,
            context={
                **context,
                "auto_fix": auto_fix,
                "strictness": strictness
            }
        )
    
    def _generate_summary(
        self,
        code_quality: Dict[str, Any],
        platform_analysis: Optional[PlatformAnalysis],
        linting_issues: List[CodeIssue],
        volume: Optional[int] = None
    ) -> CodeAnalysisReport:
        """Generate a summary report from analysis results with volume-based detail.
        
        Args:
            code_quality: Results from code quality analysis
            platform_analysis: Results from platform analysis
            linting_issues: List of linting issues found
            volume: Volume level (0-1000) to adjust summary detail
            
        Returns:
            CodeAnalysisReport: Consolidated analysis report
        """
        volume = volume if volume is not None else self.volume
        volume = max(0, min(1000, volume))  # Ensure in range
        
        # Adjust detail level based on volume
        detail_level = "high" if volume > 700 else "medium" if volume > 300 else "low"
        
        # Generate summary with appropriate detail level
        summary = f"""# Code Analysis Summary
        
## Code Quality
{code_quality.get('summary', 'No code quality issues found.')}

## Platform Analysis
{platform_analysis.summary if platform_analysis else 'No platform analysis available.'}

## Linting Issues
{f'Found {len(linting_issues)} linting issues.' if linting_issues else 'No linting issues found.'}

Detail level: {detail_level} (volume: {volume}/1000)
"""
        
        # Platform analysis summary
        if platform_analysis:
            summary_parts.append(
                f"\nPlatform Analysis:\n" + "-"*30 +
                f"\n- Detected platform: {platform_analysis.platform} "
                f"(confidence: {platform_analysis.confidence*100:.1f}%)"
                f"\n- Components detected: {len(platform_analysis.components)}"
            )
            
            # Include top components at higher volumes
            if volume > 400 and platform_analysis.components:
                top_components = sorted(
                    platform_analysis.components,
                    key=lambda x: x.confidence,
                    reverse=True
                )[:3]  # Show top 3 components
                
                summary_parts.append("\n  Top components:")
                for comp in top_components:
                    ver = f" v{comp.version}" if comp.version else ""
                    summary_parts.append(
                        f"  - {comp.name}{ver} "
                        f"({comp.confidence*100:.0f}% confidence)"
                    )
        
        # Linting summary
        if linting_issues:
            severity_counts = self._count_issues_by_severity(linting_issues)
            total_issues = len(linting_issues)
            
            summary_parts.append(
                f"\nLinting Results:\n" + "-"*30 +
                f"\n- Total issues found: {total_issues}"
                f"\n- By severity: {severity_counts}"
            )
            
            # Include fixable issues at medium volumes
            if volume > 300:
                fixable = sum(1 for issue in linting_issues if issue.fix is not None)
                if fixable > 0:
                    summary_parts.append(f"- Fixable issues: {fixable} ({(fixable/total_issues):.0%})")
        
        # Add volume-specific recommendations
        if volume < 300:
            summary_parts.append(
                "\nRecommendations:"
                "\n- For more thorough analysis, increase the volume level"
            )
        elif volume > 700 and linting_issues:
            summary_parts.append(
                "\nRecommendations:"
                "\n- Consider addressing the high-severity issues first"
            )
        
        return "\n".join(summary_parts)
    
    def _count_issues_by_severity(self, issues: List[CodeIssue]) -> str:
        """Count issues by severity level and return a formatted string.
        
        Args:
            issues: List of code issues to count
            
        Returns:
            str: Formatted string with issue counts by severity
        """
        from collections import defaultdict
        counts = defaultdict(int)
        for issue in issues:
            counts[issue.severity] += 1
            
        # Sort by severity (critical, high, medium, low, info)
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        sorted_counts = sorted(
            counts.items(),
            key=lambda x: severity_order.index(x[0]) if x[0] in severity_order else 99
        )
        
        return ", ".join(f"{count} {sev}" for sev, count in sorted_counts)
