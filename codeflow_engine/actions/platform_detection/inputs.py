from typing import Any

from pydantic import BaseModel, Field


class PlatformDetectorInputs(BaseModel):
    repository_url: str
    commit_messages: list[str] = []
    workspace_path: str = "."
    package_json_content: str | None = None
    git_log_depth: int = 50


class PlatformDetectorOutputs(BaseModel):
    primary_platform: str
    secondary_platforms: list[str] = Field(default_factory=list)
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    workflow_type: str  # "single_platform", "hybrid_workflow", "multi_platform"
    platform_specific_configs: dict[str, Any] = Field(default_factory=dict)
    recommended_enhancements: list[str] = Field(default_factory=list)
    migration_opportunities: list[str] = Field(default_factory=list)
    hybrid_workflow_analysis: dict[str, Any] | None = None
