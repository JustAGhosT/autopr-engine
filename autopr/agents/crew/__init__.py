"""
Crew orchestration for the AutoPR Agent Framework.

Crew Orchestration Module

This module provides the AutoPRCrew class for orchestrating code analysis agents.
"""
# Import the main crew implementation
from .main import AutoPRCrew

# Import task creation functions for direct access if needed
from . import tasks

# Re-export the AutoPRCrew class
__all__ = ['AutoPRCrew']
