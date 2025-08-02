"""
Specialized AI Agents for Linting Issue Types

This module provides specialized AI agents that are experts in fixing specific
types of linting issues, with tailored prompts and strategies for each issue type.
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of specialized agents for different linting issue categories."""

    LINE_LENGTH = "line_length_agent"
    IMPORT_OPTIMIZER = "import_agent"
    VARIABLE_CLEANER = "variable_agent"
    EXCEPTION_HANDLER = "exception_agent"
    STYLE_FIXER = "style_agent"
    GENERAL_FIXER = "general_agent"


class FixStrategy(BaseModel):
    """Strategy for fixing issues with specific approaches."""

    name: str
    description: str
    confidence_multiplier: float = 1.0
    max_retries: int = 3
    requires_context: bool = True


class SpecializedAgent(ABC):
    """Base class for specialized AI agents."""

    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.issue_codes = self._get_supported_issue_codes()
        self.success_rates: dict[str, float] = {}  # Track success rates per issue type
        self.fix_strategies = self._define_fix_strategies()

    @abstractmethod
    def _get_supported_issue_codes(self) -> list[str]:
        """Get the list of issue codes this agent can handle."""

    @abstractmethod
    def _define_fix_strategies(self) -> list[FixStrategy]:
        """Define the fix strategies this agent uses."""

    @abstractmethod
    def get_system_prompt(self, issues: list[dict[str, Any]]) -> str:
        """Get the specialized system prompt for this agent."""

    @abstractmethod
    def get_user_prompt(self, file_content: str, issues: list[dict[str, Any]]) -> str:
        """Get the specialized user prompt for this agent."""

    def can_handle(self, issue_code: str) -> bool:
        """Check if this agent can handle the given issue code."""
        return any(issue_code.startswith(code) for code in self.issue_codes)

    def get_confidence_score(self, issue_code: str) -> float:
        """Get confidence score for handling this issue type."""
        if not self.can_handle(issue_code):
            return 0.0

        # Base confidence from historical success rates
        base_confidence = self.success_rates.get(issue_code, 0.7)

        # Agent-specific confidence adjustments
        return min(0.95, base_confidence * self._get_agent_confidence_multiplier(issue_code))

    def _get_agent_confidence_multiplier(self, issue_code: str) -> float:
        """Get agent-specific confidence multiplier."""
        return 1.0  # Override in subclasses


class LineLengthAgent(SpecializedAgent):
    """Specialized agent for fixing line length issues (E501)."""

    def __init__(self):
        super().__init__(AgentType.LINE_LENGTH)

    def _get_supported_issue_codes(self) -> list[str]:
        return ["E501"]

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="smart_line_break",
                description="Break long lines at logical points (operators, commas, etc.)",
                confidence_multiplier=1.2,
            ),
            FixStrategy(
                name="parentheses_wrapping",
                description="Use parentheses for implicit line continuation",
                confidence_multiplier=1.1,
            ),
            FixStrategy(
                name="variable_extraction",
                description="Extract complex expressions to variables",
                confidence_multiplier=0.9,
            ),
        ]

    def get_system_prompt(self, issues: list[dict[str, Any]]) -> str:
        return """You are a LINE LENGTH SPECIALIST AI. Your expertise is fixing E501 line-too-long errors.

CORE PRINCIPLES:
1. Break lines at logical points (after operators, commas, parentheses)
2. Maintain code readability and logical flow
3. Use Python's implicit line continuation (parentheses) when possible
4. Preserve original functionality exactly
5. Follow PEP 8 line breaking guidelines

PREFERRED STRATEGIES:
• Break after operators (+, -, ==, and, or, etc.)
• Break after commas in function calls/definitions
• Use parentheses for implicit continuation
• Break long string concatenations
• Extract complex expressions to variables when needed

AVOID:
• Breaking in the middle of words or strings
• Creating less readable code
• Changing logic or functionality
• Using backslash continuation (\\) unless absolutely necessary

Focus on making clean, readable fixes that improve code quality."""

    def get_user_prompt(self, file_content: str, issues: list[dict[str, Any]]) -> str:
        issue_lines = [f"Line {issue['line_number']}: {issue['message']}" for issue in issues]

        return f"""Fix the following line length issues in this Python code:

ISSUES TO FIX:
{chr(10).join(issue_lines)}

CODE:
```python
{file_content}
```

Please fix ONLY the line length issues. Return the corrected code maintaining exact functionality."""

    def _get_agent_confidence_multiplier(self, issue_code: str) -> float:
        return 1.3  # High confidence for line length fixes


class ImportOptimizerAgent(SpecializedAgent):
    """Specialized agent for fixing import-related issues (F401, F811)."""

    def __init__(self):
        super().__init__(AgentType.IMPORT_OPTIMIZER)

    def _get_supported_issue_codes(self) -> list[str]:
        return ["F401", "F811", "F405"]

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="safe_removal",
                description="Remove unused imports after verifying they're truly unused",
                confidence_multiplier=1.3,
                requires_context=True,
            ),
            FixStrategy(
                name="conditional_import",
                description="Move imports inside functions if used conditionally",
                confidence_multiplier=0.9,
            ),
            FixStrategy(
                name="import_grouping",
                description="Reorganize imports to fix redefinition issues",
                confidence_multiplier=1.1,
            ),
        ]

    def get_system_prompt(self, issues: list[dict[str, Any]]) -> str:
        return """You are an IMPORT OPTIMIZATION SPECIALIST AI. Your expertise is fixing import-related issues.

CORE PRINCIPLES:
1. Remove unused imports (F401) safely
2. Fix import redefinitions (F811)
3. Organize imports following PEP 8
4. Preserve functionality - never remove imports that ARE actually used
5. Consider dynamic usage (getattr, eval, string references)

ANALYSIS STEPS:
1. Scan entire file for ALL usage of the imported name
2. Check for indirect usage (getattr, locals(), globals())
3. Look for usage in strings, comments, or docstrings
4. Verify the import is truly unused before removing

IMPORT ORGANIZATION:
1. Standard library imports
2. Third-party imports
3. Local application imports
4. Separated by blank lines

BE EXTREMELY CAREFUL: Only remove imports you are 100% certain are unused."""

    def get_user_prompt(self, file_content: str, issues: list[dict[str, Any]]) -> str:
        issue_details = [f"Line {issue['line_number']}: {issue['message']}" for issue in issues]

        return f"""Fix the following import issues in this Python code:

IMPORT ISSUES:
{chr(10).join(issue_details)}

CODE:
```python
{file_content}
```

CRITICAL: Before removing any import, scan the ENTIRE file to ensure it's not used anywhere.
Check for usage in:
- Direct references
- getattr() calls
- String formatting
- Dynamic imports
- Type hints
- Comments that might indicate future use

Only remove imports you are absolutely certain are unused."""

    def _get_agent_confidence_multiplier(self, issue_code: str) -> float:
        return 1.4  # Very high confidence for import fixes


class VariableCleanerAgent(SpecializedAgent):
    """Specialized agent for fixing unused variable issues (F841, F821)."""

    def __init__(self):
        super().__init__(AgentType.VARIABLE_CLEANER)

    def _get_supported_issue_codes(self) -> list[str]:
        return ["F841", "F821", "F823"]

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="underscore_prefix",
                description="Add underscore prefix to indicate intentionally unused",
                confidence_multiplier=1.2,
            ),
            FixStrategy(
                name="variable_removal",
                description="Remove assignment if variable is completely unused",
                confidence_multiplier=1.1,
            ),
            FixStrategy(
                name="use_variable",
                description="Add meaningful usage of the variable",
                confidence_multiplier=0.8,
            ),
        ]

    def get_system_prompt(self, issues: list[dict[str, Any]]) -> str:
        return """You are a VARIABLE CLEANUP SPECIALIST AI. Your expertise is fixing unused variable issues.

CORE PRINCIPLES:
1. Fix F841 (assigned but never used) variables
2. Fix F821 (undefined name) variables
3. Preserve side effects of assignments
4. Choose the most appropriate fix strategy

FIX STRATEGIES (in order of preference):
1. UNDERSCORE PREFIX: If variable might be used later or serves documentation purpose
   - Change `result = func()` to `_result = func()`
2. REMOVE ASSIGNMENT: If the assignment serves no purpose
   - Change `x = 5` to just remove the line (if no side effects)
3. MEANINGFUL USAGE: If the variable should be used
   - Add appropriate usage like logging, return, or assertion

CRITICAL CONSIDERATIONS:
- Preserve function call side effects
- Don't remove assignments that have side effects
- Consider if variable is used for future development
- Maintain code readability and intent"""

    def get_user_prompt(self, file_content: str, issues: list[dict[str, Any]]) -> str:
        variable_issues = [f"Line {issue['line_number']}: {issue['message']}" for issue in issues]

        return f"""Fix the following unused variable issues in this Python code:

VARIABLE ISSUES:
{chr(10).join(variable_issues)}

CODE:
```python
{file_content}
```

For each unused variable, choose the best strategy:
1. Add underscore prefix if variable serves documentation purpose
2. Remove assignment if it has no side effects
3. Add meaningful usage if the variable should be used

Preserve all side effects and maintain code functionality."""

    def _get_agent_confidence_multiplier(self, issue_code: str) -> float:
        return 1.2  # Good confidence for variable fixes


class ExceptionHandlerAgent(SpecializedAgent):
    """Specialized agent for fixing exception handling issues (E722, B001)."""

    def __init__(self):
        super().__init__(AgentType.EXCEPTION_HANDLER)

    def _get_supported_issue_codes(self) -> list[str]:
        return ["E722", "B001", "B014"]

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="specific_exception",
                description="Replace bare except with specific exception types",
                confidence_multiplier=1.1,
            ),
            FixStrategy(
                name="exception_as_exception",
                description="Use 'except Exception:' for broad catching",
                confidence_multiplier=1.2,
            ),
            FixStrategy(
                name="multiple_exceptions",
                description="Catch multiple specific exception types",
                confidence_multiplier=0.9,
            ),
        ]

    def get_system_prompt(self, issues: list[dict[str, Any]]) -> str:
        return """You are an EXCEPTION HANDLING SPECIALIST AI. Your expertise is fixing exception handling issues.

CORE PRINCIPLES:
1. Never use bare 'except:' clauses
2. Catch specific exceptions when possible
3. Use 'except Exception:' for broad catching
4. Preserve error handling behavior
5. Follow Python exception handling best practices

EXCEPTION HIERARCHY KNOWLEDGE:
- BaseException (system exit, keyboard interrupt)
  - Exception (all normal exceptions)
    - ValueError, TypeError, AttributeError, etc.

FIX STRATEGIES:
1. SPECIFIC EXCEPTIONS: If you can determine likely exceptions
   - `except (ValueError, TypeError):`
2. GENERAL EXCEPTION: For broad error catching
   - `except Exception:` (not bare except)
3. PRESERVE BEHAVIOR: Maintain the same error handling logic

AVOID catching BaseException unless specifically needed for system events."""

    def get_user_prompt(self, file_content: str, issues: list[dict[str, Any]]) -> str:
        exception_issues = [f"Line {issue['line_number']}: {issue['message']}" for issue in issues]

        return f"""Fix the following exception handling issues in this Python code:

EXCEPTION ISSUES:
{chr(10).join(exception_issues)}

CODE:
```python
{file_content}
```

Replace bare 'except:' clauses with appropriate exception handling:
- Use specific exceptions if you can determine the likely error types
- Use 'except Exception:' for general error catching
- Preserve the existing error handling behavior
- Never catch BaseException unless specifically needed"""

    def _get_agent_confidence_multiplier(self, issue_code: str) -> float:
        return 1.1  # Good confidence for exception fixes


class StyleFixerAgent(SpecializedAgent):
    """Specialized agent for fixing style and formatting issues (F541, E741)."""

    def __init__(self):
        super().__init__(AgentType.STYLE_FIXER)

    def _get_supported_issue_codes(self) -> list[str]:
        return ["F541", "E741", "E742", "E743"]

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="meaningful_names",
                description="Replace ambiguous variable names with descriptive ones",
                confidence_multiplier=0.8,
            ),
            FixStrategy(
                name="f_string_fix",
                description="Fix f-string formatting issues",
                confidence_multiplier=1.2,
            ),
        ]

    def get_system_prompt(self, issues: list[dict[str, Any]]) -> str:
        return """You are a CODE STYLE SPECIALIST AI. Your expertise is fixing style and formatting issues.

CORE PRINCIPLES:
1. Fix f-string formatting issues (F541)
2. Replace ambiguous variable names (E741, E742, E743)
3. Maintain code functionality while improving readability
4. Follow Python naming conventions

F-STRING FIXES:
- Add missing variables to f-strings
- Fix empty f-strings
- Ensure all placeholders have corresponding variables

VARIABLE NAMING:
- Replace single letters (l, O, I) with descriptive names
- Use meaningful names that indicate purpose
- Follow snake_case convention
- Consider context and variable usage

BE CONSERVATIVE: Only make changes that clearly improve code quality."""

    def get_user_prompt(self, file_content: str, issues: list[dict[str, Any]]) -> str:
        style_issues = [f"Line {issue['line_number']}: {issue['message']}" for issue in issues]

        return f"""Fix the following style issues in this Python code:

STYLE ISSUES:
{chr(10).join(style_issues)}

CODE:
```python
{file_content}
```

Fix the issues while maintaining exact functionality:
- For f-string issues: add missing variables or fix formatting
- For variable naming: use descriptive names that indicate purpose
- Preserve all logic and behavior"""

    def _get_agent_confidence_multiplier(self, issue_code: str) -> float:
        if issue_code.startswith("F541"):
            return 1.3  # High confidence for f-string fixes
        return 0.9  # Lower confidence for style changes


class GeneralFixerAgent(SpecializedAgent):
    """General-purpose agent for miscellaneous linting issues."""

    def __init__(self):
        super().__init__(AgentType.GENERAL_FIXER)

    def _get_supported_issue_codes(self) -> list[str]:
        return ["*"]  # Handles all issues as fallback

    def _define_fix_strategies(self) -> list[FixStrategy]:
        return [
            FixStrategy(
                name="general_fix",
                description="Apply general linting fixes based on error description",
                confidence_multiplier=0.7,
            )
        ]

    def get_system_prompt(self, issues: list[dict[str, Any]]) -> str:
        return """You are a GENERAL PURPOSE LINTING AI. You handle miscellaneous Python linting issues.

CORE PRINCIPLES:
1. Fix any Python linting issue not handled by specialists
2. Preserve exact functionality
3. Follow Python best practices
4. Make minimal, targeted changes
5. Be conservative with changes

APPROACH:
1. Analyze the specific error message
2. Apply the minimal fix needed
3. Preserve code behavior exactly
4. Follow PEP 8 guidelines
5. Maintain readability

You are the fallback agent, so be extra careful and conservative."""

    def get_user_prompt(self, file_content: str, issues: list[dict[str, Any]]) -> str:
        general_issues = [
            f"Line {issue['line_number']}: {issue['error_code']} - {issue['message']}"
            for issue in issues
        ]

        return f"""Fix the following linting issues in this Python code:

ISSUES TO FIX:
{chr(10).join(general_issues)}

CODE:
```python
{file_content}
```

Apply minimal fixes to resolve each issue while preserving exact functionality."""

    def _get_agent_confidence_multiplier(self, issue_code: str) -> float:
        return 0.8  # Conservative confidence for general fixes


class AgentManager:
    """Manages the specialized AI agents and selects the best agent for each issue."""

    def __init__(self):
        self.agents = {
            AgentType.LINE_LENGTH: LineLengthAgent(),
            AgentType.IMPORT_OPTIMIZER: ImportOptimizerAgent(),
            AgentType.VARIABLE_CLEANER: VariableCleanerAgent(),
            AgentType.EXCEPTION_HANDLER: ExceptionHandlerAgent(),
            AgentType.STYLE_FIXER: StyleFixerAgent(),
            AgentType.GENERAL_FIXER: GeneralFixerAgent(),
        }

        # Track agent performance
        self.agent_stats = {
            agent_type: {"attempts": 0, "successes": 0} for agent_type in self.agents
        }

    def select_agent_for_issues(self, issues: list[dict[str, Any]]) -> SpecializedAgent:
        """Select the best agent to handle a batch of issues."""
        if not issues:
            return self.agents[AgentType.GENERAL_FIXER]

        # Count issues by type to find the dominant type
        issue_type_counts: dict[AgentType, int] = {}
        for issue in issues:
            error_code = issue.get("error_code", "")
            for agent_type, agent in self.agents.items():
                if agent.can_handle(error_code):
                    issue_type_counts[agent_type] = issue_type_counts.get(agent_type, 0) + 1
                    break

        if not issue_type_counts:
            return self.agents[AgentType.GENERAL_FIXER]

        # Select agent with most matching issues
        best_agent_type = max(issue_type_counts, key=lambda k: issue_type_counts[k])
        return self.agents[best_agent_type]

    def get_agent_by_type(self, agent_type: AgentType) -> SpecializedAgent:
        """Get a specific agent by type."""
        return self.agents[agent_type]

    def record_agent_result(self, agent_type: AgentType, success: bool) -> None:
        """Record the result of an agent's attempt."""
        self.agent_stats[agent_type]["attempts"] += 1
        if success:
            self.agent_stats[agent_type]["successes"] += 1

    def get_agent_success_rate(self, agent_type: AgentType) -> float:
        """Get the success rate for a specific agent."""
        stats = self.agent_stats[agent_type]
        if stats["attempts"] == 0:
            return 0.0
        return stats["successes"] / stats["attempts"]

    def get_all_agent_stats(self) -> dict[str, dict[str, Any]]:
        """Get performance statistics for all agents."""
        return {
            agent_type.value: {
                "attempts": stats["attempts"],
                "successes": stats["successes"],
                "success_rate": self.get_agent_success_rate(agent_type),
                "supported_codes": agent.issue_codes,
            }
            for agent_type, (stats, agent) in zip(
                self.agent_stats.keys(),
                zip(self.agent_stats.values(), self.agents.values(), strict=False),
                strict=False,
            )
        }


# Global agent manager instance
agent_manager = AgentManager()
