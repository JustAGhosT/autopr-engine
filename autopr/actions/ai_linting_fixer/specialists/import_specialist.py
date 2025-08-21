"""
Import Specialist Module

This module provides specialized handling for import-related linting issues.
"""

from typing import List

from autopr.actions.ai_linting_fixer.models import LintingIssue
from autopr.actions.ai_linting_fixer.specialists.base_specialist import (
    AgentType,
    BaseSpecialist,
    FixStrategy,
)


class ImportSpecialist(BaseSpecialist):
    """Specialist for handling import-related linting issues."""

    def __init__(self):
        """Initialize the import specialist."""
        super().__init__(AgentType.IMPORT_OPTIMIZER)

    def _get_supported_codes(self) -> List[str]:
        """Get the list of error codes this specialist supports."""
        return [
            "F401",  # Unused imports
            "F403",  # Wildcard imports
            "F405",  # Name may be undefined or imported from star
            "TID252",  # Prefer absolute imports over relative imports
            "E402",  # Module level import not at top of file
            "E731",  # Do not assign a lambda expression
        ]

    def _get_expertise_level(self) -> str:
        """Get the expertise level of this specialist."""
        return "expert"

    def _define_fix_strategies(self) -> List[FixStrategy]:
        """Define the fix strategies this specialist uses."""
        return [
            FixStrategy(
                name="import_optimization",
                description="Optimize import statements for clarity and efficiency",
                confidence_multiplier=1.2,
                max_retries=2,
                requires_context=True,
                priority=1,
            ),
            FixStrategy(
                name="unused_import_removal",
                description="Remove unused imports to clean up the code",
                confidence_multiplier=1.5,
                max_retries=1,
                requires_context=False,
                priority=2,
            ),
        ]

    def get_system_prompt(self) -> str:
        """Get the system prompt for this specialist."""
        return """You are an expert Python import optimizer. Your role is to:

1. Remove unused imports (F401)
2. Replace wildcard imports with specific imports (F403)
3. Convert relative imports to absolute imports (TID252)
4. Move imports to the top of the file (E402)
5. Optimize import organization and structure

Always maintain code functionality while improving import clarity and efficiency."""

    def get_specialization_score(self, issues: List[LintingIssue]) -> float:
        """Calculate specialization score for import issues."""
        if not issues:
            return 0.0

        import_issues = [
            issue for issue in issues if issue.error_code in self.supported_codes
        ]

        if not import_issues:
            return 0.0

        # High specialization for import issues
        return min(1.0, len(import_issues) / len(issues) * 2.0)

    def validate_fix(
        self, original_content: str, fixed_content: str, issues: List[LintingIssue]
    ) -> bool:
        """Validate that the fix addresses the import issues."""
        # Basic validation - check if content changed
        if original_content == fixed_content:
            return False

        # Check for common import patterns
        import_keywords = ["import ", "from ", "as "]
        has_import_changes = any(
            keyword in fixed_content for keyword in import_keywords
        )

        return has_import_changes
