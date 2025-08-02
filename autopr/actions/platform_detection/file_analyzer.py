"""
Legacy File Analyzer Module

This module provides backward compatibility for the old FileAnalyzer interface.
New code should use the modular analyzer in autopr.actions.platform_detection.analysis
"""

import json
from pathlib import Path
import re
from typing import Any
import warnings

from autopr.actions.platform_detection.analysis import create_file_analyzer
from autopr.actions.platform_detection.analysis.patterns import ContentPattern, FilePattern


class FileAnalyzer:
    """
    Legacy wrapper for the modular FileAnalyzer.

    This class provides backward compatibility with the old interface while
    delegating to the new modular implementation under the hood.

    .. deprecated:: 1.0.0
       Use :class:`autopr.actions.platform_detection.analysis.FileAnalyzer` instead.
    """

    def __init__(self, workspace_path: str = "."):
        """Initialize the legacy file analyzer.

        Args:
            workspace_path: Path to the workspace to analyze (default: ".")
        """
        warnings.warn(
            "FileAnalyzer is deprecated. "
            "Use autopr.actions.platform_detection.analysis.create_file_analyzer() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.workspace_path = Path(workspace_path)
        self._analyzer = create_file_analyzer(workspace_path)

    def scan_for_platform_files(
        self, platform_configs: dict[str, dict[str, Any]]
    ) -> dict[str, list[str]]:
        """Scan workspace for platform-specific files."""
        results = {}

        # Convert platform configs to the new format
        for platform, config in platform_configs.items():
            file_matches = []
            for file_pattern in config.get("files", []):
                # Convert glob patterns to the new format
                pattern = FilePattern(platform, file_pattern, confidence=0.7)
                file_matches.extend(
                    str(match.path.relative_to(self.workspace_path))
                    for match in self._analyzer.analyze_directory()
                    if pattern.matches(match.path)
                )

            if file_matches:
                results[platform] = list(set(file_matches))  # Remove duplicates

        return results

    def scan_for_folder_patterns(
        self, platform_configs: dict[str, dict[str, Any]]
    ) -> dict[str, list[str]]:
        """Scan workspace for platform-specific folder patterns."""
        results = {}

        for platform, config in platform_configs.items():
            folder_matches = []
            for folder_pattern in config.get("folder_patterns", []):
                # Look for directories matching the pattern
                folder_matches.extend(
                    str(dir_path.relative_to(self.workspace_path))
                    for dir_path in self.workspace_path.glob(f"**/{folder_pattern}")
                    if dir_path.is_dir()
                )

            if folder_matches:
                results[platform] = list(set(folder_matches))  # Remove duplicates

        return results

    def _find_files_by_pattern(self, pattern: str) -> list[str]:
        """Find files matching the given glob pattern."""
        return [
            str(file_path.relative_to(self.workspace_path))
            for file_path in self.workspace_path.glob("**/" + pattern)
            if file_path.is_file()
        ]

    def _find_folders_by_pattern(self, pattern: str) -> list[str]:
        """Find folders matching the given glob pattern."""
        return [
            str(dir_path.relative_to(self.workspace_path))
            for dir_path in self.workspace_path.glob("**/" + pattern)
            if dir_path.is_dir()
        ]

    def analyze_file_content(
        self, file_path: str, platform_configs: dict[str, dict[str, Any]]
    ) -> dict[str, float]:
        """Analyze file content for platform indicators."""
        file_path_obj = Path(file_path)
        if not file_path_obj.exists() or not file_path_obj.is_file():
            return {}

        try:
            content = file_path_obj.read_text(encoding="utf-8", errors="ignore")
            return self._analyze_content(content, platform_configs)
        except (OSError, UnicodeDecodeError):
            return {}

    def _analyze_content(
        self, content: str, platform_configs: dict[str, dict[str, Any]]
    ) -> dict[str, float]:
        """Analyze content for platform indicators."""
        results = {}
        for platform, config in platform_configs.items():
            confidence = 0.0
            for pattern in config.get("content_patterns", []):
                # Convert to ContentPattern for consistency
                content_pattern = ContentPattern(platform, pattern, confidence=0.3)
                if content_pattern.matches(content):
                    confidence += content_pattern.confidence

            if confidence > 0:
                results[platform] = min(confidence, 1.0)  # Cap at 1.0

        return results

    def scan_for_platform_indicators(
        self, platform_configs: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """
        Scan the workspace for platform indicators.

        Returns:
            Dict mapping platform names to their detection results
        """
        # Convert platform configs to the new format
        results = {}

        # Get file and folder matches using the new analyzer
        file_matches = self.scan_for_platform_files(platform_configs)
        folder_matches = self.scan_for_folder_patterns(platform_configs)

        # Combine results in the legacy format
        for platform in set(file_matches.keys()) | set(folder_matches.keys()):
            results[platform] = {
                "files": file_matches.get(platform, []),
                "folders": folder_matches.get(platform, []),
                "confidence": 0.0,
            }

            # Calculate confidence based on number of matches
            file_count = len(results[platform]["files"])
            folder_count = len(results[platform]["folders"])

            # More matches = higher confidence, but cap at 0.7
            confidence = min(0.7, 0.1 * (file_count + folder_count))

            # Analyze file contents for additional confidence
            for file_path in results[platform]["files"]:
                content_results = self.analyze_file_content(
                    str(self.workspace_path / file_path), {platform: platform_configs[platform]}
                )
                if platform in content_results:
                    confidence = min(1.0, confidence + content_results[platform])

            results[platform]["confidence"] = confidence

        return results

    def analyze_package_json(self) -> dict[str, Any]:
        """Analyze package.json for platform indicators."""
        package_json_path = self.workspace_path / "package.json"

        if not package_json_path.exists():
            return {}

        try:
            with open(package_json_path, encoding="utf-8") as f:
                package_data = json.load(f)

            return {
                "dependencies": package_data.get("dependencies", {}),
                "devDependencies": package_data.get("devDependencies", {}),
                "scripts": package_data.get("scripts", {}),
                "name": package_data.get("name", ""),
                "description": package_data.get("description", ""),
            }
        except (OSError, json.JSONDecodeError):
            return {}

    def analyze_requirements_txt(self) -> list[str]:
        """Analyze requirements.txt for Python dependencies."""
        requirements_path = self.workspace_path / "requirements.txt"

        if not requirements_path.exists():
            return []

        try:
            with open(requirements_path, encoding="utf-8") as f:
                lines = f.readlines()

            dependencies = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract package name (before version specifiers)
                    package_name = re.split(r"[>=<!=]", line)[0].strip()
                    dependencies.append(package_name)

            return dependencies
        except OSError:
            return []

    def analyze_dockerfile(self) -> dict[str, Any]:
        """Analyze Dockerfile for platform indicators."""
        dockerfile_path = self.workspace_path / "Dockerfile"

        if not dockerfile_path.exists():
            return {}

        try:
            with open(dockerfile_path, encoding="utf-8") as f:
                content = f.read()

            return {
                "base_images": self._extract_base_images(content),
                "exposed_ports": self._extract_exposed_ports(content),
                "environment_vars": self._extract_env_vars(content),
                "commands": self._extract_run_commands(content),
            }

        except OSError:
            return {}

    def scan_content_for_patterns(
        self, platform_configs: dict[str, dict[str, Any]]
    ) -> dict[str, int]:
        """Scan file contents for platform-specific patterns."""
        pattern_matches = {}

        for platform, config in platform_configs.items():
            match_count = 0

            for pattern in config.get("content_patterns", []):
                matches = self._search_content_pattern(pattern)
                match_count += matches

            if match_count > 0:
                pattern_matches[platform] = match_count

        return pattern_matches

    def _find_files_by_pattern(self, pattern: str) -> list[str]:
        """Find files matching a specific pattern."""
        matches = []

        try:
            if "*" in pattern or "?" in pattern:
                # Use glob for wildcard patterns
                matches.extend([str(p) for p in self.workspace_path.glob(pattern)])
            else:
                # Direct file check
                file_path = self.workspace_path / pattern
                if file_path.exists():
                    matches.append(str(file_path))
        except Exception:
            pass

        return matches

    def _find_folders_by_pattern(self, pattern: str) -> list[str]:
        """Find folders matching a specific pattern."""
        matches = []

        try:
            if "*" in pattern or "?" in pattern:
                # Use glob for wildcard patterns
                matches.extend([str(p) for p in self.workspace_path.glob(pattern) if p.is_dir()])
            else:
                # Direct folder check
                folder_path = self.workspace_path / pattern
                if folder_path.exists() and folder_path.is_dir():
                    matches.append(str(folder_path))
        except Exception:
            pass

        return matches

    def _search_content_pattern(self, pattern: str) -> int:
        """Search for pattern in file contents."""
        match_count = 0

        try:
            for file_path in self.workspace_path.rglob("*"):
                if file_path.is_file() and self._is_text_file(file_path):
                    try:
                        with open(file_path, encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            match_count += len(re.findall(pattern, content, re.IGNORECASE))
                    except Exception:
                        continue
        except Exception:
            pass

        return match_count

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is likely a text file."""
        text_extensions = {
            ".txt",
            ".md",
            ".json",
            ".yml",
            ".yaml",
            ".toml",
            ".ini",
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".html",
            ".css",
            ".scss",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".sh",
            ".bat",
            ".ps1",
            ".dockerfile",
            ".gitignore",
        }

        return file_path.suffix.lower() in text_extensions or file_path.name.lower() in {
            "dockerfile",
            "makefile",
            "readme",
        }

    def _extract_base_images(self, dockerfile_content: str) -> list[str]:
        """Extract base images from Dockerfile."""
        pattern = r"^FROM\s+([^\s]+)"
        return re.findall(pattern, dockerfile_content, re.MULTILINE | re.IGNORECASE)

    def _extract_exposed_ports(self, dockerfile_content: str) -> list[str]:
        """Extract exposed ports from Dockerfile."""
        pattern = r"^EXPOSE\s+(.+)"
        matches = re.findall(pattern, dockerfile_content, re.MULTILINE | re.IGNORECASE)
        ports = []
        for match in matches:
            ports.extend(match.split())
        return ports

    def _extract_env_vars(self, dockerfile_content: str) -> list[str]:
        """Extract environment variables from Dockerfile."""
        pattern = r"^ENV\s+([^=\s]+)"
        return re.findall(pattern, dockerfile_content, re.MULTILINE | re.IGNORECASE)

    def _extract_run_commands(self, dockerfile_content: str) -> list[str]:
        """Extract RUN commands from Dockerfile."""
        pattern = r"^RUN\s+(.+)"
        return re.findall(pattern, dockerfile_content, re.MULTILINE | re.IGNORECASE)
