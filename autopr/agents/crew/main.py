"""
Main crew module for the AutoPR Agent Framework.

This module contains the main AutoPRCrew class that orchestrates the code analysis agents.
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from crewai import Crew, Process

from autopr.actions.llm import get_llm_provider_manager
from autopr.agents.models import CodeAnalysisReport, CodeIssue, PlatformAnalysis
from autopr.agents.crew.tasks import (
    create_code_quality_task,
    create_platform_analysis_task,
    create_linting_task,
    generate_analysis_summary
)
from autopr.agents.code_quality_agent import CodeQualityAgent
from autopr.agents.platform_analysis_agent import PlatformAnalysisAgent
from autopr.agents.linting_agent import LintingAgent

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
        
        # Create context with volume information
        context = {
            "repo_path": str(repo_path.absolute()),
            "volume": current_volume,
            **analysis_kwargs
        }
        
        # Create tasks for each analysis type with volume context
        tasks = [
            create_code_quality_task(repo_path, context, self.code_quality_agent),
            create_platform_analysis_task(repo_path, context, self.platform_agent),
            create_linting_task(repo_path, context, self.linting_agent)
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
                logger.error(f"Error during analysis: {result}")
                continue
                
            if isinstance(result, dict) and "metrics" in result:
                code_quality = result
            elif isinstance(result, PlatformAnalysis):
                platform_analysis = result
            elif isinstance(result, list) and all(isinstance(x, CodeIssue) for x in result):
                linting_issues = result
        
        # Generate the final report
        return generate_analysis_summary(
            code_quality=code_quality,
            platform_analysis=platform_analysis,
            linting_issues=linting_issues,
            volume=current_volume
        )
