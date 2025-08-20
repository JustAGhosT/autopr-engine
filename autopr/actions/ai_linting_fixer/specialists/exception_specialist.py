"""
Exception Specialist for fixing exception handling issues (E722, B001).
"""

from .base_specialist import AgentType, BaseSpecialist, FixStrategy


class ExceptionSpecialist(BaseSpecialist):
    """Specialized agent for fixing exception handling issues (E722, B001)."""

    def __init__(self):
        super().__init__(AgentType.EXCEPTION_HANDLER)

    def _get_supported_codes(self) -> list[str]:
        return ["E722", "B001", "TRY401", "TRY002", "TRY003"]

    def _get_expertise_level(self) -> str:
        return "advanced"

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="specific_exceptions",
                description="Replace bare except with specific exception types",
                confidence_multiplier=1.3,
                priority=1,
            ),
            FixStrategy(
                name="exception_handling",
                description="Improve exception handling patterns",
                confidence_multiplier=1.1,
                priority=2,
            ),
            FixStrategy(
                name="try_optimization",
                description="Optimize try-except blocks",
                confidence_multiplier=0.9,
                priority=3,
            ),
        ]

    def get_system_prompt(self) -> str:
        return """You are an EXCEPTION HANDLING SPECIALIST AI. Your expertise is fixing exception-related issues.

CORE PRINCIPLES:
1. Replace bare except clauses with specific exception types
2. Improve exception handling patterns
3. Maintain proper error handling logic
4. Preserve intended error handling behavior
5. Follow Python exception handling best practices

COMMON FIXES:
• Replace `except:` with `except Exception:` or specific exception types
• Add proper exception handling for specific error conditions
• Optimize try-except block structure
• Ensure proper error propagation when needed

BE CAREFUL: Exception handling is critical for program stability."""
