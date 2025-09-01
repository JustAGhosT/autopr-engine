"""
Platform Detection Models

Data models for platform detection inputs and outputs.
"""

from typing import Any

from pydantic import BaseModel


class PlatformDetectorInputs(BaseModel):
    """Inputs for platform detection."""
    repository_url: str
    commit_messages: list[str] = []
    workspace_path: str = "."
    package_json_content: str | None = None


class PlatformDetectorOutputs(BaseModel):
    """Outputs from platform detection."""
    detected_platform: str  # "replit", "lovable", "bolt", "same", "emergent", "unknown"
    confidence_score: float
    platform_specific_config: dict[str, Any]
    recommended_workflow: str
    migration_suggestions: list[str]
    enhancement_opportunities: list[str]
    enhancement_opportunities: list[str]
