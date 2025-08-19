"""
Line Length Specialist

This specialist handles E501 line-too-long errors by intelligently breaking long lines.
"""

from typing import List

from .base_specialist import BaseSpecialist
from autopr.actions.ai_linting_fixer.models import LintingIssue


class LineLengthSpecialist(BaseSpecialist):
    """Specialist for fixing line length issues (E501)."""

    def _get_supported_codes(self) -> List[str]:
        """Get supported error codes."""
        return ["E501"]

    def _get_expertise_level(self) -> str:
        """Get expertise level."""
        return "expert"

    def get_system_prompt(self, issues: List[LintingIssue]) -> str:
        """Get specialized system prompt for line length fixes."""
        return """You are a LINE LENGTH SPECIALIST AI. Your expertise is fixing E501 line-too-long errors.

CORE PRINCIPLES:
1. Break lines at logical points (after operators, commas, parentheses)
2. Maintain readability and code structure
3. Follow PEP 8 line length guidelines (typically 79-88 characters)
4. Preserve indentation and formatting
5. Use parentheses for line continuation when possible

BREAKING STRATEGIES:
• Function calls: Break after commas, before closing parenthesis
• String concatenation: Use parentheses or + operator
• Long variable assignments: Break after = or operators
• Import statements: Break after commas
• Dictionary/list literals: Break after commas
• Method chains: Break after dots or parentheses

AVOID:
• Breaking in the middle of words or strings
• Creating less readable code
• Changing logic or functionality
• Using backslash continuation (\\) unless absolutely necessary

Focus on making clean, readable fixes that improve code quality.

Provide your response in the following JSON format:
{
    "success": true/false,
    "fixed_code": "only the specific lines that were fixed",
    "changes_made": ["list of specific changes made"],
    "confidence": 0.0-1.0,
    "explanation": "brief explanation of the fix"
}

IMPORTANT: In the "fixed_code" field, provide ONLY the specific lines that need to be changed, not the entire file."""

    def get_user_prompt(
        self, file_path: str, content: str, issues: List[LintingIssue]
    ) -> str:
        """Get user prompt for line length fixes."""
        prompt = f"Please fix the following line length issues in the Python file '{file_path}':\n\n"

        # Add specific issue details
        for issue in issues:
            if issue.error_code == "E501":
                prompt += f"Line {issue.line_number}: {issue.message}\n"
                prompt += f"Content: {issue.line_content}\n\n"

        prompt += f"File content:\n```python\n{content}\n```\n\n"
        prompt += "Please provide ONLY the specific lines that need to be fixed, not the entire file. Focus on the exact changes needed to resolve the line length issues."

        return prompt
