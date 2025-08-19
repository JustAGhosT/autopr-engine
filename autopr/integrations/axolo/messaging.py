"""Message formatting and posting utilities for Axolo integration."""

import logging
from typing import Any

import aiohttp

from .config import AxoloConfig

logger = logging.getLogger(__name__)


class AxoloMessaging:
    """Handles message formatting and posting to Slack via Axolo."""

    def __init__(
        self, config: AxoloConfig, session: aiohttp.ClientSession | None = None
    ):
        self.config = config
        self.session = session

    def format_analysis_summary(self, analysis_result: dict[str, Any]) -> str:
        """Format analysis results into a readable summary."""
        summary_parts = []

        if analysis_result.get("platform_detected"):
            summary_parts.append(f"Platform: {analysis_result['platform_detected']}")

        if analysis_result.get("confidence_score"):
            summary_parts.append(
                f"Confidence: {analysis_result['confidence_score']:.0%}"
            )

        issues_count = len(analysis_result.get("issues_found", []))
        summary_parts.append(f"Issues Found: {issues_count}")

        return " | ".join(summary_parts)

    def create_issues_block(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """Create Slack block for displaying issues."""
        issues_text = []
        for issue in issues[:5]:  # Limit to first 5 issues
            severity = issue.get("severity", "unknown")
            title = issue.get("title", "Unknown issue")
            issues_text.append(f"• {severity.upper()}: {title}")

        if len(issues) > 5:
            issues_text.append(f"... and {len(issues) - 5} more issues")

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Issues Found:*\n" + "\n".join(issues_text),
            },
        }

    def create_next_steps_block(self, next_steps: list[str]) -> dict[str, Any]:
        """Create Slack block for displaying next steps."""
        steps_text = []
        for i, step in enumerate(next_steps[:3], 1):  # Limit to first 3 steps
            steps_text.append(f"{i}. {step}")

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Recommended Next Steps:*\n" + "\n".join(steps_text),
            },
        }

    async def post_slack_message(self, message: dict[str, Any]) -> None:
        """Post message to Slack via Axolo or direct API"""

        try:
            if self.session and self.config.slack_webhook:
                async with self.session.post(
                    self.config.slack_webhook, json=message
                ) as response:
                    if response.status != 200:
                        logger.error(
                            f"Failed to post Slack message - status: {response.status}"
                        )
        except Exception as e:
            logger.exception(f"Error posting Slack message: {e!s}")

    async def post_slack_response(self, channel_id: str, text: str) -> None:
        """Post simple text response to Slack"""

        message = {"channel": channel_id, "text": text}
        await self.post_slack_message(message)

    async def post_error_response(self, channel_id: str, error_text: str) -> None:
        """Post error response to Slack"""

        message = {"channel": channel_id, "text": f"❌ {error_text}"}
        await self.post_slack_message(message)
