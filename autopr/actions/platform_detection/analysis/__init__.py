"""
File Analysis Module

Provides a modular system for analyzing files and directories to detect platform-specific patterns.
"""

from typing import Dict, Optional, Type

from autopr.actions.platform_detection.analysis.base import FileAnalysisResult, FileAnalyzer
from autopr.actions.platform_detection.analysis.handlers import (
    DefaultFileHandler,
    DockerfileHandler,
    FileHandler,
    JsonFileHandler,
    PackageJsonHandler,
    PythonFileHandler,
    RequirementsFileHandler,
    YamlFileHandler,
)
from autopr.actions.platform_detection.analysis.patterns import (
    ContentPattern,
    DirectoryPattern,
    FilePattern,
)

__all__ = [
    "ContentPattern",
    "DirectoryPattern",
    "FileAnalysisResult",
    "FileAnalyzer",
    "FileHandler",
    "FilePattern",
]

# Default file handlers for common file types
DEFAULT_HANDLERS = {
    "*.json": JsonFileHandler,
    "*.yaml": YamlFileHandler,
    "*.yml": YamlFileHandler,
    "*.py": PythonFileHandler,
    "requirements*.txt": RequirementsFileHandler,
    "package.json": PackageJsonHandler,
    "Dockerfile": DockerfileHandler,
    "*": DefaultFileHandler,  # Catch-all handler
}


def create_file_analyzer(
    workspace_path: str = ".",
    handlers: dict[str, type[FileHandler]] | None = None,
) -> FileAnalyzer:
    """
    Create a configured FileAnalyzer instance with default handlers.

    Args:
        workspace_path: Path to the workspace to analyze
        handlers: Optional mapping of file patterns to handler classes

    Returns:
        Configured FileAnalyzer instance
    """
    if handlers is None:
        handlers = DEFAULT_HANDLERS

    return FileAnalyzer(workspace_path, handlers)
