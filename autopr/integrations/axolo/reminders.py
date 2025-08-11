"""Background reminder service for Axolo integration."""

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import AxoloConfig
    from .messaging import AxoloMessaging

logger = logging.getLogger(__name__)


class AxoloReminderService:
    """Handles background reminder services for Axolo integration."""

    def __init__(self, config: "AxoloConfig", messaging: "AxoloMessaging") -> None:
        self.config = config
        self.messaging = messaging

    async def start_background_service(self) -> None:
        """Background service for PR reminders and updates.

        Continuously checks the time and sends scheduled reminders for:
        - Daily standups
        - Stale PRs
        - End of day summaries
        """
        while True:
            try:
                current_time = datetime.now().strftime("%H:%M")

                # Safely access reminder_schedule with defaults
                reminder_schedule = self.config.reminder_schedule

                # Daily standup reminders
                if current_time == reminder_schedule.get("daily_standup", "10:00"):
                    await self.send_daily_standup_summary()

                # Stale PR reminders
                elif current_time == reminder_schedule.get("stale_pr_reminder", "15:00"):
                    await self.send_stale_pr_reminders()

                # End of day summary
                elif current_time == reminder_schedule.get("end_of_day_summary", "17:00"):
                    await self.send_end_of_day_summary()

                # Sleep for 1 minute
                await asyncio.sleep(60)

            except Exception as e:
                # Add proper error logging
                error_msg = f"Error in background reminder service: {e!s}"
                logger.exception(error_msg)
                await asyncio.sleep(60)  # Sleep before retrying

    async def send_daily_standup_summary(self) -> None:
        """Send daily PR summary for standups"""

        summary = await self.generate_daily_pr_summary()

        # Format summary message
        message = {
            "text": "📅 Daily Standup Summary",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📅 Daily Standup Summary",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Active PRs:*\n{len(summary['active_prs'])}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Stale PRs:*\n{len(summary['stale_prs'])}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Completed PRs:*\n{len(summary['completed_prs'])}",
                        },
                    ],
                },
            ],
        }

        await self.messaging.post_slack_message(message)

        logger.info(
            f"Daily standup summary sent - active_prs: {len(summary['active_prs'])}, stale_prs: {len(summary['stale_prs'])}"
        )

    async def send_stale_pr_reminders(self) -> None:
        """Send reminders for stale PRs."""
        logger.info("Sending stale PR reminders")

    async def send_end_of_day_summary(self) -> None:
        """Send end of day summary."""
        logger.info("Sending end of day summary")

    async def generate_daily_pr_summary(self) -> dict[str, Any]:
        """Generate daily PR summary for standups."""
        # This would gather PR data and generate summary
        return {
            "active_prs": [],
            "stale_prs": [],
            "completed_prs": [],
            "summary_date": datetime.now().isoformat(),
        }
