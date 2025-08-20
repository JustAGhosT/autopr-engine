"""
Specialist Manager for coordinating AI specialists.
"""

from typing import Any

from autopr.actions.ai_linting_fixer.models import LintingIssue

from .base_specialist import AgentType, BaseSpecialist
from .exception_specialist import ExceptionSpecialist
from .general_specialist import GeneralSpecialist
from .import_specialist import ImportSpecialist
from .line_length_specialist import LineLengthSpecialist
from .logging_specialist import LoggingSpecialist
from .style_specialist import StyleSpecialist
from .variable_specialist import VariableSpecialist


class SpecialistManager:
    """Manages all specialists and their selection."""

    def __init__(self):
        """Initialize the specialist manager with all available specialists."""
        self.specialists = {
            AgentType.LINE_LENGTH: LineLengthSpecialist(),
            AgentType.IMPORT_OPTIMIZER: ImportSpecialist(),
            AgentType.VARIABLE_CLEANER: VariableSpecialist(),
            AgentType.EXCEPTION_HANDLER: ExceptionSpecialist(),
            AgentType.STYLE_FIXER: StyleSpecialist(),
            AgentType.LOGGING_SPECIALIST: LoggingSpecialist(),
            AgentType.GENERAL_FIXER: GeneralSpecialist(),
        }

    def get_specialist_for_issues(self, issues: list[LintingIssue]) -> BaseSpecialist:
        """Get the best specialist for the given issues."""
        if not issues:
            return self.specialists[AgentType.GENERAL_FIXER]

        # Calculate specialization scores for all specialists
        scores = {}
        for agent_type, specialist in self.specialists.items():
            score = specialist.get_specialization_score(issues)
            scores[agent_type] = score

        # Select the specialist with the highest score
        best_agent_type = max(scores, key=scores.get)
        return self.specialists[best_agent_type]

    def get_specialist_by_type(self, agent_type: AgentType) -> BaseSpecialist:
        """Get a specialist by its type."""
        return self.specialists.get(agent_type, self.specialists[AgentType.GENERAL_FIXER])

    def get_specialist_stats(self) -> dict[str, dict[str, Any]]:
        """Get performance statistics for all specialists."""
        stats = {}
        for agent_type, specialist in self.specialists.items():
            stats[specialist.name] = {
                "agent_type": agent_type.value,
                "supported_codes": specialist.supported_codes,
                "expertise_level": specialist.expertise_level,
                "attempts": specialist.performance.attempts,
                "successes": specialist.performance.successes,
                "success_rate": specialist.performance.success_rate,
                "average_confidence": specialist.performance.average_confidence,
                "total_fixes": specialist.performance.total_fixes,
            }
        return stats

    def record_specialist_result(
        self, agent_type: AgentType, success: bool, confidence: float = 0.0
    ) -> None:
        """Record the result of a specialist's attempt."""
        if agent_type in self.specialists:
            self.specialists[agent_type].record_attempt(success, confidence)
