"""
AI-Enhanced Quality Analysis Modes

This module provides AI-powered code analysis capabilities for the Quality Engine,
integrating with the AutoPR LLM provider system.
"""

import os
from typing import Any

import structlog

from autopr.ai.providers.manager import LLMProviderManager

from .ai_analyzer import AICodeAnalyzer

logger = structlog.get_logger(__name__)

# System prompt templates
CODE_REVIEW_PROMPT = """You are CodeQualityGPT, an expert code review assistant specialized in identifying improvements, 
optimizations, and potential issues in code. Your task is to analyze code snippets and provide detailed, 
actionable feedback that goes beyond what static analysis tools can find.

Focus on the following aspects:
1. Architecture and design patterns
2. Performance optimization opportunities 
3. Security vulnerabilities or risks
4. Maintainability and readability concerns
5. Edge case handling and robustness
6. Business logic flaws or inconsistencies
7. API design and usability

Provide your feedback in a structured JSON format with:
- Specific issues identified
- Why they matter
- How to fix them
- A confidence score (0-1) for each suggestion

Format your response as JSON:
```json
{
  "suggestions": [
    {
      "line": 42,
      "issue": "Inefficient algorithm implementation",
      "explanation": "The current approach has O(n²) complexity but could be optimized to O(n log n).",
      "fix": "Use a more efficient sorting algorithm like quicksort instead of bubble sort.",
      "category": "performance",
      "confidence": 0.9
    }
  ],
  "summary": "Overall code quality assessment and key improvement areas.",
  "priorities": ["Top 3 most important issues to address"]
}
```
"""

ARCHITECTURE_PROMPT = """You are CodeArchitectGPT, an expert in software architecture and design patterns.
Analyze this codebase from an architectural perspective, identifying:

1. Design pattern usage and opportunities
2. Component interactions and dependencies
3. Architectural smells or anti-patterns
4. Modularization and separation of concerns
5. Potential architectural improvements

Provide detailed architectural insights in a structured JSON format.
"""

SECURITY_PROMPT = """You are SecurityGPT, a specialized AI focused on identifying security vulnerabilities and risks in code.
Perform a thorough security analysis, identifying:

1. Common vulnerability patterns (OWASP Top 10 relevant issues)
2. Input validation concerns
3. Authentication/authorization weaknesses
4. Data protection issues
5. Security best practices violations

Provide detailed security insights in a structured JSON format.
"""


async def run_ai_analysis(
    files: list[str],
    llm_manager: LLMProviderManager,
    provider_name: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Run AI-enhanced code analysis on the provided files.

    Args:
        files: List of file paths to analyze
        llm_manager: LLM provider manager instance
        provider_name: Optional specific LLM provider to use
        model: Optional specific model to use

    Returns:
        Dictionary containing AI analysis results
    """
    # Filter files to only include code files that are appropriate for AI analysis
    code_file_extensions = [
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".go",
        ".rb",
        ".php",
        ".c",
        ".cpp",
        ".cs",
        ".h",
        ".hpp",
        ".html",
        ".css",
    ]

    # Filter files to code files with a reasonable size for LLM analysis (< 100KB)
    files_for_analysis = []
    for file_path in files:
        extension = os.path.splitext(file_path)[1]
        try:
            # Skip non-code files
            if extension not in code_file_extensions:
                continue

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024:  # 100 KB
                logger.info(
                    "Skipping large file for AI analysis", file_path=file_path, size=file_size
                )
                continue

            files_for_analysis.append(file_path)
        except Exception as e:
            logger.error("Error checking file for AI analysis", file_path=file_path, error=str(e))

    # If no files are suitable for analysis, return empty results
    if not files_for_analysis:
        logger.warning("No suitable files for AI analysis")
        return {
            "issues": [],
            "files_with_issues": [],
            "summary": "No suitable files found for AI analysis.",
        }

    # Limit the number of files to analyze to avoid overloading the LLM
    max_files_to_analyze = 10
    if len(files_for_analysis) > max_files_to_analyze:
        logger.info(f"Limiting AI analysis to {max_files_to_analyze} files")
        # Prioritize smaller files that are more likely to be fully processed
        files_for_analysis = sorted(files_for_analysis, key=lambda f: os.path.getsize(f))[
            :max_files_to_analyze
        ]

    # Create an AI code analyzer and run the analysis
    analyzer = AICodeAnalyzer(llm_manager)

    logger.info(f"Starting AI analysis of {len(files_for_analysis)} files")
    results = await analyzer.analyze_files(files_for_analysis, provider_name, model)

    # Convert the results to the format expected by the quality engine
    tool_results = analyzer.convert_to_tool_results(results)

    # Add file statistics
    tool_results["total_files_analyzed"] = len(files_for_analysis)
    tool_results["total_files_with_issues"] = len(tool_results["files_with_issues"])

    # Create a consolidated summary of all issues
    summary_lines = ["# AI-Enhanced Code Analysis"]
    summary_lines.append(
        f"\nAnalyzed {len(files_for_analysis)} files. Found {len(tool_results['issues'])} potential improvements in {len(tool_results['files_with_issues'])} files."
    )

    # Add category-based summary
    categories = {}
    for issue in tool_results["issues"]:
        category = issue.get("category", "general")
        if category not in categories:
            categories[category] = 0
        categories[category] += 1

    if categories:
        summary_lines.append("\n## Issues by Category")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            summary_lines.append(f"- {category}: {count} issues")

    # Add high-confidence issues
    high_confidence_issues = [i for i in tool_results["issues"] if i.get("confidence", 0) > 0.8]
    if high_confidence_issues:
        summary_lines.append("\n## High Confidence Suggestions")
        for issue in sorted(
            high_confidence_issues, key=lambda x: x.get("confidence", 0), reverse=True
        )[:5]:
            file = issue.get("file", "unknown")
            line = issue.get("line", "?")
            message = issue.get("message", "Unknown issue")
            confidence = issue.get("confidence", 0)
            summary_lines.append(f"- {file}:{line} - {message} (Confidence: {confidence:.2f})")

    # Add file summaries
    if results:
        summary_lines.append("\n## File Summaries")
        for file_path, result in results.items():
            if result.get("summary"):
                summary_lines.append(f"\n### {os.path.basename(file_path)}")
                summary_lines.append(result["summary"])

    tool_results["summary"] = "\n".join(summary_lines)

    return tool_results


async def analyze_code_architecture(
    files: list[str],
    llm_manager: LLMProviderManager,
    provider_name: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Perform architectural analysis of the codebase using LLM.

    This function analyzes multiple files to identify architectural patterns,
    dependencies, and potential improvements.

    Args:
        files: List of file paths to analyze
        llm_manager: LLM provider manager
        provider_name: Optional specific provider to use
        model: Optional specific model to use

    Returns:
        Dictionary with architectural analysis results
    """
    # Implementation would be similar to run_ai_analysis but with architecture-specific prompts
    logger.info("Architecture analysis is not yet fully implemented")
    return {"message": "Architecture analysis will be implemented in a future version"}


async def analyze_security_issues(
    files: list[str],
    llm_manager: LLMProviderManager,
    provider_name: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Perform security-focused analysis of the codebase using LLM.

    This function specializes in identifying security vulnerabilities and risks
    that might not be caught by standard security scanning tools.

    Args:
        files: List of file paths to analyze
        llm_manager: LLM provider manager
        provider_name: Optional specific provider to use
        model: Optional specific model to use

    Returns:
        Dictionary with security analysis results
    """
    # Implementation would be similar to run_ai_analysis but with security-specific prompts
    logger.info("Security analysis is not yet fully implemented")
    return {"message": "Security analysis will be implemented in a future version"}
