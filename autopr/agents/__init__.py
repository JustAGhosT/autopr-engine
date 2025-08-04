"""
AutoPR Agent Framework

This module provides agent-based orchestration for code quality analysis using CrewAI.
"""

from .models import (
    IssueSeverity,
    CodeIssue,
    PlatformComponent,
    PlatformAnalysis,
    CodeAnalysisReport
)
from .crew import AutoPRCrew
from .agents import (
    CodeQualityAgent,
    PlatformAnalysisAgent,
    LintingAgent
)

__all__ = [
    'AutoPRCrew',
    'CodeQualityAgent',
    'PlatformAnalysisAgent',
    'LintingAgent',
    'IssueSeverity',
    'CodeIssue',
    'PlatformComponent',
    'PlatformAnalysis',
    'CodeAnalysisReport'
]
