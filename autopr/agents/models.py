"""
Data models for the AutoPR Agent Framework.

This module defines the Pydantic models used for type-safe data exchange between agents.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    """Severity levels for code issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CodeIssue(BaseModel):
    """Represents a single code quality issue."""
    file_path: str = Field(..., description="Path to the file containing the issue")
    line_number: int = Field(..., description="Line number where the issue occurs")
    column: int = Field(0, description="Column number where the issue occurs")
    message: str = Field(..., description="Description of the issue")
    severity: IssueSeverity = Field(..., description="Severity level of the issue")
    rule_id: str = Field(..., description="Identifier for the rule that was violated")
    category: str = Field(..., description="Category of the issue (e.g., 'performance', 'security')")
    fix: Optional[Dict[str, Any]] = Field(
        None, 
        description="Suggested fix for the issue, if available"
    )


class PlatformComponent(BaseModel):
    """Represents a component of the technology stack."""
    name: str = Field(..., description="Name of the component")
    version: Optional[str] = Field(
        None, 
        description="Version of the component, if detected"
    )
    confidence: float = Field(
        ..., 
        ge=0, 
        le=1,
        description="Confidence score for this detection (0-1)"
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="List of evidence supporting this detection"
    )


class PlatformAnalysis(BaseModel):
    """Analysis of the platform and technology stack."""
    platform: str = Field(..., description="Primary platform/framework detected")
    confidence: float = Field(
        ..., 
        ge=0, 
        le=1,
        description="Confidence score for platform detection (0-1)"
    )
    components: List[PlatformComponent] = Field(
        default_factory=list,
        description="List of detected platform components"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="List of recommendations for the platform"
    )


class CodeAnalysisReport(BaseModel):
    """Comprehensive code analysis report."""
    issues: List[CodeIssue] = Field(
        default_factory=list,
        description="List of code quality issues found"
    )
    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Code quality metrics"
    )
    summary: str = Field(
        ...,
        description="Human-readable summary of the analysis"
    )
    platform_analysis: PlatformAnalysis = Field(
        ...,
        description="Analysis of the platform and technology stack"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the report to a dictionary."""
        return self.dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeAnalysisReport':
        """Create a report from a dictionary."""
        return cls.parse_obj(data)
