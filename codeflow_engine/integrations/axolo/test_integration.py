#!/usr/bin/env python3
"""Test script for Axolo integration."""

import asyncio

from codeflow_engine.integrations.axolo import create_axolo_integration, is_axolo_available


async def test_axolo_integration() -> None:
    """Test Axolo integration functionality"""

    if not is_axolo_available():
        return

    # Create integration
    axolo = await create_axolo_integration()

    # Test PR channel creation
    test_pr_data = {
        "pr_number": 123,
        "title": "Test PR for Axolo Integration",
        "repository": "test/repo",
        "author": "test-user",
        "html_url": "https://github.com/test/repo/pull/123",
    }

    channel = await axolo.create_pr_channel(test_pr_data)

    # Test analysis posting
    test_analysis = {
        "platform_detected": "Next.js",
        "confidence_score": 0.95,
        "issues_found": [
            {"severity": "High", "title": "Security vulnerability detected"},
            {"severity": "Medium", "title": "Performance optimization needed"},
        ],
        "ai_assignments": [
            {"tool": "CodeRabbit", "task": "Security review"},
            {"tool": "Copilot", "task": "Performance optimization"},
        ],
    }

    await axolo.post_autopr_analysis(channel, test_analysis)

    # Cleanup
    await axolo.close()


if __name__ == "__main__":
    # Run test
    asyncio.run(test_axolo_integration())
