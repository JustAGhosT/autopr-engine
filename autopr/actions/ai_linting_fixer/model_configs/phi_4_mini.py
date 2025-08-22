"""
Phi-4 Mini Model Configuration

Configuration for Microsoft Phi-4 Mini local model with specific competency ratings
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


# Phi-4 Mini Model Configuration
PHI_4_MINI_CONFIG = ModelSpec(
    name="phi-4-mini",
    provider="local",
    release_date="2024-12-11",
    vram_required="2-4GB",
    performance_tier="Efficient",
    availability=False,  # Will be detected at runtime
    endpoint_available=False,  # Will be set based on runtime detection
    competency_ratings={
        # Efficient competency for edge deployment
        "E501": 0.65,  # Line length - moderate competency
        "F401": 0.8,  # Unused imports - high competency
        "PTH123": 0.75,  # Path handling - good competency
        "PTH118": 0.75,  # Path handling - good competency
        "PTH110": 0.75,  # Path handling - good competency
        "PTH103": 0.75,  # Path handling - good competency
        "SIM102": 0.7,  # Code simplification - moderate
        "SIM117": 0.7,  # Code simplification - moderate
        "SIM105": 0.7,  # Code simplification - moderate
        "SIM103": 0.7,  # Code simplification - moderate
        "TRY401": 0.65,  # Exception handling - moderate
        "TRY300": 0.65,  # Exception handling - moderate
        "TRY203": 0.65,  # Exception handling - moderate
        "TRY301": 0.65,  # Exception handling - moderate
        "G004": 0.78,  # Logging - good competency
        "ARG001": 0.82,  # Arguments - high competency
        "ARG002": 0.82,  # Arguments - high competency
        "TID252": 0.72,  # Import style - good
        "N806": 0.68,  # Naming conventions - moderate
        "C414": 0.75,  # Unnecessary list calls - good
        "T201": 0.85,  # Print statements - high
    },
    recommended_use_cases=[
        "Edge deployment",
        "Resource-constrained environments",
        "Fast simple fixes",
        "Mobile development",
        "Lightweight local inference",
    ],
)


def get_phi_4_mini_endpoints() -> list:
    """Get potential endpoints for Phi-4 Mini."""
    return [
        "http://localhost:8000/v1",  # Standard local inference
        "http://localhost:11434/v1",  # Ollama
        "http://localhost:5000/v1",  # Custom endpoint
        "http://127.0.0.1:8080/v1",  # Alternative port
        "http://localhost:1234/v1",  # LM Studio
    ]


def check_availability() -> tuple[bool, str]:
    """
    Check if Phi-4 Mini is available locally.

    Returns:
        Tuple of (availability, reason)
    """
    from contextlib import suppress

    import requests

    endpoints = get_phi_4_mini_endpoints()

    for endpoint in endpoints:
        try:
            with suppress(Exception):
                response = requests.get(f"{endpoint}/models", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    for model in models:
                        model_id = model.get("id", "").lower()
                        if "phi" in model_id and ("4" in model_id or "mini" in model_id):
                            return True, f"Available at {endpoint}"
        except:
            continue

    return False, "No local Phi-4 Mini endpoint found"


def update_availability() -> bool:
    """Update the availability status of Phi-4 Mini."""
    available, reason = check_availability()
    PHI_4_MINI_CONFIG.availability = available
    PHI_4_MINI_CONFIG.endpoint_available = available
    return available
