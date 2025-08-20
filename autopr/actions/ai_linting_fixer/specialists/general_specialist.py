"""
General Specialist for miscellaneous issues.
"""

from .base_specialist import AgentType, BaseSpecialist, FixStrategy


class GeneralSpecialist(BaseSpecialist):
    """General-purpose specialist for miscellaneous issues."""

    def __init__(self):
        super().__init__(AgentType.GENERAL_FIXER)

    def _get_supported_codes(self) -> list[str]:
        return ["*"]  # Handles all codes

    def _get_expertise_level(self) -> str:
        return "basic"

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="general_fixes",
                description="Apply general code improvements",
                confidence_multiplier=0.8,
                priority=1,
            ),
        ]

    def get_system_prompt(self) -> str:
        return """You are a GENERAL CODE FIXER AI. Your task is to fix various Python code issues.

CORE PRINCIPLES:
1. Fix the specific issues identified
2. Maintain code functionality and logic
3. Follow Python best practices
4. Improve code quality when possible
5. Preserve existing behavior

APPROACH:
• Focus on the specific issues mentioned
• Make minimal necessary changes
• Ensure code remains functional
• Follow Python conventions
• Test your changes mentally

Be conservative and only fix what's explicitly requested."""
