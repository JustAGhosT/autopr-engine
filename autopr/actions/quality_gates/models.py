"""
Quality Gates Models

Data models for quality gate validation and testing.
"""

from typing import Any

from pydantic import BaseModel, Field


class QualityGateInputs(BaseModel):
    """Inputs for quality gate validation."""
    file_path: str
    original_content: str
    modified_content: str
    fix_type: str
    project_standards: dict[str, Any] = {}
    run_tests: bool = True
    check_syntax: bool = True
    check_style: bool = True


class QualityGateOutputs(BaseModel):
    """Outputs from quality gate validation."""
    passed: bool
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    test_results: dict[str, Any] = Field(default_factory=dict)
    quality_score: float = 0.0
    recommendations: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
