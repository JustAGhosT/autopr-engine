"""
AI-Enhanced Quality Analysis Modes

This module provides AI-powered code analysis capabilities for the Quality Engine,
integrating with the AutoPR LLM provider system.
"""

import json
from typing import Any

import structlog

from autopr.actions.llm.manager import ActionLLMProviderManager as LLMProviderManager
from autopr.actions.quality_engine.models import ToolResult
from autopr.agents.models import CodeIssue


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

SECURITY_PROMPT = """You are SecurityGPT, an expert in application security and secure coding practices.
Analyze this code for security vulnerabilities, focusing on:

1. Input validation and sanitization
2. Authentication and authorization
3. Data encryption and protection
4. Common vulnerabilities (SQL injection, XSS, CSRF, etc.)
5. Secure coding practices
6. Compliance considerations

Provide security analysis in a structured JSON format with severity levels.
"""


async def run_ai_analysis(
    files: list[str],
    llm_manager: LLMProviderManager,
    provider_name: str = "openai",
    model: str = "gpt-4",
    prompt: str = CODE_REVIEW_PROMPT,
) -> dict[str, Any] | None:
    """
    Run AI-enhanced analysis on the provided files.

    Args:
        files: List of file paths to analyze
        llm_manager: LLM provider manager
        provider_name: Name of the LLM provider to use
        model: Model name to use for analysis

    Returns:
        Dict containing AI analysis results or None if analysis fails
    """
    try:
        if not files:
            logger.warning("No files provided for AI analysis")
            return None

        # Read file contents
        file_contents = {}
        for file_path in files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    file_contents[file_path] = f.read()
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {e}")
                continue

        if not file_contents:
            logger.warning("No files could be read for AI analysis")
            return None

        # Create analysis prompt
        analysis_prompt = _create_analysis_prompt(file_contents)

        # Get LLM response
        request = {
            "provider": provider_name,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": analysis_prompt},
            ],
            "temperature": 0.1,
        }
        response = llm_manager.complete(request)

        if not response or not response.content:
            logger.warning("No response received from LLM")
            return None

        # Parse response
        try:
            # Extract JSON from response
            content = response.content.strip()
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                if json_end != -1:
                    content = content[json_start:json_end].strip()

            ai_result = json.loads(content)

            # Add metadata
            ai_result["files_analyzed"] = list(file_contents.keys())
            ai_result["provider"] = provider_name
            ai_result["model"] = model

            logger.info(f"AI analysis completed for {len(file_contents)} files")
            return ai_result

        except json.JSONDecodeError as e:
            logger.exception(f"Failed to parse AI response as JSON: {e}")
            # Return a fallback result
            return {
                "suggestions": [],
                "summary": "AI analysis completed but response format was invalid",
                "priorities": [],
                "files_analyzed": list(file_contents.keys()),
                "provider": provider_name,
                "model": model,
                "error": "JSON parsing failed",
            }

    except Exception as e:
        logger.exception(f"AI analysis failed: {e}")
        return None


def create_tool_result_from_ai_analysis(ai_result: dict[str, Any]) -> ToolResult:
    """
    Convert AI analysis result to a ToolResult.

    Args:
        ai_result: AI analysis result dictionary

    Returns:
        ToolResult: Converted tool result
    """
    issues = []

    # Convert AI suggestions to issues
    suggestions = ai_result.get("suggestions", [])
    for suggestion in suggestions:
        issue = CodeIssue(
            file_path=suggestion.get("file", "unknown"),
            line_number=suggestion.get("line", 0),
            column=suggestion.get("column", 0),
            message=suggestion.get("issue", "AI suggestion"),
            severity="info" if suggestion.get("confidence", 0) < 0.7 else "warning",
            rule_id=suggestion.get("category", "AI_SUGGESTION"),
            category="ai_suggestion",
            fix=(
                {
                    "suggestion": suggestion.get("fix", ""),
                    "confidence": suggestion.get("confidence", 0.5),
                }
                if suggestion.get("fix")
                else None
            ),
        )
        issues.append(issue)

    # Create tool result
    return ToolResult(
        issues=[issue.model_dump() for issue in issues],
        files_with_issues=list({issue.file_path for issue in issues}),
        summary=ai_result.get("summary", "AI analysis completed"),
        execution_time=0.0,  # AI analysis time is not tracked separately
    )


def _create_analysis_prompt(file_contents: dict[str, str]) -> str:
    """
    Create a prompt for AI analysis of the provided files.

    Args:
        file_contents: Dictionary mapping file paths to their contents

    Returns:
        str: Analysis prompt
    """
    prompt_parts = [
        "Please analyze the following code files for quality issues, improvements, and potential problems:",
        "",
    ]

    for file_path, content in file_contents.items():
        # Use smart truncation to preserve syntactic boundaries
        truncated_content = _smart_truncate_content(content, max_length=2000)
        prompt_parts.extend(
            [
                f"## File: {file_path}",
                "```",
                truncated_content,
                "```",
                "",
            ]
        )

    prompt_parts.extend(
        [
            "Please provide a comprehensive analysis including:",
            "1. Code quality issues and suggestions",
            "2. Performance optimization opportunities",
            "3. Security considerations",
            "4. Maintainability improvements",
            "5. Architecture and design patterns",
            "",
            "Format your response as JSON with the structure specified in the system prompt.",
        ]
    )

    return "\n".join(prompt_parts)


def _smart_truncate_content(content: str, max_length: int = 2000) -> str:
    """
    Smartly truncate content while preserving syntactic boundaries.

    Args:
        content: The content to truncate
        max_length: Maximum length in characters

    Returns:
        Truncated content that preserves code structure
    """
    if len(content) <= max_length:
        return content

    # Try to find a good truncation point
    lines = content.split("\n")
    current_length = 0
    truncated_lines = []

    for line in lines:
        # Check if adding this line would exceed the limit
        if current_length + len(line) + 1 > max_length:
            # Try to find a better break point within this line
            if len(line) > 100:  # Long line, try to break at word boundary
                words = line.split()
                partial_line = ""
                for word in words:
                    if current_length + len(partial_line) + len(word) + 1 <= max_length:
                        partial_line += word + " "
                    else:
                        break
                if partial_line.strip():
                    truncated_lines.append(partial_line.strip())
                break
            else:
                # Line is short, just add it and stop
                truncated_lines.append(line)
                break
        else:
            truncated_lines.append(line)
            current_length += len(line) + 1

    truncated_content = "\n".join(truncated_lines)

    # Add truncation indicator if content was actually truncated
    if len(content) > len(truncated_content):
        truncated_content += f"\n\n... (content truncated, showing first {len(truncated_content)} characters)"

    return truncated_content


def _create_chunked_analysis_prompt(
    file_contents: dict[str, str], max_chunk_size: int = 2000
) -> list[str]:
    """
    Create multiple analysis prompts for large files by chunking them intelligently.

    Args:
        file_contents: Dictionary mapping file paths to their contents
        max_chunk_size: Maximum size per chunk in characters

    Returns:
        List of analysis prompts for different chunks
    """
    prompts = []

    for file_path, content in file_contents.items():
        if len(content) <= max_chunk_size:
            # Small file, create single prompt
            prompts.append(_create_analysis_prompt({file_path: content}))
        else:
            # Large file, split into chunks
            chunks = _split_content_into_chunks(content, max_chunk_size)
            for i, chunk in enumerate(chunks):
                chunk_prompt = _create_analysis_prompt(
                    {f"{file_path} (part {i+1}/{len(chunks)})": chunk}
                )
                prompts.append(chunk_prompt)

    return prompts


def _split_content_into_chunks(content: str, max_chunk_size: int) -> list[str]:
    """
    Split content into overlapping chunks while preserving code structure.

    Args:
        content: The content to split
        max_chunk_size: Maximum size per chunk

    Returns:
        List of content chunks
    """
    if len(content) <= max_chunk_size:
        return [content]

    lines = content.split("\n")
    chunks = []
    current_chunk = []
    current_length = 0
    overlap_lines = 10  # Number of lines to overlap between chunks

    for line in lines:
        if current_length + len(line) + 1 > max_chunk_size and current_chunk:
            # Current chunk is full, save it and start a new one
            chunks.append("\n".join(current_chunk))

            # Start new chunk with overlap
            overlap_start = max(0, len(current_chunk) - overlap_lines)
            current_chunk = current_chunk[overlap_start:]
            current_length = sum(len(l) + 1 for l in current_chunk)

        current_chunk.append(line)
        current_length += len(line) + 1

    # Add the last chunk
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


async def analyze_code_architecture(
    files: list[str], llm_manager: LLMProviderManager, provider_name: str = "openai"
) -> dict[str, Any] | None:
    """
    Run architectural analysis on the provided files.

    Args:
        files: List of file paths to analyze
        llm_manager: LLM provider manager
        provider_name: Name of the LLM provider to use

    Returns:
        Dict containing architectural analysis results
    """
    # Use specialized architecture analysis prompt
    return await run_ai_analysis(files, llm_manager, provider_name, prompt=ARCHITECTURE_PROMPT)


async def analyze_security_issues(
    files: list[str], llm_manager: LLMProviderManager, provider_name: str = "openai"
) -> dict[str, Any] | None:
    """
    Run security analysis on the provided files.

    Args:
        files: List of file paths to analyze
        llm_manager: LLM provider manager
        provider_name: Name of the LLM provider to use

    Returns:
        Dict containing security analysis results
    """
    # Use specialized security analysis prompt
    return await run_ai_analysis(files, llm_manager, provider_name, prompt=SECURITY_PROMPT)
