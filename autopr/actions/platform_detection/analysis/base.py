"""
Base classes and interfaces for file analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import fnmatch
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from autopr.actions.platform_detection.analysis.handlers import FileHandler

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="FileAnalyzer")


@dataclass
class FileAnalysisResult:
    """Results from analyzing a file or directory."""

    path: Path
    """Path to the analyzed file or directory."""

    platform_matches: dict[str, float] = field(default_factory=dict)
    """Mapping of platform IDs to confidence scores (0.0 to 1.0)."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the analysis."""

    def add_match(self, platform_id: str, confidence: float) -> None:
        """Add a platform match with the given confidence."""
        if confidence <= 0:
            return

        current_confidence = self.platform_matches.get(platform_id, 0.0)
        self.platform_matches[platform_id] = max(current_confidence, confidence)

    def merge(self, other: FileAnalysisResult) -> None:
        """Merge another result into this one."""
        for platform_id, confidence in other.platform_matches.items():
            self.add_match(platform_id, confidence)

        # Merge metadata
        for key, value in other.metadata.items():
            if key not in self.metadata:
                self.metadata[key] = value


class FileAnalyzer:
    """
    Modular file analyzer that uses specialized handlers for different file types.

    This class coordinates the analysis of files and directories using a set of
    registered file handlers that know how to process specific file types.
    """

    def __init__(
        self,
        workspace_path: str | Path,
        handlers: dict[str, type[FileHandler]] | None = None,
    ):
        """
        Initialize the file analyzer.

        Args:
            workspace_path: Path to the workspace to analyze
            handlers: Mapping of file patterns to handler classes
        """
        self.workspace_path = Path(workspace_path).resolve()
        self.handlers: dict[str, type[FileHandler]] = {}
        self._initialize_handlers(handlers or {})

    def _initialize_handlers(self, handlers: dict[str, type[FileHandler]]) -> None:
        """Initialize the file handlers."""

        self._handler_patterns: list[tuple[Any, type[FileHandler]]] = []

        for pattern, handler_cls in handlers.items():
            self.register_handler(pattern, handler_cls)

    def register_handler(
        self,
        pattern: str,
        handler_cls: type[FileHandler],
    ) -> None:
        """Register a handler for files matching the given pattern."""
        # Import here to avoid circular import
        from autopr.actions.platform_detection.analysis.handlers import FileHandler

        if not issubclass(handler_cls, FileHandler):
            msg = f"Handler must be a subclass of FileHandler, got {handler_cls}"
            raise ValueError(msg)

        self.handlers[pattern] = handler_cls

        # Pre-compile the pattern for faster matching
        import re

        regex = fnmatch.translate(pattern)
        self._handler_patterns.append((re.compile(regex), handler_cls))

    def get_handler_for_file(self, file_path: Path) -> FileHandler | None:
        """Get the appropriate handler for the given file."""
        filename = file_path.name

        # Check for exact matches first
        for pattern, handler_cls in self.handlers.items():
            if pattern == filename or pattern == f"*.{file_path.suffix.lstrip('.')}":
                return handler_cls()

        # Then check glob patterns
        for pattern, handler_cls in self.handlers.items():
            if fnmatch.fnmatch(filename, pattern):
                return handler_cls()

        # Default to the catch-all handler if available
        return self.handlers.get("*", DefaultFileHandler)()

    def analyze_file(self, file_path: Path) -> FileAnalysisResult:
        """
        Analyze a single file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            FileAnalysisResult containing the analysis results
        """
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        if not file_path.is_file():
            msg = f"Path is not a file: {file_path}"
            raise ValueError(msg)

        handler = self.get_handler_for_file(file_path)
        if handler is None:
            logger.debug(f"No handler found for file: {file_path}")
            return FileAnalysisResult(file_path)

        try:
            return handler.analyze(file_path, self)
        except Exception as e:
            logger.exception(f"Error analyzing file {file_path}: {e}")
            return FileAnalysisResult(file_path, metadata={"error": str(e)})

    def analyze_directory(
        self,
        dir_path: Path | None = None,
        exclude_dirs: set[str] | None = None,
        exclude_files: set[str] | None = None,
        max_depth: int = 5,
    ) -> list[FileAnalysisResult]:
        """
        Recursively analyze all files in a directory.

        Args:
            dir_path: Directory to analyze (defaults to workspace root)
            exclude_dirs: Set of directory names to exclude
            exclude_files: Set of file patterns to exclude
            max_depth: Maximum depth to recurse

        Returns:
            List of FileAnalysisResult objects, one per analyzed file
        """
        if dir_path is None:
            dir_path = self.workspace_path

        if not dir_path.exists():
            msg = f"Directory not found: {dir_path}"
            raise FileNotFoundError(msg)

        if not dir_path.is_dir():
            msg = f"Path is not a directory: {dir_path}"
            raise ValueError(msg)

        if exclude_dirs is None:
            exclude_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}

        if exclude_files is None:
            exclude_files = {"*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll", "*.exe"}

        results = []

        try:
            for entry in dir_path.iterdir():
                if entry.name.startswith("."):
                    continue

                if entry.is_dir() and entry.name not in exclude_dirs and max_depth > 0:
                    try:
                        results.extend(
                            self.analyze_directory(
                                entry, exclude_dirs, exclude_files, max_depth - 1
                            )
                        )
                    except Exception as e:
                        logger.exception(f"Error analyzing directory {entry}: {e}")

                elif entry.is_file() and not any(
                    fnmatch.fnmatch(entry.name, pattern) for pattern in exclude_files
                ):
                    try:
                        results.append(self.analyze_file(entry))
                    except Exception as e:
                        logger.exception(f"Error analyzing file {entry}: {e}")

        except PermissionError as e:
            logger.warning(f"Permission denied accessing {dir_path}: {e}")

        return results
