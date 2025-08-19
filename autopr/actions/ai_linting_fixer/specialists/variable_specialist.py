"""
Variable Specialist

This specialist handles variable-related issues like F841 (unused variables) and F821 (undefined names).
"""

from typing import List

from .base_specialist import BaseSpecialist
from autopr.actions.ai_linting_fixer.models import LintingIssue


class VariableSpecialist(BaseSpecialist):
    """Specialist for fixing variable issues (F841, F821)."""

    def _get_supported_codes(self) -> List[str]:
        """Get supported error codes."""
        return ["F841", "F821"]

    def _get_expertise_level(self) -> str:
        """Get expertise level."""
        return "expert"

    def get_system_prompt(self, issues: List[LintingIssue]) -> str:
        """Get specialized system prompt for variable fixes."""
        return """You are a VARIABLE SPECIALIST AI. Your expertise is fixing variable-related issues.

SUPPORTED ISSUES:
• F841: Unused variable (assigned but never used)
• F821: Undefined name (variable used but not defined)

CORE PRINCIPLES:
1. Remove unused variables to clean up code
2. Fix undefined variable references
3. Maintain code logic and functionality
4. Use meaningful variable names
5. Follow Python variable naming conventions

FIXING STRATEGIES:
• F841: Remove unused variable assignments or use underscore prefix
• F821: Define missing variables or fix variable names
• Use _ prefix for intentionally unused variables
• Ensure variables are properly scoped
• Check for typos in variable names

EXAMPLES:
• F841: result = process() → _ = process() or remove if not needed
• F821: print(undefined_var) → define undefined_var or fix typo
• Unused loop variable: for i in range(10): → for _ in range(10):

AVOID:
• Breaking code logic by removing needed variables
• Creating new variables unnecessarily
• Changing variable scope inappropriately
• Making variables less descriptive

Focus on cleaning up variable usage while maintaining code functionality.

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
        prompt += "Please provide ONLY the specific lines that need to be fixed, not the entire file. Focus on the exact changes needed to resolve the variable issues."

        return prompt
