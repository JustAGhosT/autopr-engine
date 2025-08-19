"""
Logging Specialist

This specialist handles logging-related issues like G004 (logging-f-string) and TRY401 (verbose-log-message).
"""

from typing import List

from .base_specialist import BaseSpecialist
from autopr.actions.ai_linting_fixer.models import LintingIssue


class LoggingSpecialist(BaseSpecialist):
    """Specialist for fixing logging issues (G004, TRY401)."""

    def _get_supported_codes(self) -> List[str]:
        """Get supported error codes."""
        return ["G004", "TRY401"]

    def _get_expertise_level(self) -> str:
        """Get expertise level."""
        return "expert"

    def get_system_prompt(self, issues: List[LintingIssue]) -> str:
        """Get specialized system prompt for logging fixes."""
        return """You are a LOGGING SPECIALIST AI. Your expertise is fixing logging-related issues.

SUPPORTED ISSUES:
• G004: Logging statement uses f-string (should use % formatting or .format())
• TRY401: Verbose log message (should be simplified)

CORE PRINCIPLES:
1. Replace f-strings in logging with % formatting or .format()
2. Simplify verbose log messages for better performance
3. Maintain logging functionality and message clarity
4. Follow Python logging best practices
5. Preserve log levels and context

FIXING STRATEGIES:
• G004: Convert f"message {var}" to "message %s" % var or "message {}".format(var)
• TRY401: Simplify verbose messages while keeping essential information
• Use % formatting for simple variable substitution
• Use .format() for complex formatting
• Avoid string concatenation in logging calls

EXAMPLES:
• logger.info(f"Processing {file}") → logger.info("Processing %s", file)
• logger.error(f"Failed to {action} {object}") → logger.error("Failed to %s %s", action, object)
• logger.debug(f"Complex {obj.name} with {obj.value}") → logger.debug("Complex %s with %s", obj.name, obj.value)

AVOID:
• Breaking logging functionality
• Losing important context in messages
• Making messages less informative
• Changing log levels

Focus on making logging more efficient and compliant with best practices.

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
        """Get user prompt for logging fixes."""
        prompt = f"Please fix the following logging issues in the Python file '{file_path}':\n\n"

        # Add specific issue details
        for issue in issues:
            if issue.error_code in ["G004", "TRY401"]:
                prompt += (
                    f"Line {issue.line_number}: {issue.error_code} - {issue.message}\n"
                )
                prompt += f"Content: {issue.line_content}\n\n"

        prompt += f"File content:\n```python\n{content}\n```\n\n"
        prompt += "Please provide ONLY the specific lines that need to be fixed, not the entire file. Focus on the exact changes needed to resolve the logging issues."

        return prompt
