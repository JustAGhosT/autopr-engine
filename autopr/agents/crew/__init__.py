"""
Crew orchestration for the AutoPR Agent Framework.

Crew Orchestration Module

This module provides the AutoPRCrew class for orchestrating code analysis agents.
"""
# Import the main crew implementation
from .main import AutoPRCrew

# Import tasks sub-module for convenient star-imports
from . import tasks  # noqa: F401

# Re-export the AutoPRCrew class
__all__ = ['AutoPRCrew']
