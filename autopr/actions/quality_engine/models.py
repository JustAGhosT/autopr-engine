"""
Quality Engine Data Models
"""

from enum import Enum
from typing import Any

import pydantic


class QualityMode(Enum):
    """Operating mode for quality checks"""

    FAST = "fast"
    COMPREHENSIVE = "comprehensive"
    AI_ENHANCED = "ai_enhanced"
    SMART = "smart"


class QualityInputs(pydantic.BaseModel):
    """Input parameters for quality engine operations"""

    mode: QualityMode = QualityMode.SMART
    files: list[str] | None = None
    max_fixes: int = 50
    enable_ai_agents: bool = True
    config_path: str = "pyproject.toml"
    verbose: bool = False
    ai_provider: str | None = None
    ai_model: str | None = None


class ToolResult(pydantic.BaseModel):
    """Results from a single quality tool execution"""

    issues: list[dict[str, Any]]
    files_with_issues: list[str]
    summary: str
    execution_time: float


class QualityOutputs(pydantic.BaseModel):
    """Complete output from quality engine operations"""

    success: bool
    total_issues_found: int
    total_issues_fixed: int
    files_modified: list[str]
    issues_by_tool: dict[str, list[dict[str, Any]]] = {}
    files_by_tool: dict[str, list[str]] = {}
    summary: str
    tool_execution_times: dict[str, float] = {}
    ai_enhanced: bool = False
    ai_summary: str | None = None
