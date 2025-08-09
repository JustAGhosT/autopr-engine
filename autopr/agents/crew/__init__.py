"""
Crew orchestration for the AutoPR Agent Framework.

Crew Orchestration Module

This module provides the AutoPRCrew class for orchestrating code analysis agents.
"""
# Import the main crew implementation
from .main import AutoPRCrew
from autopr.agents.code_quality_agent import CodeQualityAgent
from autopr.agents.platform_analysis_agent import PlatformAnalysisAgent
from autopr.agents.linting_agent import LintingAgent
from autopr.actions.llm import get_llm_provider_manager

# Import tasks sub-module for convenient star-imports
from . import tasks  # noqa: F401

# Re-export the AutoPRCrew class
__all__ = ['AutoPRCrew', 'get_llm_provider_manager', 'CodeQualityAgent', 'PlatformAnalysisAgent', 'LintingAgent']
