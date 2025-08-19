#!/usr/bin/env python3
"""
AutoPR Integration: Axolo Communication Hub
Seamless GitHub ↔ Slack integration with ephemeral PR channels
"""

import os

from autopr.integrations.axolo.client import AxoloIntegration
from autopr.integrations.axolo.config import AxoloConfig
from autopr.integrations.axolo.models import AxoloPRChannel

__all__ = [
    "AxoloConfig",
    "AxoloIntegration",
    "AxoloPRChannel",
    "create_axolo_integration",
    "is_axolo_available",
]


async def create_axolo_integration() -> AxoloIntegration:
    """Factory function to create and initialize Axolo integration"""

    # Create integration with default config, then load from environment
    integration = AxoloIntegration()

    # Load configuration from environment
    config = await integration._load_configuration()
    integration.config = config

    await integration.initialize()
    return integration


def is_axolo_available() -> bool:
    """Check if Axolo integration is properly configured"""

    required_vars = [
        "AXOLO_API_KEY",
        "AXOLO_WORKSPACE_URL",
        "SLACK_BOT_TOKEN",
        "GITHUB_TOKEN",
    ]

    return all(os.getenv(var) for var in required_vars)
