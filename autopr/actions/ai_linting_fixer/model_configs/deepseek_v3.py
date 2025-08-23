"""
DeepSeek-V3 Model Configuration

Configuration for DeepSeek-V3 local model with specific competency ratings
and performance characteristics for code linting fixes.
"""

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
    competency_ratings: dict[str, float] = None
    recommended_use_cases: list = None


# DeepSeek-V3 Model Configuration
DEEPSEEK_V3_CONFIG = ModelSpec(
    name="deepseek-v3",
    provider="local",
    release_date="2024-12-26",
    vram_required="48GB+",
    performance_tier="Maximum",
    availability=False,  # Will be detected at runtime
    endpoint_available=False,  # Will be set based on runtime detection
    competency_ratings={
        # Maximum competency for research and complex tasks
        "E501": 0.96,  # Line length - outstanding competency
        "F401": 0.98,  # Unused imports - near perfect
        "PTH123": 0.97,  # Path handling - outstanding competency
        "PTH118": 0.97,  # Path handling - outstanding competency
        "PTH110": 0.97,  # Path handling - outstanding competency
        "PTH103": 0.97,  # Path handling - outstanding competency
        "SIM102": 0.94,  # Code simplification - excellent
        "SIM117": 0.94,  # Code simplification - excellent
        "SIM105": 0.94,  # Code simplification - excellent
        "SIM103": 0.94,  # Code simplification - excellent
        "TRY401": 0.95,  # Exception handling - excellent
        "TRY300": 0.95,  # Exception handling - excellent
        "TRY203": 0.95,  # Exception handling - excellent
        "TRY301": 0.95,  # Exception handling - excellent
        "G004": 0.98,  # Logging - near perfect
        "ARG001": 0.98,  # Arguments - near perfect
        "ARG002": 0.98,  # Arguments - near perfect
        "TID252": 0.96,  # Import style - outstanding
        "N806": 0.93,  # Naming conventions - excellent
        "C414": 0.95,  # Unnecessary list calls - excellent
        "T201": 0.92,  # Print statements - excellent
    },
    recommended_use_cases=[
        "Research and complex tasks",
        "Advanced code analysis",
        "Multi-file refactoring",
        "Complex reasoning tasks",
        "High-end local deployment",
    ],
)


def get_deepseek_v3_endpoints() -> list:
    """Get potential endpoints for DeepSeek-V3."""
    return [
        "http://localhost:8000/v1",  # Standard local inference
        "http://localhost:11434/v1",  # Ollama
        "http://localhost:5000/v1",  # Custom endpoint
        "http://127.0.0.1:8080/v1",  # Alternative port
        "http://localhost:1234/v1",  # LM Studio
        "http://localhost:3000/v1",  # Text Generation WebUI
    ]


def check_availability() -> tuple[bool, str]:
    """
    Check if DeepSeek-V3 is available locally.

    Returns:
        Tuple of (availability, reason)
    """
    from contextlib import suppress

    import requests

    endpoints = get_deepseek_v3_endpoints()

    for endpoint in endpoints:
        with suppress(Exception):
            response = requests.get(f"{endpoint}/models", timeout=5)
            if response.status_code == 200:
                models = response.json().get("data", [])
                for model in models:
                    model_id = model.get("id", "").lower()
                    if "deepseek" in model_id and "v3" in model_id:
                        return True, f"Available at {endpoint}"

    return False, "No local DeepSeek-V3 endpoint found"


def update_availability() -> bool:
    """Update the availability status of DeepSeek-V3."""
    available, reason = check_availability()
    DEEPSEEK_V3_CONFIG.availability = available
    DEEPSEEK_V3_CONFIG.endpoint_available = available
    return available
