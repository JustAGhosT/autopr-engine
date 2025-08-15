"""
Models for the AutoPR Crew module.

This module provides data models and utility functions for the crew orchestration system.
"""

from typing import Any, Dict, List, Optional


def build_platform_model(
    summary_data: Dict[str, Any],
    platform_analysis: Dict[str, Any],
    last_platform_str: Optional[str] = None,
    platforms: Optional[List[tuple[str, float]]] = None,
    primary_platform: Optional[tuple[str, float]] = None,
    tools: Optional[List[str]] = None,
    frameworks: Optional[List[str]] = None,
    languages: Optional[List[str]] = None,
    config_files: Optional[List[str]] = None,
    analysis: Optional[Any] = None,
) -> Dict[str, Any]:
    """Build a platform model from analysis results."""
    # Use provided data or extract from platform_analysis
    if platforms is None and platform_analysis:
        platforms = platform_analysis.get("platforms", [])
    if primary_platform is None and platform_analysis:
        primary_platform = platform_analysis.get("primary_platform", ("unknown", 0.0))
    if tools is None and platform_analysis:
        tools = platform_analysis.get("tools", [])
    if frameworks is None and platform_analysis:
        frameworks = platform_analysis.get("frameworks", [])
    if languages is None and platform_analysis:
        languages = platform_analysis.get("languages", [])
    if config_files is None and platform_analysis:
        config_files = platform_analysis.get("config_files", [])
    if analysis is None and platform_analysis:
        analysis = platform_analysis.get("analysis")
    
    return {
        "platforms": platforms or [],
        "primary_platform": primary_platform or ("unknown", 0.0),
        "tools": tools or [],
        "frameworks": frameworks or [],
        "languages": languages or [],
        "config_files": config_files or [],
        "analysis": analysis,
        "summary_data": summary_data,
        "last_platform_str": last_platform_str,
    }


def build_code_quality_model(
    issues: List[Dict[str, Any]],
    score: float,
    metrics: Dict[str, Any],
    suggestions: List[str],
) -> Dict[str, Any]:
    """Build a code quality model from analysis results."""
    return {
        "issues": issues,
        "score": score,
        "metrics": metrics,
        "suggestions": suggestions,
    }


def build_linting_model(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a linting model from analysis results."""
    return {
        "issues": issues,
        "total_issues": len(issues),
        "critical_issues": len([i for i in issues if i.get("severity") == "critical"]),
        "high_issues": len([i for i in issues if i.get("severity") == "high"]),
        "medium_issues": len([i for i in issues if i.get("severity") == "medium"]),
        "low_issues": len([i for i in issues if i.get("severity") == "low"]),
    }
