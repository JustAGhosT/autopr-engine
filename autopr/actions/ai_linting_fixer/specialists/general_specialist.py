"""
General Specialist

This specialist serves as a fallback for all other linting issues not handled by specific specialists.
"""

from typing import List

from .base_specialist import BaseSpecialist
from autopr.actions.ai_linting_fixer.models import LintingIssue


class GeneralSpecialist(BaseSpecialist):
    """General specialist for fixing any linting issues."""

    def _get_supported_codes(self) -> List[str]:
        """Get supported error codes - handles all codes."""
        return ["*"]  # Wildcard for all codes

    def _get_expertise_level(self) -> str:
        """Get expertise level."""
        return "general"

    def get_system_prompt(self, issues: List[LintingIssue]) -> str:
        """Get general system prompt for any linting fixes."""
        return """You are a GENERAL CODE FIXER AI. Your expertise is fixing various Python linting issues.

CORE PRINCIPLES:
1. Fix linting issues while maintaining code functionality
2. Follow Python best practices and PEP 8 guidelines
3. Preserve code logic and behavior
4. Improve code readability and maintainability
5. Use appropriate Python idioms and patterns

GENERAL FIXING STRATEGIES:
• Read and understand the specific linting error
• Apply appropriate fixes based on the error type
• Maintain code structure and indentation
• Preserve variable names and function signatures
• Ensure syntax correctness

COMMON FIXES:
• Fix indentation issues
• Correct syntax errors
• Improve variable naming
• Fix import statements
• Correct string formatting
• Fix logical errors

AVOID:
• Breaking existing functionality
• Changing code logic unnecessarily
• Making code less readable
• Introducing new errors

Focus on making targeted fixes that resolve the specific linting issues.

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
        """Get user prompt for general fixes."""
        prompt = f"Please fix the following linting issues in the Python file '{file_path}':\n\n"

        # Add specific issue details
        for issue in issues:
            prompt += (
                f"Line {issue.line_number}: {issue.error_code} - {issue.message}\n"
            )
            prompt += f"Content: {issue.line_content}\n\n"

        prompt += f"File content:\n```python\n{content}\n```\n\n"
        prompt += "Please provide ONLY the specific lines that need to be fixed, not the entire file. Focus on the exact changes needed to resolve the linting issues."

        return prompt
