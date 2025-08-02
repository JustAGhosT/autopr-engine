from datetime import datetime
import logging
import re
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .messaging import AxoloMessaging
    from .models import AxoloPRChannel


class AxoloCommandHandler:
    """Handles Slack command processing for Axolo integration."""

    def __init__(
        self, messaging: "AxoloMessaging", active_channels: dict[str, "AxoloPRChannel"]
    ) -> None:
        self.messaging = messaging
        self.active_channels = active_channels

    async def handle_analyze_command(self, command_data: dict[str, Any]) -> None:
        """Handle /autopr-analyze command"""

        channel_id = command_data["channel_id"]
        command_data["user_id"]
        text = command_data.get("text", "")

        # Extract PR URL if provided, otherwise use current channel's PR
        pr_url = text.strip() or None

        if not pr_url:
            # Try to get PR from current channel context
            pr_data = await self._get_pr_from_channel_context(channel_id)
        else:
            # Parse PR from URL
            pr_data = await self._parse_pr_from_url(pr_url)

        if not pr_data:
            await self.messaging.post_error_response(
                channel_id,
                "Could not find PR to analyze. Please provide a PR URL or use this command in a PR channel.",
            )
            return

        # Trigger AutoPR analysis
        from autopr.actions.pr_review_analyzer import PRReviewAnalyzer

        analyzer = PRReviewAnalyzer()

        # Post initial response
        await self.messaging.post_slack_response(
            channel_id, f"🤖 Starting AutoPR analysis for PR #{pr_data['pr_number']}..."
        )

        try:
            # Run analysis
            await analyzer.analyze_pr_review(
                {
                    "pr_number": pr_data["pr_number"],
                    "repository": pr_data["repository"],
                    "review_data": await self._gather_review_data(pr_data["pr_number"]),
                }
            )

            # Post results (this would be handled by the main integration)
            logger.info(f"Analysis completed for PR #{pr_data['pr_number']}")

        except Exception as e:
            try:
                from slack_sdk.errors import SlackApiError  # type: ignore[import-not-found]

                if isinstance(e, SlackApiError):
                    logger.exception(f"Slack API error: {e!s}")
                    await self.messaging.post_error_response(channel_id, f"Slack API error: {e!s}")
            except ImportError:
                logger.exception(f"Analysis command failed: {e!s}")
                await self.messaging.post_error_response(channel_id, f"Analysis failed: {e!s}")

    async def handle_status_command(self, command_data: dict[str, Any]) -> None:
        """Handle /autopr-status command"""

        channel_id = command_data["channel_id"]
        command_data["user_id"]

        # Get PR from channel context
        pr_data = await self._get_pr_from_channel_context(channel_id)

        if not pr_data:
            await self.messaging.post_error_response(
                channel_id, "Could not find PR for this channel."
            )
            return

        # Get analysis status
        status = await self._get_pr_analysis_status(pr_data["pr_number"])

        # Format status message
        status_message = {
            "channel": channel_id,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 PR #{pr_data['pr_number']} Status",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Status:*\n{status.get('status', 'Unknown')}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*Last Analyzed:*\n{status.get('last_analyzed', 'Never')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Issues Found:*\n{status.get('issues_found', 0)}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Confidence:*\n{status.get('confidence_score', 0):.0%}",
                        },
                    ],
                },
            ],
        }

        await self.messaging.post_slack_message(status_message)

    async def handle_assign_ai_command(self, command_data: dict[str, Any]) -> None:
        """Handle /autopr-assign-ai command"""

        channel_id = command_data["channel_id"]
        command_data["user_id"]
        text = command_data.get("text", "")

        # Parse AI tool from command text
        ai_tool = text.strip().lower() if text.strip() else "autopr"

        if ai_tool not in {"autopr", "copilot", "coderabbit"}:
            await self.messaging.post_error_response(
                channel_id,
                f"Unknown AI tool: {ai_tool}. Available tools: autopr, copilot, coderabbit",
            )
            return

        # Get PR from channel context
        pr_data = await self._get_pr_from_channel_context(channel_id)

        if not pr_data:
            await self.messaging.post_error_response(
                channel_id, "Could not find PR for this channel."
            )
            return

        # Assign AI tool
        await self._assign_ai_tool_to_pr(pr_data["pr_number"], ai_tool)

        await self.messaging.post_slack_response(
            channel_id, f"✅ {ai_tool.title()} assigned to PR #{pr_data['pr_number']}"
        )

    async def _get_pr_from_channel_context(self, channel_id: str) -> dict[str, Any] | None:
        """Get PR data from channel context."""
        # Look up the PR associated with this channel
        for channel in self.active_channels.values():
            if channel.channel_id == channel_id:
                return {
                    "pr_number": channel.pr_number,
                    "repository": channel.repository,
                    "channel_id": channel_id,
                }
        return None

    async def _parse_pr_from_url(self, pr_url: str) -> dict[str, Any] | None:
        """Parse PR data from GitHub URL."""
        # Match GitHub PR URL pattern
        pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.match(pattern, pr_url)

        if match:
            owner, repo, pr_number = match.groups()
            return {"pr_number": int(pr_number), "repository": f"{owner}/{repo}", "url": pr_url}
        return None

    async def _gather_review_data(self, pr_number: int) -> dict[str, Any]:
        """Gather review data for PR analysis."""
        # This would typically fetch data from GitHub API
        return {
            "pr_number": pr_number,
            "files_changed": [],
            "comments": [],
            "reviews": [],
            "commits": [],
        }

    async def _get_pr_analysis_status(self, pr_number: int) -> dict[str, Any]:
        """Get current analysis status for a PR."""
        # This would check the status of ongoing or completed analyses
        return {
            "status": "completed",
            "last_analyzed": datetime.now().isoformat(),
            "issues_found": 0,
            "confidence_score": 0.85,
        }

    async def _assign_ai_tool_to_pr(self, pr_number: int, ai_tool: str) -> None:
        """Assign an AI tool to a PR."""
        # This would handle the actual assignment logic
        logger.info(f"Assigning {ai_tool} to PR #{pr_number}")
