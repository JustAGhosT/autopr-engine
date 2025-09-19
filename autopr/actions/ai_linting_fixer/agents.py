"""
Specialized AI Agents for Linting Issue Types

This module provides specialized AI agents that are experts in fixing specific
types of linting issues, with tailored prompts and strategies for each issue type.
"""

# Import from the modular specialists package
from autopr.actions.ai_linting_fixer.specialists import (
    AgentPerformance,
    AgentType,
    BaseSpecialist,
    ExceptionSpecialist,
    FixStrategy,
    GeneralSpecialist,
    ImportSpecialist,
    LineLengthSpecialist,
    LoggingSpecialist,
    SpecialistManager,
    StyleSpecialist,
    VariableSpecialist,
)


# Create a global specialist manager instance
specialist_manager = SpecialistManager()

__all__ = [
    "BaseSpecialist",
    "AgentType",
    "FixStrategy",
    "AgentPerformance",
    "LineLengthSpecialist",
    "ImportSpecialist",
    "VariableSpecialist",
    "ExceptionSpecialist",
    "StyleSpecialist",
    "LoggingSpecialist",
    "GeneralSpecialist",
    "SpecialistManager",
    "specialist_manager",
]
