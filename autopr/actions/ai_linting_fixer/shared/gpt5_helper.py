"""
Shared GPT-5-Chat Helper Functions

Centralized logic for GPT-5-Chat availability checking, fallback strategies,
and endpoint reachability to prevent duplication and maintain consistency.
"""

import os
from typing import Any


def get_gpt5_fallback_strategies() -> dict[str, list[tuple[str, str]]]:
    """
    Get fallback strategies for GPT-5-Chat.

    Returns:
        Dictionary containing primary and fallback model strategies
    """
    return {
        "primary": [
            ("gpt-5-chat", "openai"),  # Primary choice
        ],
        "with_fallback": [
            ("gpt-5-chat", "openai"),  # Best available
            ("gpt-4o", "azure_openai"),  # High competency fallback
            ("gpt-4", "azure_openai"),  # Solid fallback
        ],
    }


def check_availability(config: Any) -> tuple[bool, str]:
    """
    Check if GPT-5-Chat is available based on config and environment.

    Args:
        config: ModelSpec object containing availability and other settings

    Returns:
        Tuple of (availability, reason)
    """
    try:
        # Check config-based availability first
        if not config.availability:
            return False, "Model flagged unavailable in config"

        # Check for API key availability
        has_key = bool(os.getenv("OPENAI_API_KEY"))
        if has_key:
            return True, "GPT-5-Chat is available (API key present)"
        else:
            return False, "GPT-5-Chat not available: OPENAI_API_KEY missing"
    except Exception as e:
        return False, f"Error checking availability: {e}"


def check_endpoint_reachability() -> bool:
    """
    Check if the GPT-5-Chat endpoint is reachable.

    Returns:
        True if endpoint is reachable, False otherwise
    """
    try:
        # This would be the actual endpoint reachability check
        # For now, return False as it's not released yet
        return False
    except Exception:
        return False


def update_availability(config: Any, update_endpoint_only: bool = False) -> bool:
    """
    Update the availability status of GPT-5-Chat.

    Args:
        config: ModelSpec object to update
        update_endpoint_only: If True, only update endpoint_available, not availability

    Returns:
        True if model is available, False otherwise
    """
    available, reason = check_availability(config)

    if not update_endpoint_only:
        config.availability = available

    # Check endpoint reachability separately
    endpoint_reachable = check_endpoint_reachability()
    config.endpoint_available = endpoint_reachable

    return available
