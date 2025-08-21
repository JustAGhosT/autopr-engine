"""
Mistral 7B Model Configuration

Configuration for Mistral 7B local model with specific competency ratings
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


# Mistral 7B Model Configuration
MISTRAL_7B_CONFIG = ModelSpec(
    name="mistral-7b",
    provider="local",
    release_date="2023-09-27",
    vram_required="4-6GB",
    performance_tier="Fast",
    availability=False,  # Will be detected at runtime
    endpoint_available=False,  # Will be set based on runtime detection
    competency_ratings={
        # Good competency for simpler linting tasks
        "E501": 0.7,  # Line length - good competency
        "F401": 0.85,  # Unused imports - high competency
        "PTH123": 0.8,  # Path handling - high competency
        "PTH118": 0.8,  # Path handling - high competency
        "PTH110": 0.8,  # Path handling - high competency
        "PTH103": 0.8,  # Path handling - high competency
        "SIM102": 0.75,  # Code simplification - good
        "SIM117": 0.75,  # Code simplification - good
        "SIM105": 0.75,  # Code simplification - good
        "SIM103": 0.75,  # Code simplification - good
        "TRY401": 0.7,  # Exception handling - moderate
        "TRY300": 0.7,  # Exception handling - moderate
        "TRY203": 0.7,  # Exception handling - moderate
        "TRY301": 0.7,  # Exception handling - moderate
        "G004": 0.8,  # Logging - high competency
        "ARG001": 0.85,  # Arguments - high competency
        "ARG002": 0.85,  # Arguments - high competency
        "TID252": 0.75,  # Import style - good
        "N806": 0.7,  # Naming conventions - moderate
        "C414": 0.8,  # Unnecessary list calls - high
        "T201": 0.9,  # Print statements - very high
    },
    recommended_use_cases=[
        "Development testing",
        "Simple linting fixes",
        "Fast iterations",
        "Local development",
        "Resource-constrained environments",
    ],
)


def get_mistral_7b_endpoints() -> list:
    """Get potential endpoints for Mistral 7B."""
    return [
        "http://localhost:8000/v1",  # Standard local inference
        "http://localhost:11434/v1",  # Ollama
        "http://localhost:5000/v1",  # Custom endpoint
        "http://127.0.0.1:8080/v1",  # Alternative port
    ]


def check_availability() -> Tuple[bool, str]:
    """
    Check if Mistral 7B is available locally.

    Returns:
        Tuple of (availability, reason)
    """
    import requests
    from contextlib import suppress

    endpoints = get_mistral_7b_endpoints()

    for endpoint in endpoints:
        try:
            with suppress(Exception):
                response = requests.get(f"{endpoint}/models", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    for model in models:
                        if "mistral" in model.get("id", "").lower():
                            return True, f"Available at {endpoint}"
        except:
            continue

    return False, "No local Mistral 7B endpoint found"


def update_availability() -> bool:
    """Update the availability status of Mistral 7B."""
    available, reason = check_availability()
    MISTRAL_7B_CONFIG.availability = available
    MISTRAL_7B_CONFIG.endpoint_available = available
    return available
