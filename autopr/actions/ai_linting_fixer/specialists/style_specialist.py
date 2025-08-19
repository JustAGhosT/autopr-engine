"""
Style Specialist

This specialist handles style and naming issues like F541 (f-string without placeholders) and E741 (ambiguous variable name).
"""

from typing import List

from .base_specialist import BaseSpecialist
from autopr.actions.ai_linting_fixer.models import LintingIssue


class StyleSpecialist(BaseSpecialist):
    """Specialist for fixing style and naming issues (F541, E741)."""

    def _get_supported_codes(self) -> List[str]:
        """Get supported error codes."""
        return ["F541", "E741"]

    def _get_expertise_level(self) -> str:
        """Get expertise level."""
        return "expert"

    def get_system_prompt(self, issues: List[LintingIssue]) -> str:
        """Get specialized system prompt for style fixes."""
        return """You are a STYLE SPECIALIST AI. Your expertise is fixing style and naming issues.

SUPPORTED ISSUES:
• F541: f-string without placeholders (should be regular string)
• E741: Ambiguous variable name (l, I, O, etc.)

CORE PRINCIPLES:
1. Convert f-strings without placeholders to regular strings
2. Replace ambiguous variable names with descriptive ones
3. Maintain code readability and clarity
4. Follow PEP 8 naming conventions
5. Preserve code functionality

FIXING STRATEGIES:
• F541: Convert f"string" to "string" when no placeholders
• E741: Replace l, I, O with descriptive names
• Use descriptive variable names
• Follow Python naming conventions
• Maintain code readability

EXAMPLES:
• F541: f"Hello world" → "Hello world"
• E741: l = [1, 2, 3] → items = [1, 2, 3]
• E741: I = 0 → index = 0
• E741: O = object() → obj = object()

COMMON REPLACEMENTS:
• l → items, list_data, elements
• I → index, i, counter
• O → obj, object_instance
• o → obj, item, element

AVOID:
• Breaking code functionality
• Making names less descriptive
• Changing variable scope
• Creating naming conflicts

Focus on improving code style and readability.

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
        """Get user prompt for style fixes."""
        prompt = f"Please fix the following style issues in the Python file '{file_path}':\n\n"

        # Add specific issue details
        for issue in issues:
            if issue.error_code in ["F541", "E741"]:
                prompt += (
                    f"Line {issue.line_number}: {issue.error_code} - {issue.message}\n"
                )
                prompt += f"Content: {issue.line_content}\n\n"

        prompt += f"File content:\n```python\n{content}\n```\n\n"
        prompt += "Please provide ONLY the specific lines that need to be fixed, not the entire file. Focus on the exact changes needed to resolve the style issues."

        return prompt
