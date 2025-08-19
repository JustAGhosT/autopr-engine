"""
Pattern classes for platform detection.
"""

from dataclasses import dataclass
from pathlib import Path
import re
from re import Pattern


@dataclass
class BasePattern:
    """Base class for all pattern types."""

    platform_id: str
    """ID of the platform this pattern matches."""

    confidence: float = 1.0
    """Confidence score (0.0 to 1.0) that this pattern indicates the platform."""

    def __post_init__(self):
        """Validate the pattern after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            msg = f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            raise ValueError(msg)


@dataclass
class ContentPattern:
    """Pattern for matching content within files."""

    pattern: str | Pattern[str]
    """The regex pattern to search for in file content."""

    platform_id: str
    """ID of the platform this pattern matches."""

    confidence: float = 1.0
    """Confidence score (0.0 to 1.0) that this pattern indicates the platform."""

    def __post_init__(self):
        """Compile the regex pattern if it's a string."""
        if not 0.0 <= self.confidence <= 1.0:
            msg = f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            raise ValueError(msg)
        if isinstance(self.pattern, str):
            self._compiled = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)
        else:
            self._compiled = self.pattern

    def matches(self, content: str) -> bool:
        """Check if the pattern matches the given content."""
        return bool(self._compiled.search(content))


@dataclass
class FilePattern:
    """Pattern for matching file names and paths."""

    pattern: str
    """The glob pattern to match against file names."""

    platform_id: str
    """ID of the platform this pattern matches."""

    confidence: float = 1.0
    """Confidence score (0.0 to 1.0) that this pattern indicates the platform."""

    def __post_init__(self):
        """Validate the pattern after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            msg = f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            raise ValueError(msg)

    def matches(self, file_path: Path) -> bool:
        """Check if the pattern matches the given file path."""
        from fnmatch import fnmatch

        return fnmatch(file_path.name, self.pattern)


@dataclass
class DirectoryPattern:
    """Pattern for matching directory structures."""

    pattern: str
    """The glob pattern to match against directory paths."""

    platform_id: str
    """ID of the platform this pattern matches."""

    confidence: float = 1.0
    """Confidence score (0.0 to 1.0) that this pattern indicates the platform."""

    def __post_init__(self):
        """Validate the pattern after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            msg = f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            raise ValueError(msg)

    def matches(self, dir_path: Path) -> bool:
        """Check if the pattern matches the given directory path."""
        from fnmatch import fnmatch

        return fnmatch(str(dir_path), self.pattern)


@dataclass
class CompositePattern:
    """Combines multiple patterns with logical operators."""

    patterns: list[BasePattern]
    """List of patterns to combine."""

    platform_id: str
    """ID of the platform this pattern matches."""

    confidence: float = 1.0
    """Confidence score (0.0 to 1.0) that this pattern indicates the platform."""

    operator: str = "and"
    """Logical operator to combine patterns ("and" or "or")."""

    def __post_init__(self):
        """Validate the operator."""
        if not 0.0 <= self.confidence <= 1.0:
            msg = f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            raise ValueError(msg)
        if self.operator not in {"and", "or"}:
            msg = f"Operator must be 'and' or 'or', got {self.operator}"
            raise ValueError(msg)

    def matches(self, target) -> bool:
        """Check if the combined patterns match the target."""
        if not self.patterns:
            return False

        results = [p.matches(target) for p in self.patterns]

        if self.operator == "and":
            return all(results)
        # "or"
        return any(results)
