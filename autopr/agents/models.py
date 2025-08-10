"""
Data models for the AutoPR Agent Framework.

This module defines the Pydantic models used for type-safe data exchange between agents.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    """Severity levels for code issues."""
    WARNING = "warning"
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

    def to_dict(self, *, include: set[str] | None = None, exclude: set[str] | None = None, 
               by_alias: bool = False, exclude_unset: bool = False, 
               exclude_defaults: bool = False, exclude_none: bool = False) -> Dict[str, Any]:
        """Convert the report to a dictionary using Pydantic v2 serialization.
        
        Args:
            include: Fields to include in the output
            exclude: Fields to exclude from the output
            by_alias: Whether to use field aliases in the output
            exclude_unset: Whether to exclude fields that were not explicitly set
            exclude_defaults: Whether to exclude fields that are set to their default value
            exclude_none: Whether to exclude fields that are None
            
        Returns:
            Dictionary representation of the model
        """
        return self.model_dump(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none
        )
        
    def to_json(self, *, indent: int | None = None, **kwargs) -> str:
        """Convert the report to a JSON string using Pydantic v2 serialization.
        
        Args:
            indent: Number of spaces for JSON indentation
            **kwargs: Additional arguments passed to model_dump_json()
            
        Returns:
            JSON string representation of the model
        """
        return self.model_dump_json(indent=indent, **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeAnalysisReport':
        """Create a report from a dictionary using Pydantic v2 validation.
        
        Args:
            data: Dictionary containing the report data
            
        Returns:
            A new CodeAnalysisReport instance
        """
        return cls.model_validate(data)
        
    @classmethod
    def from_json(cls, json_data: str | bytes | bytearray) -> 'CodeAnalysisReport':
        """Create a report from a JSON string using Pydantic v2 validation.
        
        Args:
            json_data: JSON string or bytes containing the report data
            
        Returns:
            A new CodeAnalysisReport instance
        """
        return cls.model_validate_json(json_data)
