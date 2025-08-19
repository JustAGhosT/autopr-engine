"""
Base Specialist for AI Linting Fixer

This module provides the base class for all AI specialists.
"""

from abc import ABC, abstractmethod
from typing import Any, List

from autopr.actions.ai_linting_fixer.models import LintingIssue


class BaseSpecialist(ABC):
    """Base class for all AI specialists."""

    def __init__(self):
        """Initialize the specialist."""
        self.name = self.__class__.__name__
        self.supported_codes = self._get_supported_codes()
        self.expertise_level = self._get_expertise_level()

    @abstractmethod
    def _get_supported_codes(self) -> List[str]:
        """Get the list of error codes this specialist supports."""
        pass

    @abstractmethod
    def _get_expertise_level(self) -> str:
        """Get the expertise level of this specialist."""
        pass

    @abstractmethod
    def get_system_prompt(self, issues: List[LintingIssue]) -> str:
        """Get the specialized system prompt for this specialist."""
        pass

    @abstractmethod
    def get_user_prompt(
        self, file_path: str, content: str, issues: List[LintingIssue]
    ) -> str:
        """Get the user prompt for this specialist."""
        pass

    def can_handle_issues(self, issues: List[LintingIssue]) -> bool:
        """Check if this specialist can handle the given issues."""
        if not issues:
            return False

        for issue in issues:
            if issue.error_code in self.supported_codes:
                return True

        return False

    def get_confidence_multiplier(self, issues: List[LintingIssue]) -> float:
        """Get confidence multiplier based on issue types."""
        if not self.can_handle_issues(issues):
            return 0.0

        # Count how many issues we can handle
        handled_count = sum(
            1 for issue in issues if issue.error_code in self.supported_codes
        )
        total_count = len(issues)

        # Higher confidence for specialists that can handle more of the issues
        return handled_count / total_count

    def get_specialization_score(self, issues: List[LintingIssue]) -> float:
        """Get specialization score for issue selection."""
        if not issues:
            return 0.0

        # Count issues by type
        issue_counts = {}
        for issue in issues:
            issue_counts[issue.error_code] = issue_counts.get(issue.error_code, 0) + 1

        # Calculate score based on how well we match the issue types
        score = 0.0
        for code, count in issue_counts.items():
            if code in self.supported_codes:
                score += count

        return score / len(issues)

    def can_handle_issues_from_codes(self, codes: List[str]) -> bool:
        """Check if this specialist can handle the given error codes."""
        if not codes:
            return False

        for code in codes:
            if code == "*" or code in self.supported_codes:
                return True

        return False
