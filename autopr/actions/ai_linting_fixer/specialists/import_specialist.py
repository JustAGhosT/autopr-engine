"""
Import Specialist

This specialist handles import-related issues like F401 (unused imports) and F811 (redefined imports).
"""

from typing import List

from .base_specialist import BaseSpecialist
from autopr.actions.ai_linting_fixer.models import LintingIssue


class ImportSpecialist(BaseSpecialist):
    """Specialist for fixing import issues (F401, F811)."""

    def _get_supported_codes(self) -> List[str]:
        """Get supported error codes."""
        return ["F401", "F811"]

    def _get_expertise_level(self) -> str:
        """Get expertise level."""
        return "expert"

    def get_system_prompt(self, issues: List[LintingIssue]) -> str:
        """Get specialized system prompt for import fixes."""
        return """You are an IMPORT SPECIALIST AI. Your expertise is fixing import-related issues.

SUPPORTED ISSUES:
• F401: Unused import (imported but not used)
• F811: Redefined import (imported multiple times)

CORE PRINCIPLES:
1. Remove unused imports to clean up code
2. Consolidate duplicate imports
3. Maintain import order and grouping
4. Preserve necessary imports for functionality
5. Follow PEP 8 import guidelines

FIXING STRATEGIES:
• F401: Remove the unused import statement
• F811: Consolidate duplicate imports into a single statement
• Group imports: standard library, third-party, local
• Use absolute imports when possible
• Maintain alphabetical order within groups

IMPORT ORDER (PEP 8):
1. Standard library imports
2. Third-party imports
3. Local application imports
4. Each group separated by blank line

EXAMPLES:
• Remove: import unused_module  # if not used
• Consolidate: 
  import os
  import os  # duplicate
  → import os
• Group: import json, os, sys  # standard library together

AVOID:
• Removing imports that are actually used
• Breaking import dependencies
• Changing import order unnecessarily
• Removing __future__ imports

Focus on cleaning up imports while maintaining code functionality.

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
        """Get user prompt for import fixes."""
        prompt = f"Please fix the following import issues in the Python file '{file_path}':\n\n"

        # Add specific issue details
        for issue in issues:
            if issue.error_code in ["F401", "F811"]:
                prompt += (
                    f"Line {issue.line_number}: {issue.error_code} - {issue.message}\n"
                )
                prompt += f"Content: {issue.line_content}\n\n"

        prompt += f"File content:\n```python\n{content}\n```\n\n"
        prompt += "Please provide ONLY the specific lines that need to be fixed, not the entire file. Focus on the exact changes needed to resolve the import issues."

        return prompt
