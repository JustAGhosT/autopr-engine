"""
DeepSeek-R1 7B Model Configuration

Configuration for DeepSeek-R1 7B local model with specific competency ratings
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


# DeepSeek-R1 7B Model Configuration
DEEPSEEK_R1_7B_CONFIG = ModelSpec(
    name="deepseek-r1-7b",
    provider="local",
    release_date="2024-12-20",
    vram_required="4-6GB",
    performance_tier="Excellent",
    availability=False,  # Will be detected at runtime
    endpoint_available=False,  # Will be set based on runtime detection
    competency_ratings={
        # Excellent competency for code generation and fixing
        "E501": 0.85,  # Line length - high competency
        "F401": 0.9,  # Unused imports - very high competency
        "PTH123": 0.88,  # Path handling - high competency
        "PTH118": 0.88,  # Path handling - high competency
        "PTH110": 0.88,  # Path handling - high competency
        "PTH103": 0.88,  # Path handling - high competency
        "SIM102": 0.82,  # Code simplification - high
        "SIM117": 0.82,  # Code simplification - high
        "SIM105": 0.82,  # Code simplification - high
        "SIM103": 0.82,  # Code simplification - high
        "TRY401": 0.85,  # Exception handling - high
        "TRY300": 0.85,  # Exception handling - high
        "TRY203": 0.85,  # Exception handling - high
        "TRY301": 0.85,  # Exception handling - high
        "G004": 0.9,  # Logging - very high competency
        "ARG001": 0.9,  # Arguments - very high competency
        "ARG002": 0.9,  # Arguments - very high competency
        "TID252": 0.85,  # Import style - high
        "N806": 0.8,  # Naming conventions - high
        "C414": 0.87,  # Unnecessary list calls - high
        "T201": 0.85,  # Print statements - high
    },
    recommended_use_cases=[
        "Code generation",
        "Complex linting fixes",
        "Reasoning-based refactoring",
        "Local development",
        "Privacy-sensitive environments",
    ],
)


def get_deepseek_r1_endpoints() -> list:
    """Get potential endpoints for DeepSeek-R1 7B."""
    return [
        "http://localhost:8000/v1",  # Standard local inference
        "http://localhost:11434/v1",  # Ollama
        "http://localhost:5000/v1",  # Custom endpoint
        "http://127.0.0.1:8080/v1",  # Alternative port
        "http://localhost:1234/v1",  # LM Studio
    ]


def check_availability() -> Tuple[bool, str]:
    """
    Check if DeepSeek-R1 7B is available locally.

    Returns:
        Tuple of (availability, reason)
    """
    import requests
    from contextlib import suppress

    endpoints = get_deepseek_r1_endpoints()

    for endpoint in endpoints:
        try:
            with suppress(Exception):
                response = requests.get(f"{endpoint}/models", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    for model in models:
                        model_id = model.get("id", "").lower()
                        if "deepseek" in model_id and "r1" in model_id:
                            return True, f"Available at {endpoint}"
        except:
            continue

    return False, "No local DeepSeek-R1 7B endpoint found"


def update_availability() -> bool:
    """Update the availability status of DeepSeek-R1 7B."""
    available, reason = check_availability()
    DEEPSEEK_R1_7B_CONFIG.availability = available
    DEEPSEEK_R1_7B_CONFIG.endpoint_available = available
    return available
