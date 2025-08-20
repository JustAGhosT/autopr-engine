"""
Logging Specialist for fixing logging-related issues (G004).
"""

from .base_specialist import AgentType, BaseSpecialist, FixStrategy


class LoggingSpecialist(BaseSpecialist):
    """Specialized agent for fixing logging-related issues (G004)."""

    def __init__(self):
        super().__init__(AgentType.LOGGING_SPECIALIST)

    def _get_supported_codes(self) -> list[str]:
        return ["G004", "LOG001", "LOG002"]

    def _get_expertise_level(self) -> str:
        return "intermediate"

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="logging_fixes",
                description="Fix logging configuration and usage",
                confidence_multiplier=1.2,
                priority=1,
            ),
            FixStrategy(
                name="log_levels",
                description="Improve log level usage",
                confidence_multiplier=1.0,
                priority=2,
            ),
        ]

    def get_system_prompt(self) -> str:
        return """You are a LOGGING SPECIALIST AI. Your expertise is fixing logging-related issues.

CORE PRINCIPLES:
1. Fix logging configuration issues
2. Improve log level usage
3. Ensure proper logging setup
4. Maintain logging functionality
5. Follow logging best practices

COMMON FIXES:
• Fix logging configuration problems
• Improve log level selection
• Ensure proper logger setup
• Fix logging format issues

Focus on making logging more effective and maintainable."""
