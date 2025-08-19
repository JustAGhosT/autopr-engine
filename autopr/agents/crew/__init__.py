"""
Crew orchestration for the AutoPR Agent Framework.

Crew Orchestration Module

This module provides the AutoPRCrew class for orchestrating code analysis agents.
"""

# Import the main crew implementation
from autopr.actions.llm import get_llm_provider_manager
from autopr.agents.code_quality_agent import CodeQualityAgent

# Import tasks sub-module for convenient star-imports
from autopr.agents.crew import tasks
from autopr.agents.crew.main import AutoPRCrew
from autopr.agents.linting_agent import LintingAgent
from autopr.agents.platform_analysis_agent import PlatformAnalysisAgent


# Re-export the AutoPRCrew class
__all__ = [
    "AutoPRCrew",
    "CodeQualityAgent",
    "LintingAgent",
    "PlatformAnalysisAgent",
    "get_llm_provider_manager",
]
