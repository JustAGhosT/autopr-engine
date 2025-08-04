"""
Crew orchestration for the AutoPR Agent Framework.

This module defines the main crew that coordinates the code analysis agents.
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from crewai import Crew, Process, Task
from autopr.actions.llm import get_llm_provider_manager

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


class AutoPRCrew:
    """Main crew for orchestrating code analysis agents."""
    
    def __init__(self, llm_model: str = "gpt-4"):
        """Initialize the AutoPR crew with specialized agents."""
        self.llm_model = llm_model
        self.llm_provider = get_llm_provider_manager()
        
        # Initialize agents
        self.code_quality_agent = CodeQualityAgent(llm_model=llm_model)
        self.platform_agent = PlatformAnalysisAgent(llm_model=llm_model)
        self.linting_agent = LintingAgent(llm_model=llm_model)
        
        # Initialize the crew
        self.crew = Crew(
            agents=[
                self.code_quality_agent,
                self.platform_agent,
                self.linting_agent
            ],
            process=Process.hierarchical,
            manager_llm=self.llm_provider.get_llm(llm_model),
            verbose=True
        )
    
    async def analyze_repository(self, repo_path: Union[str, Path]) -> CodeAnalysisReport:
        """
        Run a full analysis of the repository.
        
        Args:
            repo_path: Path to the repository to analyze
            
        Returns:
            CodeAnalysisReport: Comprehensive analysis report
        """
        if isinstance(repo_path, str):
            repo_path = Path(repo_path)
        
        # Create tasks for each analysis type
        tasks = [
            self._create_code_quality_task(repo_path),
            self._create_platform_analysis_task(repo_path),
            self._create_linting_task(repo_path)
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
    
    def _create_code_quality_task(self, repo_path: Path) -> Task:
        """Create a task for code quality analysis."""
        return Task(
            description=f"""Analyze the codebase at {repo_path} for quality issues, including:
            - Code smells and anti-patterns
            - Performance bottlenecks
            - Security vulnerabilities
            - Test coverage gaps
            
            Generate a detailed report with specific issues and recommendations.""",
            agent=self.code_quality_agent,
            expected_output="A detailed report of code quality issues and improvement suggestions",
            context={"repo_path": str(repo_path.absolute())}
        )
    
    def _create_platform_analysis_task(self, repo_path: Path) -> Task:
        """Create a task for platform and technology stack analysis."""
        return Task(
            description=f"""Analyze the technology stack and platform architecture for {repo_path}:
            - Identify all framework and library dependencies
            - Detect platform-specific patterns and configurations
            - Assess version compatibility
            - Provide optimization recommendations
            
            Return a structured analysis of the technology stack.""",
            agent=self.platform_agent,
            expected_output="A structured analysis of the platform and technology stack",
            context={"repo_path": str(repo_path.absolute())}
        )
    
    def _create_linting_task(self, repo_path: Path) -> Task:
        """Create a task for code linting and style enforcement."""
        return Task(
            description=f"""Apply automated linting and code style fixes to {repo_path}:
            - Enforce code style guidelines
            - Fix common anti-patterns
            - Apply best practices
            - Ensure consistent formatting
            
            Return a list of all issues found and fixed.""",
            agent=self.linting_agent,
            expected_output="A list of code style issues found and fixed",
            context={"repo_path": str(repo_path.absolute())}
        )
    
    def _generate_summary(
        self,
        code_quality: Dict[str, Any],
        platform_analysis: Optional[PlatformAnalysis],
        linting_issues: List[CodeIssue]
    ) -> str:
        """Generate a human-readable summary of the analysis."""
        summary_parts = ["# AutoPR Code Analysis Report\n"]
        
        # Code quality summary
        metrics = code_quality.get("metrics", {})
        summary_parts.append("## Code Quality Metrics")
        for metric, value in metrics.items():
            summary_parts.append(f"- **{metric.replace('_', ' ').title()}**: {value:.2f}")
        
        # Platform summary
        if platform_analysis:
            summary_parts.append("\n## Platform Analysis")
            summary_parts.append(f"**Primary Platform**: {platform_analysis.platform} "
                               f"(confidence: {platform_analysis.confidence*100:.1f}%)")
            
            if platform_analysis.components:
                summary_parts.append("\n### Detected Components")
                for comp in sorted(platform_analysis.components, 
                                 key=lambda x: x.confidence, 
                                 reverse=True)[:5]:  # Top 5 components
                    version = f" v{comp.version}" if comp.version else ""
                    summary_parts.append(f"- {comp.name}{version} "
                                       f"({comp.confidence*100:.0f}% confidence)")
        
        # Linting issues summary
        if linting_issues:
            issue_counts = {}
            for issue in linting_issues:
                issue_counts[issue.severity] = issue_counts.get(issue.severity, 0) + 1
            
            summary_parts.append("\n## Code Style Issues")
            for severity in sorted(issue_counts.keys(), reverse=True):
                summary_parts.append(f"- **{severity.title()}**: {issue_counts[severity]} issues")
        
        return "\n".join(summary_parts)
