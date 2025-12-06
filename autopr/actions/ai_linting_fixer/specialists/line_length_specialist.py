"""
Line Length Specialist for fixing E501 line-too-long errors.
"""

from autopr.actions.ai_linting_fixer.models import LintingIssue
from autopr.actions.ai_linting_fixer.specialists.base_specialist import (
    AgentType,
    BaseSpecialist,
    FixStrategy,
)


class LineLengthSpecialist(BaseSpecialist):
    """Specialized agent for fixing line length issues (E501)."""

    def __init__(self):
        super().__init__(AgentType.LINE_LENGTH)

    def _get_supported_codes(self) -> list[str]:
        return ["E501"]

    def _get_expertise_level(self) -> str:
        return "expert"

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="smart_line_break",
                description="Break long lines at logical points (operators, commas, etc.)",
                confidence_multiplier=1.2,
                priority=1,
            ),
            FixStrategy(
                name="parentheses_wrapping",
                description="Use parentheses for implicit line continuation",
                confidence_multiplier=1.1,
                priority=2,
            ),
            FixStrategy(
                name="variable_extraction",
                description="Extract complex expressions to variables",
                confidence_multiplier=0.9,
                priority=3,
            ),
        ]

    def get_system_prompt(self) -> str:
        return """You are a LINE LENGTH SPECIALIST AI. Your expertise is fixing E501 line-too-long errors.

CORE PRINCIPLES:
1. Break lines at logical points (after operators, commas, parentheses)
2. Maintain code readability and logical flow
3. Use Python's implicit line continuation (parentheses) when possible
4. Preserve original functionality exactly
5. Follow PEP 8 line breaking guidelines

PREFERRED STRATEGIES:
• Break after operators (+, -, ==, and, or, etc.)
• Break after commas in function calls/definitions
• Use parentheses for implicit continuation
• Break long string concatenations
• Extract complex expressions to variables when needed

AVOID:
• Breaking in the middle of words or strings
• Creating less readable code
• Changing logic or functionality
• Using backslash continuation (\\) unless absolutely necessary

Focus on making clean, readable fixes that improve code quality."""

    def get_user_prompt(
        self, file_path: str, content: str, issues: list[LintingIssue]
    ) -> str:
        """Get user prompt for line length fixes."""
        prompt = f"Please fix the following line length issues in the Python file '{file_path}':\n\n"

        # Add specific issue details
        for issue in issues:
            if issue.error_code == "E501":
                prompt += f"Line {issue.line_number}: {issue.message}\n"
                prompt += f"Content: {issue.line_content}\n\n"

        prompt += f"File content:\n```python\n{content}\n```\n\n"
        prompt += (
            "Please provide ONLY the specific lines that need to be fixed, "
            "not the entire file. Focus on the exact changes needed to "
            "resolve the line length issues."
        )

        return prompt
