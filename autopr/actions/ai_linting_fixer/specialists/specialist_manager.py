"""
Specialist Manager

This module manages all AI specialists and coordinates their selection and usage.
"""

from typing import List, Dict, Type

from .base_specialist import BaseSpecialist
from .line_length_specialist import LineLengthSpecialist
from .import_specialist import ImportSpecialist
from .variable_specialist import VariableSpecialist
from .exception_specialist import ExceptionSpecialist
from .style_specialist import StyleSpecialist
from .logging_specialist import LoggingSpecialist
from .general_specialist import GeneralSpecialist

from autopr.actions.ai_linting_fixer.models import LintingIssue


class SpecialistManager:
    """Manages all AI specialists and their selection."""

    def __init__(self):
        """Initialize the specialist manager."""
        self.specialists: Dict[str, BaseSpecialist] = {}
        self._initialize_specialists()

    def _initialize_specialists(self):
        """Initialize all available specialists."""
        specialist_classes = [
            LineLengthSpecialist,
            LoggingSpecialist,
            ImportSpecialist,
            VariableSpecialist,
            ExceptionSpecialist,
            StyleSpecialist,
            GeneralSpecialist,
        ]

        for specialist_class in specialist_classes:
            specialist = specialist_class()
            self.specialists[specialist.name] = specialist

    def get_specialist_for_issues(self, issues: List[LintingIssue]) -> BaseSpecialist:
        """Get the best specialist for the given issues."""
        if not issues:
            return self.specialists["GeneralSpecialist"]

        # Calculate specialization scores for each specialist
        scores = {}
        for name, specialist in self.specialists.items():
            score = specialist.get_specialization_score(issues)
            scores[name] = score

        # Find the specialist with the highest score
        best_specialist_name = max(scores, key=scores.get)
        best_score = scores[best_specialist_name]

        # If no specialist has a good match, use the general specialist
        if best_score == 0.0:
            return self.specialists["GeneralSpecialist"]

        return self.specialists[best_specialist_name]

    def get_specialist_by_name(self, name: str) -> BaseSpecialist:
        """Get a specialist by name."""
        return self.specialists.get(name, self.specialists["GeneralSpecialist"])

    def get_all_specialists(self) -> Dict[str, BaseSpecialist]:
        """Get all available specialists."""
        return self.specialists.copy()

    def get_specialist_stats(self) -> Dict[str, Dict]:
        """Get statistics about all specialists."""
        stats = {}
        for name, specialist in self.specialists.items():
            stats[name] = {
                "supported_codes": specialist.supported_codes,
                "expertise_level": specialist.expertise_level,
                "can_handle_wildcard": "*" in specialist.supported_codes,
            }
        return stats

    def list_supported_codes(self) -> List[str]:
        """Get a list of all supported error codes."""
        codes = set()
        for specialist in self.specialists.values():
            codes.update(specialist.supported_codes)
        return sorted(list(codes))
