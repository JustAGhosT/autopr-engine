"""
AutoPR Engine Integrations
External service integrations for communication and project management
"""

from typing import Any, List, Optional, Type

from autopr.integrations.base import Integration

# Import integration classes with error handling
AxoloIntegration: type[Any] | None = None
_axolo_available = False
try:
    from autopr.integrations.axolo import AxoloIntegration

    _axolo_available = True
except ImportError:
    pass

# Registry of available integrations
AVAILABLE_INTEGRATIONS = {}
if _axolo_available and AxoloIntegration is not None:
    AVAILABLE_INTEGRATIONS["axolo"] = AxoloIntegration


def get_integration(integration_name: str) -> type[Integration] | None:
    """Get an integration class by name"""
    return AVAILABLE_INTEGRATIONS.get(integration_name)


def list_integrations() -> list[str]:
    """List all available integrations"""
    return list(AVAILABLE_INTEGRATIONS.keys())


__all__ = [
    "AVAILABLE_INTEGRATIONS",
    "get_integration",
    "list_integrations",
]

# Conditionally add AxoloIntegration to __all__ if available
if _axolo_available and AxoloIntegration is not None:
    __all__.append("AxoloIntegration")
