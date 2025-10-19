"""
AutoGen Models

Data models for AutoGen multi-agent integration.
"""

from typing import Any

from pydantic import BaseModel, Field


class AutoGenInputs(BaseModel):
    """Inputs for AutoGen multi-agent processing."""
    comment_body: str
    file_path: str | None = None
    file_content: str | None = None
    pr_context: dict[str, Any] = Field(default_factory=dict)
    task_type: str = (
        "analyze_and_fix"  # "analyzeAnd_fix", "code_review", "security_audit"
    )
    agents_config: dict[str, Any] = Field(default_factory=dict)


class AutoGenOutputs(BaseModel):
    """Outputs from AutoGen multi-agent processing."""
    success: bool
    analysis: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    fix_code: str | None = None
    agent_conversations: list[dict[str, str]] = Field(default_factory=list)
    consensus: str | None = None
    error_message: str | None = None
