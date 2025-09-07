"""
AI Agent Manager for AI Linting Fixer

Manages AI agents for different types of code fixes.
"""

import json
import logging
from typing import Any

from autopr.actions.ai_linting_fixer.detection import LintingIssue
from autopr.actions.ai_linting_fixer.models import \
    LintingIssue as ModelLintingIssue
from autopr.actions.ai_linting_fixer.specialists.base_specialist import \
    AgentType
from autopr.actions.ai_linting_fixer.specialists.specialist_manager import \
    SpecialistManager
from autopr.actions.llm.manager import ActionLLMProviderManager

logger = logging.getLogger(__name__)


def convert_detection_issues_to_model_issues(detection_issues: list[LintingIssue]) -> list[ModelLintingIssue]:
    """Convert a list of LintingIssues from detection module to models module."""
    return [
        ModelLintingIssue(
            file_path=issue.file_path,
            line_number=issue.line_number,
            column_number=issue.column_number,
            error_code=issue.error_code,
            message=issue.message,
            line_content=getattr(issue, 'line_content', ''),
            column=issue.column_number,
        )
        for issue in detection_issues
    ]


class AIAgentManager:
    """
    Manages AI agents and their specializations for linting issue resolution.

    This class provides a clean interface between the AI fixer and the modularized
    specialist system, handling agent selection, prompt generation, response parsing,
    and confidence scoring.
    """

    # Issue complexity classifications for confidence scoring
    EASY_ISSUES = {"E501", "F401", "W292", "W293", "F541", "UP006"}
    MEDIUM_ISSUES = {"F841", "E722", "E401", "TID252", "G004"}
    HARD_ISSUES = {"B001", "E302", "E305", "TRY401"}

    # Agent type mapping for backward compatibility
    AGENT_TYPE_MAP = {
        "line_length_agent": AgentType.LINE_LENGTH,
        "import_agent": AgentType.IMPORT_OPTIMIZER,
        "variable_agent": AgentType.VARIABLE_CLEANER,
        "exception_agent": AgentType.EXCEPTION_HANDLER,
        "style_agent": AgentType.STYLE_FIXER,
        "logging_agent": AgentType.LOGGING_SPECIALIST,
        "general_agent": AgentType.GENERAL_FIXER,
    }

    def __init__(self, llm_manager: ActionLLMProviderManager, performance_tracker=None):
        """
        Initialize the AI agent manager.

        Args:
            llm_manager: Manager for LLM providers
            performance_tracker: Optional performance tracking component
        """
        self.llm_manager = llm_manager
        self.performance_tracker = performance_tracker
        self.specialist_manager = SpecialistManager()

    def select_agent_for_issues(self, issues: list[LintingIssue]) -> str:
        """
        Select the most appropriate agent for the given issues.

        Args:
            issues: List of linting issues to be fixed

        Returns:
            Name of the selected specialist
        """
        if not issues:
            return "GeneralSpecialist"

        specialist = self.specialist_manager.get_specialist_for_issues(convert_detection_issues_to_model_issues(issues))
        logger.debug(
            "Selected specialist '%s' for %d issues", specialist.name, len(issues)
        )
        return specialist.name

    def get_specialized_system_prompt(
        self, agent_type: str, _issues: list[LintingIssue]
    ) -> str:
        """
        Get a specialized system prompt for the given agent type.

        Args:
            agent_type: String identifier for the agent type
            _issues: List of issues (used for context, prefixed with _ to indicate unused)

        Returns:
            Specialized system prompt for the agent
        """
        agent_enum = self.AGENT_TYPE_MAP.get(agent_type, AgentType.GENERAL_FIXER)
        specialist = self.specialist_manager.get_specialist_by_type(agent_enum)
        return specialist.get_system_prompt()

    def get_user_prompt(
        self, file_path: str, content: str, issues: list[LintingIssue]
    ) -> str:
        """
        Generate a user prompt for fixing the given issues.

        Args:
            file_path: Path to the file being fixed
            content: Current content of the file
            issues: List of issues to be fixed

        Returns:
            Specialized user prompt for the issues
        """
        specialist = self.specialist_manager.get_specialist_for_issues(convert_detection_issues_to_model_issues(issues))
        return specialist.get_user_prompt(file_path, content, convert_detection_issues_to_model_issues(issues))

    def parse_ai_response(self, content: str) -> dict[str, Any]:
        """
        Parse the AI response and extract the fix information.

        Args:
            content: Raw AI response content

        Returns:
            Parsed response dictionary with fix information
        """
        try:
            # First, try to extract JSON from the response
            parsed = self._extract_json_response(content)
            if parsed:
                return self._validate_parsed_response(parsed)

            # Fallback: try to extract code blocks
            return self._extract_code_blocks_fallback(content)

        except Exception as exc:
            logger.exception("Unexpected error parsing AI response")
            return self._create_error_response(f"Parsing error: {exc}", content)

    def calculate_confidence_score(
        self,
        ai_response: dict[str, Any],
        issues: list[LintingIssue],
        original_content: str,
        fixed_content: str,
    ) -> float:
        """
        Calculate a comprehensive confidence score for the AI fix.

        Args:
            ai_response: Parsed AI response
            issues: Original issues that were fixed
            original_content: Original file content
            fixed_content: Fixed file content

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            confidence = 0.3  # Base confidence

            # Score different aspects
            confidence = self._score_response_success(ai_response, confidence)
            confidence = self._score_ai_confidence(ai_response, confidence)
            confidence = self._score_change_size(
                original_content, fixed_content, confidence
            )
            confidence = self._score_explanation(ai_response, confidence)
            confidence = self._score_changes_list(ai_response, confidence)
            confidence = self._score_issue_complexity(issues, confidence)
            confidence = self._score_issue_types(issues, confidence)

            return max(0.0, min(confidence, 1.0))

        except Exception as exc:
            logger.debug("Error calculating confidence score: %s", exc)
            return 0.3

    def _extract_json_response(self, content: str) -> dict[str, Any] | None:
        """Extract JSON response from AI content."""
        json_start = content.find("{")
        json_end = content.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            logger.warning("No JSON found in AI response")
            return None

        json_content = content[json_start:json_end]

        try:
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse AI response as JSON: %s", e)
            return None

    def _validate_parsed_response(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize parsed response."""
        # Ensure required fields exist
        if "success" not in parsed:
            parsed["success"] = False
            parsed["error"] = "Missing 'success' field in response"

        if "fixed_code" not in parsed and parsed.get("success", False):
            parsed["success"] = False
            parsed["error"] = "Missing 'fixed_code' field in successful response"

        return parsed

    def _extract_code_blocks_fallback(self, content: str) -> dict[str, Any]:
        """Fallback method to extract code blocks when JSON parsing fails."""
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
                "confidence": 0.7,
                "changes_made": ["Extracted code from response"],
                "parsing_warning": "JSON parsing failed, used code block extraction",
            }

        return self._create_error_response("No code blocks found in response", content)

    def _create_error_response(self, error: str, content: str) -> dict[str, Any]:
        """Create a standardized error response."""
        return {
            "success": False,
            "error": error,
            "raw_response": content[:300] + "..." if len(content) > 300 else content,
        }

    def _score_response_success(
        self, ai_response: dict[str, Any], confidence: float
    ) -> float:
        """Score based on response success."""
        if ai_response.get("success"):
            confidence += 0.2
        return confidence

    def _score_ai_confidence(
        self, ai_response: dict[str, Any], confidence: float
    ) -> float:
        """Score based on AI's own confidence."""
        if "confidence" in ai_response:
            response_confidence = ai_response["confidence"]
            if (
                isinstance(response_confidence, int | float)
                and not isinstance(response_confidence, bool)
                and 0 <= response_confidence <= 1
            ):
                confidence = confidence * 0.7 + response_confidence * 0.3
        return confidence

    def _score_change_size(
        self, original_content: str, fixed_content: str, confidence: float
    ) -> float:
        """Score based on change size and ratio."""
        if original_content != fixed_content:
            confidence += 0.15
            change_ratio = len(fixed_content) / max(len(original_content), 1)
            if 0.8 <= change_ratio <= 1.2:
                confidence += 0.1
            elif change_ratio < 0.5 or change_ratio > 2.0:
                confidence -= 0.1
        return confidence

    def _score_explanation(
        self, ai_response: dict[str, Any], confidence: float
    ) -> float:
        """Score based on explanation quality."""
        explanation = ai_response.get("explanation")
        if explanation:
            confidence += 0.1
            if len(explanation) > 50:
                confidence += 0.05
        return confidence

    def _score_changes_list(
        self, ai_response: dict[str, Any], confidence: float
    ) -> float:
        """Score based on changes list quality."""
        changes = ai_response.get("changes_made")
        if changes:
            confidence += 0.1
            if len(changes) > 0:
                confidence += 0.05
        return confidence

    def _score_issue_complexity(
        self, issues: list[LintingIssue], confidence: float
    ) -> float:
        """Score based on issue complexity."""
        if len(issues) == 1:
            confidence += 0.1
        elif len(issues) <= 3:
            confidence += 0.05
        elif len(issues) > 10:
            confidence -= 0.1
        return confidence

    def _score_issue_types(
        self, issues: list[LintingIssue], confidence: float
    ) -> float:
        """Score based on issue types and their complexity."""
        for issue in issues:
            code = issue.error_code
            if code in self.EASY_ISSUES:
                confidence += 0.05
            elif code in self.MEDIUM_ISSUES:
                confidence += 0.02
            elif code in self.HARD_ISSUES:
                confidence -= 0.02
        return confidence

    def get_specialist_stats(self) -> dict[str, dict[str, Any]]:
        """Get performance statistics for all specialists."""
        return self.specialist_manager.get_specialist_stats()

    def record_specialist_result(
        self, agent_type: str, success: bool, confidence: float = 0.0
    ) -> None:
        """Record the result of a specialist's attempt."""
        agent_enum = self.AGENT_TYPE_MAP.get(agent_type, AgentType.GENERAL_FIXER)
        self.specialist_manager.record_specialist_result(
            agent_enum, success, confidence
        )
