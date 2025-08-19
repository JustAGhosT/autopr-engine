"""Configuration classes for Axolo integration."""

from pydantic import BaseModel, Field


class AxoloConfig(BaseModel):
    """Configuration for Axolo integration."""

    api_key: str = Field(..., description="API key for Axolo service")
    base_url: str = Field("https://api.axolo.dev/v1", description="Base URL for Axolo API")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retries for failed requests")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")
    reminder_schedule: dict[str, str] = Field(
        default_factory=lambda: {
            "daily_standup": "10:00",
            "stale_pr_reminder": "15:00",
            "end_of_day_summary": "17:00",
        },
        description="Schedule for automated reminders",
    )
    workspace_url: str | None = Field(None, description="Axolo workspace URL")
    slack_webhook: str | None = Field(None, description="Slack webhook URL")
    github_repos: list[str] = Field(
        default_factory=list, description="GitHub repositories to monitor"
    )
    ai_tool_mentions: dict[str, str] = Field(
        default_factory=dict, description="AI tool mention mappings"
    )
    custom_commands: dict[str, str] = Field(
        default_factory=dict, description="Custom command mappings"
    )
