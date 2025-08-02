"""
Platform detection and tool adaptation for the Quality Engine.
"""

import platform
import sys

import structlog

logger = structlog.get_logger(__name__)


class PlatformDetector:
    """Detects the current platform and provides tool adaptations."""

    def __init__(self) -> None:
        self.platform = platform.system().lower()
        self.is_windows = self.platform == "windows"
        self.is_linux = self.platform == "linux"
        self.is_macos = self.platform == "darwin"

    def detect_platform(self) -> dict[str, any]:
        """Detect the current platform and its capabilities."""
        return {
            "platform": self.platform,
            "is_windows": self.is_windows,
            "is_linux": self.is_linux,
            "is_macos": self.is_macos,
            "python_version": sys.version,
            "architecture": platform.architecture()[0],
        }

    def get_windows_limitations(self) -> list[str]:
        """Get list of tools that have limitations on Windows."""
        limitations = []

        if self.is_windows:
            limitations.extend(
                [
                    "CodeQL - Not available on Windows (GitHub CLI required)",
                    "Some Docker-based tools may have performance issues",
                    "Some Unix-specific tools may not work",
                ]
            )

        return limitations

    def get_windows_alternatives(self) -> dict[str, list[str]]:
        """Get Windows alternatives for tools that don't work well on Windows."""
        return {
            "codeql": [
                "semgrep - Cross-platform static analysis for security (RECOMMENDED)",
                "bandit - Python security linting",
                "safety - Dependency vulnerability scanning",
                "windows_security - Comprehensive Windows security scanner",
            ],
            "docker_tools": [
                "native_windows_tools - Use Windows-native alternatives",
                "wsl2 - Windows Subsystem for Linux for Docker support",
            ],
        }

    def get_available_tools(self, all_tools: list[str]) -> list[str]:
        """Filter tools based on platform compatibility."""
        if not self.is_windows:
            return all_tools

        # Tools that work well on Windows
        windows_compatible = {
            "ruff",
            "mypy",
            "bandit",
            "interrogate",
            "pytest",
            "radon",
            "eslint",
            "sonarqube",
            "dependency_scanner",
            "performance_analyzer",
            "semgrep",
        }

        # Tools that don't work well on Windows
        windows_incompatible = {"codeql"}

        # Tools that are available but should be used carefully (may be slow)
        windows_careful = {"windows_security"}

        available_tools = []
        for tool in all_tools:
            if tool in windows_compatible:
                available_tools.append(tool)
            elif tool in windows_incompatible:
                logger.warning(
                    f"Tool '{tool}' is not available on Windows, skipping",
                    tool=tool,
                    platform=self.platform,
                )
            elif tool in windows_careful:
                # Include but warn about potential performance issues
                logger.info(
                    f"Tool '{tool}' is available on Windows but may be slow - use with caution",
                    tool=tool,
                    platform=self.platform,
                )
                available_tools.append(tool)
            else:
                # Unknown tool, include it but warn
                logger.info(
                    f"Tool '{tool}' compatibility with Windows unknown, including",
                    tool=tool,
                    platform=self.platform,
                )
                available_tools.append(tool)

        return available_tools

    def get_tool_substitutions(self) -> dict[str, str]:
        """Get tool substitutions for Windows-incompatible tools."""
        if not self.is_windows:
            return {}

        return {
            "codeql": "semgrep",  # Use Semgrep as the primary security alternative
        }

    def should_show_windows_warning(self) -> bool:
        """Determine if we should show Windows-specific warnings."""
        return self.is_windows

    def get_windows_recommendations(self) -> list[str]:
        """Get recommendations for Windows users."""
        if not self.is_windows:
            return []

        return [
            "Use Semgrep for comprehensive cross-platform security analysis",
            "Consider using WSL2 for better tool compatibility",
            "Install Windows-native versions of tools when available",
            "Use Bandit for Python-specific security scanning",
            "Enable Windows Security Tool for additional security checks",
        ]

    def get_cross_platform_tools(self) -> list[str]:
        """Get list of tools that work well across all platforms."""
        return [
            "semgrep",  # Excellent cross-platform static analysis
            "ruff",  # Fast Python linter
            "bandit",  # Python security scanner
            "safety",  # Dependency vulnerability scanner
            "mypy",  # Python type checker
            "pytest",  # Python testing framework
        ]


def create_platform_aware_tool_registry(tool_registry: any) -> any:
    """Create a platform-aware tool registry that adapts tools for the current platform."""
    detector = PlatformDetector()

    if detector.should_show_windows_warning():
        logger.warning(
            "Running on Windows - some tools may have limitations",
            platform_info=detector.detect_platform(),
            limitations=detector.get_windows_limitations(),
            recommendations=detector.get_windows_recommendations(),
        )

    return detector
