"""
Exception Specialist

This specialist handles exception-related issues like E722 (bare except) and B001 (bare except).
"""

from typing import List

from .base_specialist import BaseSpecialist
from autopr.actions.ai_linting_fixer.models import LintingIssue


class ExceptionSpecialist(BaseSpecialist):
    """Specialist for fixing exception handling issues (E722, B001)."""

    def _get_supported_codes(self) -> List[str]:
        """Get supported error codes."""
        return ["E722", "B001"]

    def _get_expertise_level(self) -> str:
        """Get expertise level."""
        return "expert"

    def get_system_prompt(self, issues: List[LintingIssue]) -> str:
        """Get specialized system prompt for exception fixes."""
        return """You are an EXCEPTION SPECIALIST AI. Your expertise is fixing exception handling issues.

SUPPORTED ISSUES:
• E722: Bare except clause (should specify exception type)
• B001: Bare except clause (should specify exception type)

CORE PRINCIPLES:
1. Replace bare except clauses with specific exception types
2. Maintain proper exception handling logic
3. Preserve error handling functionality
4. Follow Python exception handling best practices
5. Use appropriate exception types for the context

FIXING STRATEGIES:
• Replace bare except: with specific exception types
• Use Exception for general error handling
• Use specific exceptions (ValueError, TypeError, etc.) when appropriate
• Maintain the existing exception handling logic
• Add logging or error reporting when needed

EXAMPLES:
• except: → except Exception:
• except: → except (ValueError, TypeError):
• except: → except OSError:  # for file operations
• except: → except (KeyError, IndexError):  # for dict/list access

COMMON EXCEPTION TYPES:
• Exception: General exceptions
• ValueError: Invalid value/argument
• TypeError: Wrong type
• OSError: Operating system errors
• KeyError: Dictionary key not found
• IndexError: List index out of range
• AttributeError: Attribute not found
• ImportError: Import failed

AVOID:
• Breaking existing error handling
• Catching exceptions that shouldn't be caught
• Making exception handling less specific
• Removing necessary exception handling

Focus on making exception handling more specific and robust.

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
        """Get user prompt for exception fixes."""
        prompt = f"Please fix the following exception handling issues in the Python file '{file_path}':\n\n"

        # Add specific issue details
        for issue in issues:
            if issue.error_code in ["E722", "B001"]:
                prompt += (
                    f"Line {issue.line_number}: {issue.error_code} - {issue.message}\n"
                )
                prompt += f"Content: {issue.line_content}\n\n"

        prompt += f"File content:\n```python\n{content}\n```\n\n"
        prompt += "Please provide ONLY the specific lines that need to be fixed, not the entire file. Focus on the exact changes needed to resolve the exception handling issues."

        return prompt
