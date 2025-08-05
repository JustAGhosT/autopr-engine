"""Task creation and summary generation for the AutoPR Agent Framework."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from crewai import Task
from autopr.agents.models import CodeIssue, PlatformAnalysis
from autopr.actions.quality_engine.volume_mapping import get_volume_config, get_volume_level_name

def create_code_quality_task(repo_path: Union[str, Path], context: Dict[str, Any], agent: Any) -> Task:
    """Create a task for code quality analysis."""
    volume = context.get("volume", 500)
    volume_config = get_volume_config(volume)
    volume_level = get_volume_level_name(volume)
    
    analysis_depth = "thorough" if volume > 700 else "standard" if volume > 300 else "quick"
    detail_level = "exhaustive" if volume > 800 else "detailed" if volume > 500 else "focused"
    
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
    volume = context.get("volume", 500)
    volume_level = get_volume_level_name(volume)
    analysis_depth = "deep" if volume > 700 else "moderate" if volume > 300 else "light"
    
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
    volume: int = 500
) -> Dict[str, Any]:
    """Generate a summary report from analysis results."""
    summary = ["# Code Analysis Summary\n"]
    
    # Code quality summary
    summary.append("## Code Quality")
    summary.append(code_quality.get('summary', 'No issues found'))
    
    # Platform analysis summary
    if platform_analysis:
        summary.extend([
            "\n## Platform Analysis",
            f"- Platform: {platform_analysis.platform} ({platform_analysis.confidence*100:.1f}%)",
            f"- Components: {len(platform_analysis.components)}"
        ])
    
    # Linting summary
    if linting_issues:
        severity_counts = _count_issues_by_severity(linting_issues)
        summary.extend([
            "\n## Linting Results",
            f"- Issues found: {len(linting_issues)}",
            f"- By severity: {severity_counts}"
        ])
    
    # Add recommendations
    if volume < 300:
        summary.append("\nNote: Increase volume for more detailed analysis")
    
    return {
        "summary": "\n".join(summary),
        "metrics": code_quality.get("metrics", {}),
        "issues": linting_issues,
        "platform_analysis": platform_analysis or {
            "platform": "unknown",
            "confidence": 0.0,
            "components": [],
            "recommendations": []
        }
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
