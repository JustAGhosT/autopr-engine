"""
Specialists package for AI linting fixer.

This package contains specialized AI agents for different types of linting issues.
"""

from autopr.actions.ai_linting_fixer.specialists.base_specialist import (
    AgentPerformance,
    AgentType,
    BaseSpecialist,
    FixStrategy,
)
from autopr.actions.ai_linting_fixer.specialists.exception_specialist import ExceptionSpecialist
from autopr.actions.ai_linting_fixer.specialists.general_specialist import GeneralSpecialist
from autopr.actions.ai_linting_fixer.specialists.import_specialist import ImportSpecialist
from autopr.actions.ai_linting_fixer.specialists.line_length_specialist import LineLengthSpecialist
from autopr.actions.ai_linting_fixer.specialists.logging_specialist import LoggingSpecialist
from autopr.actions.ai_linting_fixer.specialists.specialist_manager import SpecialistManager
from autopr.actions.ai_linting_fixer.specialists.style_specialist import StyleSpecialist
from autopr.actions.ai_linting_fixer.specialists.variable_specialist import VariableSpecialist


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
]
