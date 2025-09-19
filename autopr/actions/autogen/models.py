"""
AutoGen Models

Data models for AutoGen multi-agent integration.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AutoGenInputs(BaseModel):
    """Inputs for AutoGen multi-agent processing."""
    comment_body: str
    file_path: Optional[str] = None
    file_content: Optional[str] = None
    pr_context: Dict[str, Any] = Field(default_factory=dict)
    task_type: str = (
        "analyze_and_fix"  # "analyzeAnd_fix", "code_review", "security_audit"
    )
    agents_config: Dict[str, Any] = Field(default_factory=dict)


class AutoGenOutputs(BaseModel):
    """Outputs from AutoGen multi-agent processing."""
    success: bool
    analysis: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    fix_code: Optional[str] = None
    agent_conversations: List[Dict[str, str]] = Field(default_factory=list)
    consensus: Optional[str] = None
    error_message: Optional[str] = None
