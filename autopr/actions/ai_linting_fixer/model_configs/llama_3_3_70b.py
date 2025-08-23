"""
Llama 3.3 70B Model Configuration

Configuration for Llama 3.3 70B local model with specific competency ratings
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


# Llama 3.3 70B Model Configuration
LLAMA_3_3_70B_CONFIG = ModelSpec(
    name="llama-3.3-70b",
    provider="local",
    release_date="2024-12-06",
    vram_required="35-40GB",
    performance_tier="High",
    availability=False,  # Will be detected at runtime
    endpoint_available=False,  # Will be set based on runtime detection
    competency_ratings={
        # High competency across all areas
        "E501": 0.9,  # Line length - very high competency
        "F401": 0.92,  # Unused imports - excellent competency
        "PTH123": 0.91,  # Path handling - excellent competency
        "PTH118": 0.91,  # Path handling - excellent competency
        "PTH110": 0.91,  # Path handling - excellent competency
        "PTH103": 0.91,  # Path handling - excellent competency
        "SIM102": 0.88,  # Code simplification - high
        "SIM117": 0.88,  # Code simplification - high
        "SIM105": 0.88,  # Code simplification - high
        "SIM103": 0.88,  # Code simplification - high
        "TRY401": 0.89,  # Exception handling - high
        "TRY300": 0.89,  # Exception handling - high
        "TRY203": 0.89,  # Exception handling - high
        "TRY301": 0.89,  # Exception handling - high
        "G004": 0.93,  # Logging - excellent competency
        "ARG001": 0.93,  # Arguments - excellent competency
        "ARG002": 0.93,  # Arguments - excellent competency
        "TID252": 0.9,  # Import style - very high
        "N806": 0.87,  # Naming conventions - high
        "C414": 0.9,  # Unnecessary list calls - very high
        "T201": 0.88,  # Print statements - high
    },
    recommended_use_cases=[
        "General purpose linting",
        "Complex reasoning tasks",
        "Multi-step refactoring",
        "High-quality code generation",
        "Enterprise local deployment",
    ],
)


def get_llama_3_3_endpoints() -> list:
    """Get potential endpoints for Llama 3.3 70B."""
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
    Check if Llama 3.3 70B is available locally.

    Returns:
        Tuple of (availability, reason)
    """
    from contextlib import suppress

    import requests

    endpoints = get_llama_3_3_endpoints()

    for endpoint in endpoints:
        try:
            response = requests.get(f"{endpoint}/models", timeout=5)
            response.raise_for_status()
            models = response.json().get("data", [])
            for model in models:
                model_id = model.get("id", "").lower()
                if "llama" in model_id and ("3.3" in model_id or "70b" in model_id):
                    return True, f"Available at {endpoint}"
        except (requests.RequestException, ValueError) as e:
            continue

    return False, "No local Llama 3.3 70B endpoint found"


def update_availability() -> bool:
    """Update the availability status of Llama 3.3 70B."""
    available, reason = check_availability()
    LLAMA_3_3_70B_CONFIG.availability = available
    LLAMA_3_3_70B_CONFIG.endpoint_available = available
    return available
