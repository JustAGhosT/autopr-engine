"""
Variable Specialist for fixing unused variable issues (F841, F821).
"""

from autopr.actions.ai_linting_fixer.models import LintingIssue
from autopr.actions.ai_linting_fixer.specialists.base_specialist import (
    AgentType,
    BaseSpecialist,
    FixStrategy,
)


class VariableSpecialist(BaseSpecialist):
    """Specialized agent for fixing unused variable issues (F841, F821)."""

    def __init__(self):
        super().__init__(AgentType.VARIABLE_CLEANER)

    def _get_supported_codes(self) -> list[str]:
        return ["F841", "F821", "F823"]

    def _get_expertise_level(self) -> str:
        return "advanced"

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="underscore_prefix",
                description="Add underscore prefix to indicate intentionally unused",
                confidence_multiplier=1.2,
                priority=1,
            ),
            FixStrategy(
                name="variable_removal",
                description="Remove unused variable assignments",
                confidence_multiplier=1.1,
                priority=2,
            ),
            FixStrategy(
                name="use_variable",
                description="Add meaningful usage of the variable",
                confidence_multiplier=0.8,
                priority=3,
            ),
        ]

    def get_system_prompt(self) -> str:
        return """You are a VARIABLE CLEANUP SPECIALIST AI. Your expertise is fixing unused variable issues.

CORE PRINCIPLES:
1. Remove truly unused variables (F841)
2. Fix undefined variable references (F821)
3. Use underscore prefix for intentionally unused variables
4. Preserve code functionality and logic
5. Consider future usage patterns

STRATEGIES:
• Add underscore prefix (_variable) for intentionally unused variables
• Remove unused variable assignments when safe
• Fix undefined variable references
• Consider if variable might be used in future development

BE CAREFUL: Some variables might be used for side effects or future functionality."""

    def get_user_prompt(
        self, file_path: str, content: str, issues: list[LintingIssue]
    ) -> str:
        """Get user prompt for variable fixes."""
        prompt = f"Please fix the following variable issues in the Python file '{file_path}':\n\n"

        # Add specific issue details
        for issue in issues:
            if issue.error_code in ["F841", "F821"]:
                prompt += (
                    f"Line {issue.line_number}: {issue.error_code} - {issue.message}\n"
                )
                prompt += f"Content: {issue.line_content}\n\n"

        prompt += f"File content:\n```python\n{content}\n```\n\n"
        prompt += (
            "Please provide ONLY the specific lines that need to be fixed, "
            "not the entire file. Focus on the exact changes needed to "
            "resolve the variable issues."
        )

        return prompt
