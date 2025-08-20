"""
Import Specialist for fixing import-related issues (F401, F811, etc.).
"""

from autopr.actions.ai_linting_fixer.models import LintingIssue
from autopr.actions.ai_linting_fixer.specialists.base_specialist import (
    AgentType,
    BaseSpecialist,
    FixStrategy,
)


class ImportSpecialist(BaseSpecialist):
    """Specialized agent for fixing import-related issues (F401, F811)."""

    def __init__(self):
        super().__init__(AgentType.IMPORT_OPTIMIZER)

    def _get_supported_codes(self) -> list[str]:
        return ["F401", "F811", "F405", "F403", "F402"]

    def _get_expertise_level(self) -> str:
        return "expert"

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="safe_removal",
                description="Safely remove unused imports after thorough analysis",
                confidence_multiplier=1.3,
                priority=1,
                requires_context=True,
            ),
            FixStrategy(
                name="conditional_import",
                description="Move imports inside functions if used conditionally",
                confidence_multiplier=0.9,
                priority=2,
            ),
            FixStrategy(
                name="import_grouping",
                description="Reorganize imports to fix redefinition issues",
                confidence_multiplier=1.1,
                priority=3,
            ),
        ]

    def get_system_prompt(self) -> str:
        return """You are an IMPORT OPTIMIZATION SPECIALIST AI. Your expertise is fixing import-related issues.

CORE PRINCIPLES:
1. Remove unused imports (F401) safely
2. Fix import redefinitions (F811)
3. Organize imports following PEP 8
4. Preserve functionality - never remove imports that ARE actually used
5. Consider dynamic usage (getattr, eval, string references)

ANALYSIS STEPS:
1. Scan entire file for ALL usage of the imported name
2. Check for indirect usage (getattr, locals(), globals())
3. Look for usage in strings, comments, or docstrings
4. Verify the import is truly unused before removing

IMPORT ORGANIZATION:
1. Standard library imports
2. Third-party imports
3. Local application imports
4. Separated by blank lines

BE EXTREMELY CAREFUL: Only remove imports you are 100% certain are unused."""

    def get_user_prompt(self, file_path: str, content: str, issues: list[LintingIssue]) -> str:
        """Get user prompt for import fixes."""
        prompt = f"Please fix the following import issues in the Python file '{file_path}':\n\n"

        # Add specific issue details
        for issue in issues:
            if issue.error_code in ["F401", "F811"]:
                prompt += f"Line {issue.line_number}: {issue.error_code} - {issue.message}\n"
                prompt += f"Content: {issue.line_content}\n\n"

        prompt += f"File content:\n```python\n{content}\n```\n\n"
        prompt += "Please provide ONLY the specific lines that need to be fixed, not the entire file. Focus on the exact changes needed to resolve the import issues."

        return prompt
