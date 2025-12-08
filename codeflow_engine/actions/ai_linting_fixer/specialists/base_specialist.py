"""
Base specialist class and related models for AI linting fixer specialists.
"""

from abc import ABC, abstractmethod
from enum import Enum
import logging

from pydantic import BaseModel

from codeflow_engine.actions.ai_linting_fixer.models import LintingIssue


logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of specialized agents for different linting issue categories."""

    LINE_LENGTH = "line_length_agent"
    IMPORT_OPTIMIZER = "import_agent"
    VARIABLE_CLEANER = "variable_agent"
    EXCEPTION_HANDLER = "exception_agent"
    STYLE_FIXER = "style_agent"
    LOGGING_SPECIALIST = "logging_agent"
    GENERAL_FIXER = "general_agent"


class FixStrategy(BaseModel):
    """Strategy for fixing issues with specific approaches."""

    name: str
    description: str
    confidence_multiplier: float = 1.0
    max_retries: int = 3
    requires_context: bool = True
    priority: int = 1  # Lower number = higher priority


class AgentPerformance(BaseModel):
    """Performance tracking for agents."""

    attempts: int = 0
    successes: int = 0
    total_fixes: int = 0
    average_confidence: float = 0.0
    last_used: str | None = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.attempts == 0:
            return 0.0
        return self.successes / self.attempts


class BaseSpecialist(ABC):
    """Base class for all AI specialists."""

    def __init__(self, agent_type: AgentType):
        """Initialize the specialist."""
        self.agent_type = agent_type
        self.name = self.__class__.__name__
        self.supported_codes = self._get_supported_codes()
        self.expertise_level = self._get_expertise_level()
        self.fix_strategies = self._define_fix_strategies()
        self.performance = AgentPerformance()

    @abstractmethod
    def _get_supported_codes(self) -> list[str]:
        """Get the list of error codes this specialist supports."""
        pass

    @abstractmethod
    def _get_expertise_level(self) -> str:
        """Get the expertise level of this specialist."""
        pass

    @abstractmethod
    def _define_fix_strategies(self) -> list[FixStrategy]:
        """Define the fix strategies this specialist uses."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this specialist."""
        pass

    def get_user_prompt(
        self, file_path: str, content: str, issues: list[LintingIssue]
    ) -> str:
        """Get the user prompt for fixing issues."""
        issue_lines = [f"Line {issue.line_number}: {issue.message}" for issue in issues]

        return f"""Fix the following issues in this Python code:

ISSUES TO FIX:
{chr(10).join(issue_lines)}

CODE:
```python
{content}
```

Please fix ONLY the specified issues. Return the corrected code maintaining exact functionality."""

    def can_handle_issues(self, issues: list[LintingIssue]) -> bool:
        """Check if this specialist can handle the given issues."""
        if not issues:
            return False
        return all(self.can_handle_issue(issue) for issue in issues)

    def can_handle_issue(self, issue: LintingIssue) -> bool:
        """Check if this specialist can handle a specific issue."""
        return any(issue.error_code.startswith(code) for code in self.supported_codes)

    def can_handle_issues_from_codes(self, codes: list[str]) -> bool:
        """Check if this specialist can handle issues with the given codes."""
        if not codes:
            return False
        return any(self.can_handle_issue_code(code) for code in codes)

    def can_handle_issue_code(self, code: str) -> bool:
        """Check if this specialist can handle a specific issue code."""
        return any(
            code.startswith(supported_code) for supported_code in self.supported_codes
        )

    def get_confidence_multiplier(self, issue_code: str) -> float:
        """Get confidence multiplier for a specific issue code."""
        if not self.can_handle_issue_code(issue_code):
            return 0.0

        # Find the best strategy for this issue
        best_strategy = max(self.fix_strategies, key=lambda s: s.confidence_multiplier)
        return best_strategy.confidence_multiplier

    def get_specialization_score(self, issues: list[LintingIssue]) -> float:
        """Calculate specialization score for the given issues."""
        if not issues:
            return 0.0

        # Count how many issues this specialist can handle
        handled_count = sum(1 for issue in issues if self.can_handle_issue(issue))
        coverage_ratio = handled_count / len(issues)

        # Factor in success rate
        success_rate = self.performance.success_rate

        # Factor in expertise level
        expertise_multiplier = {
            "expert": 1.2,
            "advanced": 1.1,
            "intermediate": 1.0,
            "basic": 0.9,
        }.get(self.expertise_level, 1.0)

        return coverage_ratio * success_rate * expertise_multiplier

    def record_attempt(self, success: bool, confidence: float = 0.0) -> None:
        """Record an attempt and its result."""
        self.performance.attempts += 1
        if success:
            self.performance.successes += 1
            self.performance.total_fixes += 1

        # Update average confidence
        if self.performance.attempts == 1:
            self.performance.average_confidence = confidence
        else:
            total_confidence = self.performance.average_confidence * (
                self.performance.attempts - 1
            )
            self.performance.average_confidence = (
                total_confidence + confidence
            ) / self.performance.attempts
