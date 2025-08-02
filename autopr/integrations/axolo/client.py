"""Main Axolo integration client."""

from datetime import datetime
import logging
import os
from typing import Any

import aiohttp

from .commands import AxoloCommandHandler
from .config import AxoloConfig
from .messaging import AxoloMessaging
from .models import AxoloPRChannel
from .reminders import AxoloReminderService

logger = logging.getLogger(__name__)


class AxoloIntegration:
    """
    Primary communication integration using Axolo for GitHub ↔ Slack

    Features:
    - Ephemeral PR channels (1 PR = 1 Channel)
    - Bi-directional GitHub/Slack sync
    - AI tool integration and mentions
    - Custom AutoPR commands
    - Smart reminder system
    """

    def __init__(self, config: dict[str, Any] | AxoloConfig | None = None) -> None:
        """Initialize Axolo integration."""
        if config is None:
            config = {}

        if isinstance(config, dict):
            self.config = AxoloConfig(**config)
        else:
            self.config = config

        self.active_channels: dict[str, AxoloPRChannel] = {}
        self.session: aiohttp.ClientSession | None = None
        self._initialized: bool = False

        # Integration clients
        self.github_client: Any | None = None
        self.slack_client: Any | None = None
        self.linear_client: Any | None = None

        # Component modules
        self.messaging: AxoloMessaging | None = None
        self.command_handler: AxoloCommandHandler | None = None
        self.reminder_service: AxoloReminderService | None = None

    async def initialize(self) -> None:
        """Initialize the integration."""
        if self._initialized:
            return

        self.session = aiohttp.ClientSession()

        # Initialize component modules
        self.messaging = AxoloMessaging(self.config, self.session)
        self.command_handler = AxoloCommandHandler(self.messaging, self.active_channels)
        self.reminder_service = AxoloReminderService(self.config, self.messaging)

        await self._setup_reminder_schedules()
        await self._initialize_clients()
        self._initialized = True

    async def close(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
        self._initialized = False

    async def _setup_reminder_schedules(self) -> None:
        """Set up reminder schedules from config."""
        if not self.config.reminder_schedule:
            logger.info("No reminder schedules configured")
            return

        for repo_name, schedule in self.config.reminder_schedule.items():
            logger.info(f"Setting up reminders for {repo_name}: {schedule}")
            # Implementation would go here

    async def _initialize_clients(self) -> None:
        """Initialize GitHub, Slack, and Linear clients"""

        try:
            # GitHub client
            from autopr.clients.github_client import GitHubClient

            self.github_client = GitHubClient(os.getenv("GITHUB_TOKEN"))

            # Slack client (if using direct API)
            from slack_sdk.web.async_client import AsyncWebClient  # type: ignore[import-not-found]

            self.slack_client = AsyncWebClient(token=os.getenv("SLACK_BOT_TOKEN"))

            # Linear client
            from autopr.clients.linear_client import LinearClient

            self.linear_client = LinearClient(os.getenv("LINEAR_API_KEY"))

            logger.info("Integration clients initialized")

        except Exception as e:
            logger.exception(f"Failed to initialize clients: {e!s}")
            raise

    async def _load_configuration(self) -> AxoloConfig:
        """Load Axolo configuration from environment"""

        return AxoloConfig(
            api_key=os.getenv("AXOLO_API_KEY", ""),
            base_url=os.getenv("AXOLO_BASE_URL", "https://api.axolo.dev/v1"),
            timeout=int(os.getenv("AXOLO_TIMEOUT", "30")),
            max_retries=int(os.getenv("AXOLO_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("AXOLO_RETRY_DELAY", "1.0")),
            workspace_url=os.getenv("AXOLO_WORKSPACE_URL", ""),
            slack_webhook=os.getenv("AXOLO_SLACK_WEBHOOK", ""),
            github_repos=(
                os.getenv("AXOLO_GITHUB_REPOS", "").split(",")
                if os.getenv("AXOLO_GITHUB_REPOS")
                else []
            ),
            reminder_schedule={
                "daily_standup": os.getenv("AXOLO_STANDUP_TIME", "09:00"),
                "stale_pr_reminder": os.getenv("AXOLO_STALE_REMINDER", "14:00"),
                "end_of_day_summary": os.getenv("AXOLO_EOD_SUMMARY", "17:00"),
            },
            ai_tool_mentions={
                "autopr": os.getenv("AUTOPR_MENTION", "@autopr"),
                "copilot": os.getenv("COPILOT_MENTION", "@github-copilot"),
            },
            custom_commands={
                "analyze": "/autopr-analyze",
                "status": "/autopr-status",
                "assign": "/autopr-assign-ai",
            },
        )

    async def create_pr_channel(self, pr_data: dict[str, Any]) -> AxoloPRChannel:
        """Create or get existing Axolo channel for PR"""

        pr_key = f"{pr_data['repository']}/#{pr_data['pr_number']}"

        # Check if channel already exists
        if pr_key in self.active_channels:
            return self.active_channels[pr_key]

        # Let Axolo create the channel (it does this automatically)
        # We just track it in our system
        channel = AxoloPRChannel(
            channel_id=f"pr-{pr_data['repository'].replace('/', '-')}-{pr_data['pr_number']}",
            channel_name=f"PR #{pr_data['pr_number']}: {pr_data['title'][:30]}...",
            pr_number=pr_data["pr_number"],
            repository=pr_data["repository"],
            created_at=datetime.utcnow(),
            participants=[],
            status="active",
        )

        self.active_channels[pr_key] = channel

        logger.info(
            f"PR channel created - channel_id: {channel.channel_id}, pr_number: {pr_data['pr_number']}, repository: {pr_data['repository']}"
        )

        return channel

    async def post_autopr_analysis(
        self, channel: AxoloPRChannel, analysis_result: dict[str, Any]
    ) -> None:
        """Post AutoPR analysis results to Axolo channel"""

        if not self.messaging:
            logger.error("Messaging not initialized")
            return

        # Format analysis summary
        self.messaging.format_analysis_summary(analysis_result)

        # Create rich Slack message
        message: dict[str, Any] = {
            "channel": channel.channel_id,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🤖 AutoPR Analysis Complete",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Platform Detected:*\n{analysis_result.get('platform_detected', 'Unknown')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Confidence:*\n{analysis_result.get('confidence_score', 0):.0%}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Issues Found:*\n{len(analysis_result.get('issues_found', []))}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*AI Tools Assigned:*\n{len(analysis_result.get('ai_assignments', []))}",
                        },
                    ],
                },
            ],
        }

        # Add detailed findings if any
        if analysis_result.get("issues_found"):
            issues_block = self.messaging.create_issues_block(analysis_result["issues_found"])
            message["blocks"].append(issues_block)

        # Add next steps
        if analysis_result.get("next_steps"):
            next_steps_block = self.messaging.create_next_steps_block(analysis_result["next_steps"])
            message["blocks"].append(next_steps_block)

        # Post to Slack
        await self.messaging.post_slack_message(message)

        logger.info(
            f"Analysis posted to channel - channel_id: {channel.channel_id}, issues_count: {len(analysis_result.get('issues_found', []))}"
        )

    async def link_linear_issues(
        self, channel: AxoloPRChannel, issues: list[dict[str, Any]]
    ) -> None:
        """Link created Linear issues to Axolo channel"""

        if not issues:
            return

        if not self.messaging:
            logger.error("Messaging not initialized")
            return

        # Create message with Linear issues
        message: dict[str, Any] = {
            "channel": channel.channel_id,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔗 Linear Issues Created",
                    },
                },
            ],
        }

        # Add issue details
        for issue in issues[:5]:  # Limit to 5 issues
            issue_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"• *{issue.get('title', 'Untitled')}*\n{issue.get('url', 'No URL')}",
                },
            }
            message["blocks"].append(issue_block)

        await self.messaging.post_slack_message(message)

        logger.info(
            f"Linear issues linked to channel - channel_id: {channel.channel_id}, issues_count: {len(issues)}"
        )

    async def setup_ai_assignments(
        self, channel: AxoloPRChannel, assignments: list[dict[str, Any]]
    ) -> None:
        """Setup AI tool assignments in channel"""

        if not assignments:
            return

        if not self.messaging:
            logger.error("Messaging not initialized")
            return

        # Create message with AI assignments
        message: dict[str, Any] = {
            "channel": channel.channel_id,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🤖 AI Tools Assigned",
                    },
                },
            ],
        }

        # Add assignment details
        for assignment in assignments:
            assignment_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"• *{assignment.get('tool', 'Unknown')}*: {assignment.get('task', 'No task specified')}",
                },
            }
            message["blocks"].append(assignment_block)

        await self.messaging.post_slack_message(message)

        logger.info(
            f"AI assignments posted to channel - channel_id: {channel.channel_id}, assignments_count: {len(assignments)}"
        )

    # Command handlers (delegate to command_handler)
    async def handle_analyze_command(self, command_data: dict[str, Any]) -> None:
        """Handle /autopr-analyze command"""
        if self.command_handler:
            await self.command_handler.handle_analyze_command(command_data)

    async def handle_status_command(self, command_data: dict[str, Any]) -> None:
        """Handle /autopr-status command"""
        if self.command_handler:
            await self.command_handler.handle_status_command(command_data)

    async def handle_assign_ai_command(self, command_data: dict[str, Any]) -> None:
        """Handle /autopr-assign-ai command"""
        if self.command_handler:
            await self.command_handler.handle_assign_ai_command(command_data)

    # Background service
    async def start_background_reminder_service(self) -> None:
        """Start the background reminder service"""
        if self.reminder_service:
            await self.reminder_service.start_background_service()
