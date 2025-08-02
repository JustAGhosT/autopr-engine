"""
File handler implementations for different file types.
"""

from abc import ABC, abstractmethod
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from autopr.actions.platform_detection.analysis.base import FileAnalysisResult
from autopr.actions.platform_detection.analysis.patterns import ContentPattern, FilePattern

if TYPE_CHECKING:
    from autopr.actions.platform_detection.analysis.base import FileAnalyzer

logger = logging.getLogger(__name__)


class FileHandler(ABC):
    """Base class for file handlers that process specific file types."""

    def __init__(self):
        self.supported_extensions: set[str] = set()
        self.patterns: list[ContentPattern] = []
        self.file_patterns: list[FilePattern] = []
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the handler with patterns and configurations."""
        if self._initialized:
            return

        self._setup_patterns()
        self._initialized = True

    @abstractmethod
    def _setup_patterns(self) -> None:
        """Set up the patterns and configurations for this handler."""

    def analyze(self, file_path: Path, analyzer: "FileAnalyzer") -> FileAnalysisResult:
        """
        Analyze a file and return the analysis results.

        Args:
            file_path: Path to the file to analyze
            analyzer: The parent FileAnalyzer instance

        Returns:
            FileAnalysisResult containing the analysis results
        """
        self.initialize()
        result = FileAnalysisResult(file_path)

        try:
            # First check file patterns (name, path, etc.)
            for pattern in self.file_patterns:
                if pattern.matches(file_path):
                    result.add_match(pattern.platform_id, pattern.confidence)

            # Then check content patterns
            content = self._read_file(file_path)
            if content is not None:
                for pattern in self.patterns:
                    if pattern.matches(content):
                        result.add_match(pattern.platform_id, pattern.confidence)

            # Run any custom analysis
            custom_result = self._analyze_content(file_path, content, analyzer)
            if custom_result is not None:
                result.merge(custom_result)

        except Exception as e:
            logger.exception(f"Error in {self.__class__.__name__} analyzing {file_path}")
            result.metadata["error"] = str(e)

        return result

    def _read_file(self, file_path: Path) -> str | None:
        """Read the file content with proper encoding handling."""
        try:
            return file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return None

    def _analyze_content(
        self,
        file_path: Path,
        content: str | None,
        analyzer: "FileAnalyzer",
    ) -> FileAnalysisResult | None:
        """
        Perform custom analysis on the file content.

        Subclasses can override this to implement custom analysis logic.

        Args:
            file_path: Path to the file being analyzed
            content: The file content as text (or None if reading failed)
            analyzer: The parent FileAnalyzer instance

        Returns:
            Optional FileAnalysisResult with additional analysis results
        """
        return None


class JsonFileHandler(FileHandler):
    """Handler for JSON files."""

    def _setup_patterns(self) -> None:
        self.supported_extensions.update({".json"})

        # Example patterns - should be moved to configuration
        self.patterns.extend(
            [
                ContentPattern("replit", r'"replit"\s*:', confidence=0.7),
                ContentPattern("vercel", r'"vercel"\s*:', confidence=0.7),
            ]
        )

    def _analyze_content(
        self,
        file_path: Path,
        content: str | None,
        analyzer: "FileAnalyzer",
    ) -> FileAnalysisResult | None:
        if content is None:
            return None

        try:
            data = json.loads(content)
            return self._analyze_json(file_path, data, analyzer)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {file_path}: {e}")
            return None

    def _analyze_json(
        self,
        file_path: Path,
        data: Any,
        analyzer: "FileAnalyzer",
    ) -> FileAnalysisResult | None:
        """Analyze JSON data."""
        result = FileAnalysisResult(file_path)

        # Example: Check for common platform indicators in package.json
        if file_path.name == "package.json" and isinstance(data, dict):
            # Check dependencies
            for dep_field in ["dependencies", "devDependencies", "peerDependencies"]:
                if dep_field in data and isinstance(data[dep_field], dict):
                    deps = data[dep_field]
                    if "next" in deps:
                        result.add_match("vercel", 0.9)
                    if "express" in deps:
                        result.add_match("nodejs", 0.8)
                    if "react" in deps:
                        result.add_match("react", 0.9)

        return result if result.platform_matches else None


class YamlFileHandler(FileHandler):
    """Handler for YAML files."""

    def _setup_patterns(self) -> None:
        self.supported_extensions.update({".yaml", ".yml"})
        self.patterns.extend(
            [
                ContentPattern("kubernetes", r"apiVersion\s*:", confidence=0.9),
                ContentPattern("docker-compose", r"version\s*:", confidence=0.7),
            ]
        )

    def _analyze_content(
        self,
        file_path: Path,
        content: str | None,
        analyzer: "FileAnalyzer",
    ) -> FileAnalysisResult | None:
        if content is None:
            return None

        try:
            data = yaml.safe_load(content)
            return self._analyze_yaml(file_path, data, analyzer)
        except yaml.YAMLError as e:
            logger.warning(f"Invalid YAML in {file_path}: {e}")
            return None

    def _analyze_yaml(
        self,
        file_path: Path,
        data: Any,
        analyzer: "FileAnalyzer",
    ) -> FileAnalysisResult | None:
        """Analyze YAML data."""
        result = FileAnalysisResult(file_path)

        if isinstance(data, dict):
            # Check for Kubernetes resources
            if "apiVersion" in data and "kind" in data:
                result.add_match("kubernetes", 0.9)

            # Check for GitHub Actions workflows
            if "on" in data and "jobs" in data:
                result.add_match("github-actions", 0.9)

        return result if result.platform_matches else None


class PythonFileHandler(FileHandler):
    """Handler for Python files."""

    def _setup_patterns(self) -> None:
        self.supported_extensions.update({".py"})
        self.patterns.extend(
            [
                ContentPattern("django", r"from\s+django\.", confidence=0.9),
                ContentPattern("flask", r"from\s+flask\s+import", confidence=0.9),
                ContentPattern("fastapi", r"from\s+fastapi\s+import", confidence=0.9),
            ]
        )

    def _analyze_content(
        self,
        file_path: Path,
        content: str | None,
        analyzer: "FileAnalyzer",
    ) -> FileAnalysisResult | None:
        if content is None:
            return None

        result = FileAnalysisResult(file_path)

        # Check for common Python web frameworks
        if "import flask" in content or "from flask import" in content:
            result.add_match("flask", 0.9)

        if "import django" in content or "from django." in content:
            result.add_match("django", 0.9)

        if "import fastapi" in content or "from fastapi import" in content:
            result.add_match("fastapi", 0.9)

        return result if result.platform_matches else None


class RequirementsFileHandler(FileHandler):
    """Handler for Python requirements files."""

    def _setup_patterns(self) -> None:
        self.file_patterns.extend(
            [
                FilePattern("python", "requirements*.txt", confidence=0.8),
            ]
        )

    def _analyze_content(
        self,
        file_path: Path,
        content: str | None,
        analyzer: "FileAnalyzer",
    ) -> FileAnalysisResult | None:
        if content is None:
            return None

        result = FileAnalysisResult(file_path)

        # Check for common Python packages
        lines = content.lower().split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Basic package name extraction (handles most common cases)
            pkg_name = (
                line.split(">", 1)[0].split("<", 1)[0].split("=", 1)[0].split("[", 1)[0].strip()
            )

            # Map packages to platforms
            package_platforms = {
                "django": "django",
                "flask": "flask",
                "fastapi": "fastapi",
                "tensorflow": "tensorflow",
                "torch": "pytorch",
                "pytorch": "pytorch",
                "numpy": "scientific-python",
                "pandas": "scientific-python",
                "scikit-learn": "scientific-python",
                "requests": "python",
                "aiohttp": "python",
            }

            if pkg_name in package_platforms:
                result.add_match(package_platforms[pkg_name], 0.8)

        return result if result.platform_matches else None


class PackageJsonHandler(FileHandler):
    """Handler for package.json files."""

    def _setup_patterns(self) -> None:
        self.file_patterns.append(FilePattern("nodejs", "package.json", confidence=0.9))

    def _analyze_content(
        self,
        file_path: Path,
        content: str | None,
        analyzer: "FileAnalyzer",
    ) -> FileAnalysisResult | None:
        if content is None:
            return None

        try:
            data = json.loads(content)
            return self._analyze_package_json(file_path, data, analyzer)
        except json.JSONDecodeError:
            logger.warning(f"Invalid package.json: {file_path}")
            return None

    def _analyze_package_json(
        self,
        file_path: Path,
        data: dict[str, Any],
        analyzer: "FileAnalyzer",
    ) -> FileAnalysisResult | None:
        """Analyze package.json content."""
        result = FileAnalysisResult(file_path)

        if not isinstance(data, dict):
            return None

        # Always detect Node.js for package.json
        result.add_match("nodejs", 0.9)

        # Check for frameworks
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

        framework_detectors = {
            "next": "nextjs",
            "react": "react",
            "vue": "vue",
            "@angular/core": "angular",
            "express": "express",
            "koa": "koa",
            "svelte": "svelte",
            "nuxt": "nuxt",
            "gatsby": "gatsby",
            "remix": "remix",
        }

        for pkg, platform in framework_detectors.items():
            if any(dep.startswith(pkg) for dep in deps):
                result.add_match(platform, 0.9)

        # Check for deployment platforms
        if "vercel" in deps or "now" in deps:
            result.add_match("vercel", 0.9)

        if "netlify" in deps:
            result.add_match("netlify", 0.9)

        if "firebase" in deps or "firebase-admin" in deps:
            result.add_match("firebase", 0.9)

        return result


class DockerfileHandler(FileHandler):
    """Handler for Dockerfiles."""

    def _setup_patterns(self) -> None:
        self.file_patterns.extend(
            [
                FilePattern("docker", "Dockerfile*", confidence=0.9),
                FilePattern("docker", "*.dockerfile", confidence=0.9),
            ]
        )

    def _analyze_content(
        self,
        file_path: Path,
        content: str | None,
        analyzer: "FileAnalyzer",
    ) -> FileAnalysisResult | None:
        if content is None:
            return None

        result = FileAnalysisResult(file_path)
        result.add_match("docker", 0.9)

        # Check for common base images
        lines = content.lower().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("from "):
                image = line[5:].split(":", 1)[0].split(" ", 1)[0].strip()

                # Map common base images to platforms
                image_platforms = {
                    "node": "nodejs",
                    "python": "python",
                    "ruby": "ruby",
                    "php": "php",
                    "golang": "go",
                    "openjdk": "java",
                    "microsoft/dotnet": "dotnet",
                    "nginx": "nginx",
                    "httpd": "apache",
                    "mysql": "mysql",
                    "postgres": "postgresql",
                    "mongo": "mongodb",
                    "redis": "redis",
                    "amazon/aws-": "aws",
                    "gcr.io/google": "gcp",
                    "mcr.microsoft.com/azure": "azure",
                }

                for img_prefix, platform in image_platforms.items():
                    if img_prefix in image:
                        result.add_match(platform, 0.8)
                        break

                break  # Only check the first FROM line

        return result


class DefaultFileHandler(FileHandler):
    """Default handler for files without a specific handler."""

    def _setup_patterns(self) -> None:
        # No patterns by default
        pass

    def _analyze_content(
        self,
        file_path: Path,
        content: str | None,
        analyzer: "FileAnalyzer",
    ) -> FileAnalysisResult | None:
        # Simple content matching for common files
        result = FileAnalysisResult(file_path)

        # Check for common web server files
        if file_path.name == ".htaccess":
            result.add_match("apache", 0.9)
        elif file_path.name == "nginx.conf" or (
            file_path.suffix == ".conf" and "nginx" in file_path.parts
        ):
            result.add_match("nginx", 0.9)

        return result if result.platform_matches else None
