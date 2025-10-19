"""
Base classes and interfaces for quality tools used by the Quality Engine.
"""

import abc
from enum import Enum

import pydantic
from structlog import get_logger

from autopr.enums import QualityMode


logger = get_logger(__name__)


class ToolCategory(Enum):
    """Categories of quality tools"""

    FORMATTING = "formatting"
    LINTING = "linting"
    TYPE_CHECKING = "type_checking"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    COMPLEXITY = "complexity"
    TESTING = "testing"
    DEPENDENCY = "dependency"
    AI_ENHANCED = "ai_enhanced"


class ToolResult(pydantic.BaseModel):
    """Results from running a quality tool"""

    success: bool
    issues_found: int
    issues_fixed: int
    files_analyzed: list[str]
    files_modified: list[str]
    error_message: str | None = None
    logs: list[str] = []
    tool_name: str
    tool_category: ToolCategory
    execution_time_ms: int


class QualityToolConfig(pydantic.BaseModel):
    """Base configuration for quality tools"""

    enabled: bool = True
    modes: set[QualityMode] = {QualityMode.COMPREHENSIVE, QualityMode.SMART}
    auto_fix: bool = True
    max_issues: int | None = None
    timeout_seconds: int = 60
    exclude_patterns: list[str] = []
    include_patterns: list[str] = []


class QualityTool(abc.ABC):
    """Base class for all quality tools"""

    def __init__(self, config: QualityToolConfig | None = None):
        self.config = config or QualityToolConfig()
        self.logger = get_logger(self.__class__.__name__)
        # Pre-compile patterns for better performance
        self._compiled_exclude_patterns = self._compile_patterns(self.config.exclude_patterns)
        self._compiled_include_patterns = self._compile_patterns(self.config.include_patterns) if self.config.include_patterns else []

    def _compile_patterns(self, patterns: list[str]) -> list[Any]:
        """Compile patterns for faster matching."""
        import re
        compiled = []
        for pattern in patterns:
            # Check if it's a glob pattern (contains *, ?, [, ])
            if any(char in pattern for char in '*?[]'):
                # For glob patterns, we'll use fnmatch which handles them properly
                compiled.append(('glob', pattern))
            else:
                # For simple string patterns, compile as regex for speed
                try:
                    compiled.append(('regex', re.compile(pattern)))
                except re.error:
                    # Fallback to simple string matching if regex compilation fails
                    compiled.append(('string', pattern))
        return compiled

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of the tool"""

    @property
    @abc.abstractmethod
    def category(self) -> ToolCategory:
        """Return the category of the tool"""

    @property
    def modes(self) -> set[QualityMode]:
        """Return the modes this tool supports"""
        return self.config.modes

    def supports_mode(self, mode: QualityMode) -> bool:
        """Check if the tool supports a specific mode"""
        return mode in self.modes

    @abc.abstractmethod
    async def check(self, files: list[str] | None = None) -> ToolResult:
        """Run the tool in check-only mode"""

    @abc.abstractmethod
    async def fix(self, files: list[str] | None = None) -> ToolResult:
        """Run the tool in fix mode"""

    async def run(
        self, files: list[str] | None = None, *, auto_fix: bool | None = None
    ) -> ToolResult:
        """Run the tool based on configuration"""
        should_fix = self.config.auto_fix if auto_fix is None else auto_fix

        try:
            if should_fix:
                return await self.fix(files)
            return await self.check(files)
        except Exception as e:
            self.logger.exception("Error running %s", self.name)
            return ToolResult(
                success=False,
                issues_found=0,
                issues_fixed=0,
                files_analyzed=[],
                files_modified=[],
                error_message=str(e),
                logs=[f"Exception: {e!s}"],
                tool_name=self.name,
                tool_category=self.category,
                execution_time_ms=0,
            )

    def filter_files(self, files: list[str]) -> list[str]:
        """Filter files based on include/exclude patterns using pre-compiled patterns"""
        if not files:
            return []

        result = files.copy()

        # Apply exclusions using pre-compiled patterns
        for pattern_type, pattern in self._compiled_exclude_patterns:
            filtered_result = []
            for file_path in result:
                should_exclude = False

                if pattern_type == 'glob':
                    # Use fnmatch for glob patterns
                    import fnmatch
                    should_exclude = fnmatch.fnmatch(file_path, pattern)
                elif pattern_type == 'regex':
                    should_exclude = pattern.search(file_path) is not None
                else:  # string pattern
                    should_exclude = pattern in file_path

                if not should_exclude:
                    filtered_result.append(file_path)
            result = filtered_result

        # Apply inclusions if specified using pre-compiled patterns
        if self._compiled_include_patterns:
            filtered_result = []
            for file_path in result:
                should_include = False

                for pattern_type, pattern in self._compiled_include_patterns:
                    if pattern_type == 'glob':
                        # Use fnmatch for glob patterns
                        import fnmatch
                        if fnmatch.fnmatch(file_path, pattern):
                            should_include = True
                            break
                    elif pattern_type == 'regex':
                        if pattern.search(file_path) is not None:
                            should_include = True
                            break
                    else:  # string pattern
                        if pattern in file_path:
                            should_include = True
                            break

                if should_include:
                    filtered_result.append(file_path)
            result = filtered_result

        return result
