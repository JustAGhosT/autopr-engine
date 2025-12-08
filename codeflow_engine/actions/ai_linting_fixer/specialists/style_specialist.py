"""
Style Specialist for fixing style and formatting issues.
"""

from codeflow_engine.actions.ai_linting_fixer.specialists.base_specialist import (
    AgentType,
    BaseSpecialist,
    FixStrategy,
)


class StyleSpecialist(BaseSpecialist):
    """Specialized agent for fixing style and formatting issues."""

    def __init__(self):
        super().__init__(AgentType.STYLE_FIXER)

    def _get_supported_codes(self) -> list[str]:
        return ["E501", "E302", "E305", "E303", "E304", "UP006", "TID252"]

    def _get_expertise_level(self) -> str:
        return "intermediate"

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="style_fixes",
                description="Apply PEP 8 style fixes",
                confidence_multiplier=1.1,
                priority=1,
            ),
            FixStrategy(
                name="formatting",
                description="Improve code formatting and structure",
                confidence_multiplier=1.0,
                priority=2,
            ),
        ]

    def get_system_prompt(self) -> str:
        return """You are a STYLE FIXER SPECIALIST AI. Your expertise is fixing Python style and formatting issues.

CORE PRINCIPLES:
1. Follow PEP 8 style guidelines
2. Improve code readability and consistency
3. Fix spacing, indentation, and formatting issues
4. Maintain code functionality while improving style
5. Apply modern Python idioms when appropriate

COMMON FIXES:
• Fix spacing around operators and keywords
• Improve import organization
• Fix indentation issues
• Apply consistent formatting
• Use modern Python syntax when beneficial

Focus on making code more readable and maintainable."""
