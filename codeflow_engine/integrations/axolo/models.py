"""Data models for Axolo integration."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AxoloPRChannel:
    """Axolo PR Channel data class."""

    channel_id: str
    channel_name: str
    pr_number: int
    repository: str
    created_at: datetime
    participants: list[str]
    status: str  # 'active', 'archived', 'closed'
