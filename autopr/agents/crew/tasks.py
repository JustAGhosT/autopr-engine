"""Task creation and summary generation for the AutoPR Agent Framework."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from crewai import Task
from autopr.agents.models import CodeIssue, PlatformAnalysis
from autopr.actions.quality_engine.volume_mapping import get_volume_level_name, VolumeLevel

# Volume thresholds for analysis depth (0-1000 scale)
VOLUME_THOROUGH_THRESHOLD = VolumeLevel.THOROUGH.value  # 700
VOLUME_STANDARD_THRESHOLD = VolumeLevel.MODERATE.value  # 300
VOLUME_QUICK_THRESHOLD = VolumeLevel.QUIET.value  # 100

# Volume thresholds for detail level (0-1000 scale)
VOLUME_EXHAUSTIVE_THRESHOLD = 800
VOLUME_DETAILED_THRESHOLD = VolumeLevel.BALANCED.value  # 500

def create_code_quality_task(repo_path: Union[str, Path], context: Dict[str, Any], agent: Any) -> Task:
    """Create a task for code quality analysis."""
    volume = context.get("volume", 500)
    volume_level = get_volume_level_name(volume)
    
    # Determine analysis depth based on volume
    analysis_depth = (
        "thorough" if volume > VOLUME_THOROUGH_THRESHOLD 
        else "standard" if volume > VOLUME_STANDARD_THRESHOLD 
        else "quick"
    )
    detail_level = (
        "exhaustive" if volume > VOLUME_EXHAUSTIVE_THRESHOLD 
        else "detailed" if volume > VOLUME_DETAILED_THRESHOLD 
        else "focused"
    )
    
    return Task(
        description=f"""Analyze code quality at {repo_path} (Volume: {volume_level} {volume}/1000)
        
        Guidelines:
        - Perform {analysis_depth} analysis with {detail_level} detail
        - Focus on critical/high-impact issues
        - Include code examples and improvements
        
        Areas: code smells, performance, security, tests, docs""",
        agent=agent,
        expected_output=f"{detail_level} code quality report with issues and fixes",
        output_json=dict,
        context=context
    )

def create_platform_analysis_task(repo_path: Union[str, Path], context: Dict[str, Any], agent: Any) -> Task:
    """Create a task for platform/tech stack analysis."""
    volume = context.get("volume", VolumeLevel.BALANCED.value)  # Default to balanced (500)
    volume_level = get_volume_level_name(volume)
    
    # Use consistent volume thresholds for determining analysis depth
    analysis_depth = (
        "deep" if volume > VOLUME_THOROUGH_THRESHOLD 
        else "moderate" if volume > VOLUME_STANDARD_THRESHOLD 
        else "light"
    )
    
    return Task(
        description=f"""Analyze tech stack at {repo_path} (Volume: {volume_level} {volume}/1000)
        
        Guidelines:
        - Perform {analysis_depth} analysis
        - Identify frameworks and patterns
        - Check for security and version issues
        
        Focus: Frameworks, architecture, performance, security""",
        agent=agent,
        expected_output=f"{analysis_depth} platform analysis report",
        output_json=PlatformAnalysis.schema(),
        context=context
    )

def create_linting_task(repo_path: Union[str, Path], context: Dict[str, Any], agent: Any) -> Task:
    """Create a task for code linting and style enforcement."""
    volume = context.get("volume", 500)
    strictness = "strict" if volume > 700 else "moderate" if volume > 300 else "relaxed"
    
    return Task(
        description=f"""Lint code at {repo_path} (Strictness: {strictness})
        
        Guidelines:
        - Apply {strictness} linting rules
        - Focus on critical/high-priority issues
        - Include specific fix suggestions
        
        Areas: style, bugs, docs, security, performance""",
        agent=agent,
        expected_output=f"Linting report with {strictness} enforcement",
        output_json=List[CodeIssue],
        context=context
    )

def generate_analysis_summary(
    code_quality: Dict[str, Any],
    platform_analysis: Optional[PlatformAnalysis],
    linting_issues: List[CodeIssue],
    volume: int = VolumeLevel.BALANCED.value  # Default to balanced (500)
) -> Dict[str, Any]:
    """Generate a summary report from analysis results.
    
    Args:
        code_quality: Dictionary containing code quality metrics and summary
        platform_analysis: Optional platform analysis results
        linting_issues: List of linting issues found
        volume: Volume level (0-1000) for detail level control
        
    Returns:
        Dictionary containing the analysis summary and metrics
    """
    summary = ["# Code Analysis Summary\n"]
    
    # Code quality summary with defensive access
    summary.append("## Code Quality")
    summary.append(str(code_quality.get('summary', 'No issues found')))
    
    # Platform analysis summary with defensive checks
    if platform_analysis is not None and hasattr(platform_analysis, 'platform'):
        platform_name = getattr(platform_analysis, 'platform', 'unknown')
        confidence = getattr(platform_analysis, 'confidence', 0.0)
        components = getattr(platform_analysis, 'components', [])
        recommendations = getattr(platform_analysis, 'recommendations', [])
        
        summary.extend([
            "\n## Platform Analysis",
            f"- Platform: {platform_name} (confidence: {confidence:.1%})",
            "- Components:" + ("\n  - " + "\n  - ".join(components) if components else " None"),
            "- Recommendations:" + ("\n  - " + "\n  - ".join(recommendations) if recommendations else " None")
        ])
    
    # Linting issues summary
    if linting_issues:
        severity_counts = _count_issues_by_severity(linting_issues)
        summary.extend([
            "\n## Linting Results",
            f"- Issues found: {len(linting_issues)}",
            f"- By severity: {severity_counts}"
        ])
    
    # Add recommendations based on volume level
    if volume < VOLUME_STANDARD_THRESHOLD:  # 300
        summary.append(f"\nNote: Increase volume above {VOLUME_STANDARD_THRESHOLD} for more detailed analysis")
    
    # Prepare platform analysis data with safe attribute access
    platform_data = {
        "platform": getattr(platform_analysis, 'platform', 'unknown') if platform_analysis else "unknown",
        "confidence": float(getattr(platform_analysis, 'confidence', 0.0)) if platform_analysis else 0.0,
        "components": list(getattr(platform_analysis, 'components', []) if platform_analysis else []),
        "recommendations": list(getattr(platform_analysis, 'recommendations', []) if platform_analysis else [])
    }
    
    return {
        "summary": "\n".join(summary),
        "metrics": dict(code_quality.get("metrics", {})),
        "issues": list(linting_issues),
        "platform_analysis": platform_data
    }

def _count_issues_by_severity(issues: List[CodeIssue]) -> str:
    """Count issues by severity and return formatted string."""
    from collections import defaultdict
    counts = defaultdict(int)
    for issue in issues:
        counts[issue.severity] += 1
    
    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    sorted_counts = sorted(
        counts.items(),
        key=lambda x: severity_order.index(x[0]) if x[0] in severity_order else 99
    )
    
    return ", ".join(f"{count} {sev}" for sev, count in sorted_counts)
