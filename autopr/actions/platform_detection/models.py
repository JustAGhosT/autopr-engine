"""
Platform Detection Models

Data models for platform detection inputs and outputs.
"""

from typing import Any

from pydantic import BaseModel, Field


class PlatformDetectorInputs(BaseModel):
    """Inputs for platform detection."""
    repository_url: str
    commit_messages: list[str] = Field(default_factory=list)
    workspace_path: str = "."
    package_json_content: str | None = None


class PlatformDetectorOutputs(BaseModel):
    """Outputs from platform detection."""
    primary_platform: str
    secondary_platforms: list[str] = []
    confidence_scores: dict[str, float] = {}
    workflow_type: str = "single_platform"
    platform_specific_configs: dict[str, Any] = {}
    recommended_enhancements: list[str] = []
    migration_opportunities: list[str] = []
    hybrid_workflow_analysis: dict[str, Any] | None = None
