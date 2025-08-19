"""
AI Agent Manager Module

This module manages AI agents and their specializations for different types of linting issues.
"""

from collections import Counter
import logging
from typing import Any

from autopr.actions.llm.manager import LLMProviderManager

from .models import LintingIssue

logger = logging.getLogger(__name__)


class AIAgentManager:
    """Manages AI agents and their specializations."""

    def __init__(self, llm_manager: LLMProviderManager, performance_tracker=None):
        """Initialize the AI agent manager."""
        self.llm_manager = llm_manager
        self.performance_tracker = performance_tracker

        # Agent specialization mapping
        self.agent_specializations = {
            "line_length_agent": ["E501"],  # Line length specialist
            "import_agent": ["F401", "F811"],  # Import specialist
            "variable_agent": ["F841", "F821"],  # Variable specialist
            "exception_agent": ["E722", "B001"],  # Exception handling specialist
            "style_agent": ["F541", "E741"],  # Style and naming specialist
            "general_agent": ["*"],  # Fallback for everything else
        }

    def select_agent_for_issues(self, issues: list[LintingIssue]) -> str:
        """Select the most appropriate agent for the given issues."""
        if not issues:
            return "general_agent"

        # Count issues by type
        issue_counts: Counter[str] = Counter()
        for issue in issues:
            error_code = issue.error_code
            issue_counts[error_code] += 1

        # Find the best agent based on issue types
        best_agent = "general_agent"
        best_score = 0

        for agent_name, supported_codes in self.agent_specializations.items():
            score = 0
            for code in supported_codes:
                if code == "*":  # Wildcard agent
                    score += len(issue_counts)
                elif code in issue_counts:
                    score += issue_counts[code]

            if score > best_score:
                best_score = score
                best_agent = agent_name

        logger.debug("Selected agent '%s' for %d issues", best_agent, len(issues))
        return best_agent

    def get_specialized_system_prompt(self, agent_type: str, issues: list[LintingIssue]) -> str:
        """Get a specialized system prompt for the given agent type."""
        base_prompt = self._get_base_system_prompt()

        # Add agent-specific instructions
        agent_instructions = self._get_agent_instructions(agent_type, issues)

        return f"{base_prompt}\n\n{agent_instructions}"

    def get_system_prompt(self) -> str:
        """Get the base system prompt for AI linting fixer."""
        return """You are an expert Python code reviewer and fixer. Your task is to fix linting issues in Python code while maintaining code quality and functionality.

Key responsibilities:
1. Fix linting issues identified by flake8
2. Maintain code readability and style
3. Preserve existing functionality
4. Follow PEP 8 style guidelines
5. Ensure syntax correctness

When fixing code:
- Only make necessary changes to fix the specific linting issue
- Maintain the original logic and behavior
- Use clear, readable variable names
- Follow Python best practices
- Ensure the fixed code is syntactically correct

Provide your response in the following JSON format:
{
    "success": true/false,
    "fixed_code": "the complete fixed code",
    "changes_made": ["list of specific changes made"],
    "confidence": 0.0-1.0,
    "explanation": "brief explanation of the fix"
}"""

    def get_enhanced_system_prompt(self) -> str:
        """Get an enhanced system prompt for better JSON generation."""
        return """You are an expert Python code fixer. Your task is to fix linting issues in Python code.

CRITICAL: You must respond with valid JSON only. Follow these rules:
1. Use double quotes for all strings
2. Escape any quotes within strings with backslash: \"
3. Do not include any text before or after the JSON
4. Ensure all strings are properly closed
5. Use proper JSON syntax with no trailing commas
6. In the "fixed_code" field, provide ONLY the fixed code, not the entire file
7. Focus on the specific lines that need fixing

Response format (JSON only):
{
    "success": true/false,
    "fixed_code": "only the fixed code lines",
    "explanation": "brief explanation of what was fixed",
    "confidence": 0.0-1.0,
    "changes_made": ["list", "of", "specific", "changes"]
}

If you cannot fix the issue, respond with:
{
    "success": false,
    "error": "explanation of why it cannot be fixed",
    "confidence": 0.0
}

IMPORTANT: Never include markdown formatting, code blocks, or any text outside the JSON."""

    def get_user_prompt(self, file_path: str, content: str, issues: list[LintingIssue]) -> str:
        """Generate a user prompt for fixing the given issues."""
        prompt = f"Please fix the following linting issues in the Python file '{file_path}':\n\n"

        # Add file content
        prompt += f"File content:\n```python\n{content}\n```\n\n"

        # Add specific issues
        prompt += "Linting issues to fix:\n"
        for i, issue in enumerate(issues, 1):
            prompt += f"{i}. Line {issue.line_number}: {issue.error_code} - {issue.message}\n"
            if issue.line_content:
                prompt += f"   Line content: {issue.line_content}\n"

        prompt += "\nPlease provide the complete fixed code that resolves all these issues."
        return prompt

    def parse_ai_response(self, content: str) -> dict[str, Any]:
        """Parse the AI response and extract the fix information."""
        try:
            # Try to extract JSON from the response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                logger.warning("No JSON found in AI response")
                return {
                    "success": False,
                    "error": "No JSON response found",
                    "raw_response": (content[:200] + "..." if len(content) > 200 else content),
                }

            json_content = content[json_start:json_end]

            try:
                import json

                parsed = json.loads(json_content)

                # Validate required fields
                if "success" not in parsed:
                    parsed["success"] = False
                    parsed["error"] = "Missing 'success' field in response"

                if "fixed_code" not in parsed and parsed.get("success", False):
                    parsed["success"] = False
                    parsed["error"] = "Missing 'fixed_code' field in successful response"

                return parsed

            except json.JSONDecodeError as e:
                logger.warning("Failed to parse AI response as JSON: %s", e)

                # Try to extract useful information from the response
                lines = content.split("\n")
                fixed_code = []
                in_code_block = False
                explanation = ""

                for line in lines:
                    if "```" in line:
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        fixed_code.append(line)
                    elif line.strip() and not line.startswith("{") and not line.startswith("}"):
                        explanation += line + "\n"

                if fixed_code:
                    return {
                        "success": True,
                        "fixed_code": "\n".join(fixed_code),
                        "explanation": explanation.strip(),
                        "confidence": 0.7,  # Default confidence for parsed responses
                        "changes_made": ["Extracted code from response"],
                        "parsing_warning": f"JSON parsing failed: {e}",
                    }
                return {
                    "success": False,
                    "error": f"JSON parsing failed: {e}",
                    "raw_response": (content[:300] + "..." if len(content) > 300 else content),
                    "suggestion": "AI response format needs improvement",
                }

        except Exception as exc:
            logger.exception("Unexpected error parsing AI response")
            return {
                "success": False,
                "error": f"Parsing error: {exc}",
                "raw_response": (content[:200] + "..." if len(content) > 200 else content),
            }

    def calculate_confidence_score(
        self,
        ai_response: dict[str, Any],
        issues: list[LintingIssue],
        original_content: str,
        fixed_content: str,
    ) -> float:
        """Calculate a comprehensive confidence score for the AI fix."""
        try:
            confidence = 0.3
            confidence = self._score_response_success(ai_response, confidence)
            confidence = self._score_ai_confidence(ai_response, confidence)
            confidence = self._score_change_size(original_content, fixed_content, confidence)
            confidence = self._score_explanation(ai_response, confidence)
            confidence = self._score_changes_list(ai_response, confidence)
            confidence = self._score_issue_complexity(issues, confidence)
            confidence = self._score_issue_types(issues, confidence)
            return max(0.0, min(confidence, 1.0))
        except Exception as exc:
            logger.debug("Error calculating confidence score: %s", exc)
            return 0.3

    def _score_response_success(self, ai_response: dict[str, Any], confidence: float) -> float:
        if ai_response.get("success"):
            confidence += 0.2
        return confidence

    def _score_ai_confidence(self, ai_response: dict[str, Any], confidence: float) -> float:
        if "confidence" in ai_response:
            response_confidence = ai_response["confidence"]
            if isinstance(response_confidence, (int, float)) and 0 <= response_confidence <= 1:
                confidence = confidence * 0.7 + response_confidence * 0.3
        return confidence

    def _score_change_size(
        self, original_content: str, fixed_content: str, confidence: float
    ) -> float:
        if original_content != fixed_content:
            confidence += 0.15
            change_ratio = len(fixed_content) / max(len(original_content), 1)
            if 0.8 <= change_ratio <= 1.2:
                confidence += 0.1
            elif change_ratio < 0.5 or change_ratio > 2.0:
                confidence -= 0.1
        return confidence

    def _score_explanation(self, ai_response: dict[str, Any], confidence: float) -> float:
        explanation = ai_response.get("explanation")
        if explanation:
            confidence += 0.1
            if len(explanation) > 50:
                confidence += 0.05
        return confidence

    def _score_changes_list(self, ai_response: dict[str, Any], confidence: float) -> float:
        changes = ai_response.get("changes_made")
        if changes:
            confidence += 0.1
            if len(changes) > 0:
                confidence += 0.05
        return confidence

    def _score_issue_complexity(self, issues: list[LintingIssue], confidence: float) -> float:
        if len(issues) == 1:
            confidence += 0.1
        elif len(issues) <= 3:
            confidence += 0.05
        elif len(issues) > 10:
            confidence -= 0.1
        return confidence

    def _score_issue_types(self, issues: list[LintingIssue], confidence: float) -> float:
        easy = {"E501", "F401", "W292", "W293"}
        medium = {"F841", "E722", "E401"}
        hard = {"B001", "E302", "E305"}
        for issue in issues:
            code = issue.error_code
            if code in easy:
                confidence += 0.05
            elif code in medium:
                confidence += 0.02
            elif code in hard:
                confidence -= 0.02
        return confidence

    def _get_base_system_prompt(self) -> str:
        """Get the base system prompt."""
        return self.get_system_prompt()

    def _get_agent_instructions(self, agent_type: str, issues: list[LintingIssue]) -> str:
        """Get agent-specific instructions."""
        instructions = {
            "line_length_agent": """
SPECIALIZATION: Line Length and Formatting Issues
Focus on:
- Breaking long lines appropriately
- Maintaining readability
- Using proper line continuation
- Following PEP 8 line length guidelines
- Preserving logical structure
""",
            "import_agent": """
SPECIALIZATION: Import and Module Issues
Focus on:
- Removing unused imports
- Organizing imports properly
- Fixing import order
- Handling circular imports
- Using appropriate import statements
""",
            "variable_agent": """
SPECIALIZATION: Variable and Assignment Issues
Focus on:
- Fixing unused variables
- Proper variable naming
- Assignment issues
- Scope problems
- Variable initialization
""",
            "exception_agent": """
SPECIALIZATION: Exception Handling Issues
Focus on:
- Proper exception handling
- Avoiding bare except clauses
- Using specific exception types
- Proper error handling patterns
- Exception safety
""",
            "style_agent": """
SPECIALIZATION: Code Style and Naming Issues
Focus on:
- Variable naming conventions
- Function naming
- Class naming
- Style consistency
- PEP 8 compliance
""",
            "general_agent": """
SPECIALIZATION: General Code Quality
Focus on:
- Overall code quality
- Best practices
- Readability improvements
- Performance considerations
- Maintainability
""",
        }

        return instructions.get(agent_type, instructions["general_agent"])

    def _extract_code_blocks(self, content: str) -> list[str]:
        """Extract code blocks from AI response."""
        import re

        # Look for code blocks marked with ```
        code_block_pattern = r"```(?:python)?\s*\n(.*?)\n```"
        matches = re.findall(code_block_pattern, content, re.DOTALL)

        if matches:
            return [match.strip() for match in matches]

        # Look for indented code blocks
        lines = content.split("\n")
        code_blocks = []
        current_block = []
        in_code_block = False

        for line in lines:
            if (
                line.strip().startswith("def ")
                or line.strip().startswith("class ")
                or line.strip().startswith("import ")
            ):
                in_code_block = True

            if in_code_block:
                current_block.append(line)
            elif current_block:
                code_blocks.append("\n".join(current_block))
                current_block = []

        if current_block:
            code_blocks.append("\n".join(current_block))

        return code_blocks
