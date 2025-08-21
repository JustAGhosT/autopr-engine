"""
GPT-5-Chat Model Configuration

Configuration for OpenAI's GPT-5-Chat model with specific competency ratings
and performance characteristics for code linting fixes.
"""

from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class ModelSpec:
    """Model specification with availability and performance characteristics."""

    name: str
    provider: str
    release_date: str
    vram_required: str
    performance_tier: str
    availability: bool
    endpoint_available: bool = False
    competency_ratings: Dict[str, float] = None
    recommended_use_cases: list = None


# GPT-5-Chat Model Configuration
GPT_5_CHAT_CONFIG = ModelSpec(
    name="gpt-5-chat",
    provider="openai",
    release_date="2025-08-07",
    vram_required="N/A (Cloud)",
    performance_tier="Maximum",
    availability=True,
    endpoint_available=False,  # Will be set based on runtime detection
    competency_ratings={
        # Exceptional competency across all linting categories
        "E501": 0.98,  # Line length - outstanding competency
        "F401": 0.99,  # Unused imports - near perfect
        "PTH123": 0.99,  # Path handling - near perfect
        "PTH118": 0.99,  # Path handling - near perfect
        "PTH110": 0.99,  # Path handling - near perfect
        "PTH103": 0.99,  # Path handling - near perfect
        "SIM102": 0.95,  # Code simplification - excellent
        "SIM117": 0.95,  # Code simplification - excellent
        "SIM105": 0.95,  # Code simplification - excellent
        "SIM103": 0.95,  # Code simplification - excellent
        "TRY401": 0.98,  # Exception handling - outstanding
        "TRY300": 0.98,  # Exception handling - outstanding
        "TRY203": 0.98,  # Exception handling - outstanding
        "TRY301": 0.98,  # Exception handling - outstanding
        "G004": 0.99,  # Logging - near perfect
        "ARG001": 0.99,  # Arguments - near perfect
        "ARG002": 0.99,  # Arguments - near perfect
        "TID252": 0.98,  # Import style - outstanding
        "N806": 0.97,  # Naming conventions - excellent
        "C414": 0.96,  # Unnecessary list calls - excellent
        "T201": 0.94,  # Print statements - very high
    },
    recommended_use_cases=[
        "Complex linting fixes",
        "Advanced code refactoring",
        "Challenging syntax transformations",
        "Multi-file dependency resolution",
        "Performance-critical fixes",
    ],
)


def get_gpt5_fallback_strategies() -> Dict[str, list]:
    """Get fallback strategies for GPT-5-Chat."""
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


def check_availability() -> Tuple[bool, str]:
    """
    Check if GPT-5-Chat is available.

    Returns:
        Tuple of (availability, reason)
    """
    try:
        # This would be the actual availability check
        # For now, return False as it's not released yet
        return False, "GPT-5-Chat not yet released (expected 2025)"
    except Exception as e:
        return False, f"Error checking availability: {e}"


def update_availability() -> bool:
    """Update the availability status of GPT-5-Chat."""
    available, reason = check_availability()
    GPT_5_CHAT_CONFIG.availability = available
    GPT_5_CHAT_CONFIG.endpoint_available = available
    return available
