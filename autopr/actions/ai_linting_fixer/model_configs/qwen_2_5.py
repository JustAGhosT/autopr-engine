"""
Qwen 2.5 Model Configuration

Configuration for Qwen 2.5 local model with specific competency ratings
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


# Qwen 2.5 Model Configuration
QWEN_2_5_CONFIG = ModelSpec(
    name="qwen-2.5",
    provider="local",
    release_date="2024-09-19",
    vram_required="Varies (3B-72B)",
    performance_tier="Good",
    availability=False,  # Will be detected at runtime
    endpoint_available=False,  # Will be set based on runtime detection
    competency_ratings={
        # Good multilingual competency
        "E501": 0.78,  # Line length - good competency
        "F401": 0.83,  # Unused imports - high competency
        "PTH123": 0.81,  # Path handling - high competency
        "PTH118": 0.81,  # Path handling - high competency
        "PTH110": 0.81,  # Path handling - high competency
        "PTH103": 0.81,  # Path handling - high competency
        "SIM102": 0.76,  # Code simplification - good
        "SIM117": 0.76,  # Code simplification - good
        "SIM105": 0.76,  # Code simplification - good
        "SIM103": 0.76,  # Code simplification - good
        "TRY401": 0.74,  # Exception handling - good
        "TRY300": 0.74,  # Exception handling - good
        "TRY203": 0.74,  # Exception handling - good
        "TRY301": 0.74,  # Exception handling - good
        "G004": 0.82,  # Logging - high competency
        "ARG001": 0.84,  # Arguments - high competency
        "ARG002": 0.84,  # Arguments - high competency
        "TID252": 0.78,  # Import style - good
        "N806": 0.75,  # Naming conventions - good
        "C414": 0.8,  # Unnecessary list calls - high
        "T201": 0.82,  # Print statements - high
    },
    recommended_use_cases=[
        "Multilingual code projects",
        "International development teams",
        "Good general purpose model",
        "Balanced performance/efficiency",
        "Various model sizes available",
    ],
)


def get_qwen_2_5_endpoints() -> list:
    """Get potential endpoints for Qwen 2.5."""
    return [
        "http://localhost:8000/v1",  # Standard local inference
        "http://localhost:11434/v1",  # Ollama
        "http://localhost:5000/v1",  # Custom endpoint
        "http://127.0.0.1:8080/v1",  # Alternative port
        "http://localhost:1234/v1",  # LM Studio
        "http://localhost:3000/v1",  # Text Generation WebUI
    ]


def check_availability() -> Tuple[bool, str]:
    """
    Check if Qwen 2.5 is available locally.

    Returns:
        Tuple of (availability, reason)
    """
    import requests
    from contextlib import suppress

    endpoints = get_qwen_2_5_endpoints()

    for endpoint in endpoints:
        try:
            with suppress(Exception):
                response = requests.get(f"{endpoint}/models", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    for model in models:
                        model_id = model.get("id", "").lower()
                        if "qwen" in model_id and "2.5" in model_id:
                            return True, f"Available at {endpoint}"
        except:
            continue

    return False, "No local Qwen 2.5 endpoint found"


def update_availability() -> bool:
    """Update the availability status of Qwen 2.5."""
    available, reason = check_availability()
    QWEN_2_5_CONFIG.availability = available
    QWEN_2_5_CONFIG.endpoint_available = available
    return available
