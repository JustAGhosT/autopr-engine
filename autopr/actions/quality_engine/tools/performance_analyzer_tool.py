import asyncio
import json
import os
from typing import Any

from .tool_base import Tool


class PerformanceAnalyzerTool(Tool):
    """
    A tool for analyzing code performance issues.
    """

    @property
    def name(self) -> str:
        return "performance_analyzer"

    @property
    def description(self) -> str:
        return "Analyzes code for potential performance issues."

    def is_available(self) -> bool:
        """Check if performance analysis tools are available."""
        # Check if python is available for basic analysis
        return self.check_command_availability("python")

    def get_required_command(self) -> str | None:
        """Get the required command for this tool."""
        return "python"

    async def run(self, files: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Run performance analysis checks.
        For Python, we'll use scalene if available.
        """
        python_files = [f for f in files if f.endswith(".py")]

        issues = []

        # Python performance analysis with scalene if available
        if python_files:
            scalene_issues = await self._run_scalene_analysis(python_files)
            issues.extend(scalene_issues)

        # Static performance analysis (check for common patterns)
        static_issues = await self._run_static_analysis(files)
        issues.extend(static_issues)

        return issues

    async def _run_scalene_analysis(self, python_files: list[str]) -> list[dict[str, Any]]:
        """Run Scalene performance analysis on Python files."""
        issues = []

        try:
            # Check if scalene is installed
            process = await asyncio.create_subprocess_exec(
                "python",
                "-m",
                "scalene",
                "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await process.communicate()
            scalene_installed = process.returncode == 0

            if scalene_installed:
                for py_file in python_files[:5]:  # Limit to 5 files for quicker profiling
                    scalene_issues = await self._analyze_file_with_scalene(py_file)
                    issues.extend(scalene_issues)
        except Exception:
            pass

        return issues

    async def _analyze_file_with_scalene(self, py_file: str) -> list[dict[str, Any]]:
        """Analyze a single Python file with Scalene."""
        issues = []

        try:
            # Run simple scalene profiling
            out_file = f"{os.path.splitext(py_file)[0]}_profile.json"

            cmd = ["python", "-m", "scalene", "--outfile", out_file, "--json", py_file]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _, _ = await process.communicate()

            # Try to read the profiling results if available
            if os.path.exists(out_file):
                try:
                    with open(out_file) as f:
                        profile_data = json.load(f)

                    # Find hotspots
                    if profile_data and isinstance(profile_data, dict):
                        functions = profile_data.get("functions", [])
                        sorted_funcs = sorted(
                            functions,
                            key=lambda x: x.get("cpu_percent", 0),
                            reverse=True,
                        )

                        for func in sorted_funcs[:3]:  # Top 3 CPU consumers
                            line = func.get("lineno", 0)
                            cpu_pct = func.get("cpu_percent", 0)
                            mem = func.get("memory_mb", 0)

                            if cpu_pct > 5 or mem > 10:  # Only report significant usage
                                issue = {
                                    "filename": py_file,
                                    "line_number": line,
                                    "message": f"Performance hotspot: {cpu_pct:.1f}% CPU, {mem:.1f}MB memory",
                                    "severity": "info",
                                    "code": "performance_hotspot",
                                }
                                issues.append(issue)

                    # Clean up the temp file
                    os.remove(out_file)
                except Exception:
                    pass
        except Exception:
            pass

        return issues

    async def _run_static_analysis(self, files: list[str]) -> list[dict[str, Any]]:
        """Run static performance analysis on files."""
        issues = []

        # Filter out directories and only process actual files
        actual_files = []
        for f in files:
            # Skip directories and problematic paths
            if f in [".", "..", "/", "\\"] or f.endswith((".", "/", "\\")):
                continue
            try:
                # Check if it's actually a file
                import os

                if os.path.isfile(f):
                    actual_files.append(f)
            except (OSError, PermissionError):
                # Skip files we can't access
                continue

        for file in actual_files:
            try:
                with open(file) as f:
                    content = f.read()

                # Check for python performance issues
                if file.endswith(".py"):
                    python_issues = self._analyze_python_performance(file, content)
                    issues.extend(python_issues)

                # Check for JavaScript/TypeScript performance issues
                elif file.endswith((".js", ".ts", ".jsx", ".tsx")):
                    js_issues = self._analyze_js_performance(file, content)
                    issues.extend(js_issues)
            except (OSError, PermissionError, UnicodeDecodeError):
                # Skip files we can't read
                continue

        return issues

    def _analyze_python_performance(self, file: str, content: str) -> list[dict[str, Any]]:
        """Analyze Python file for performance patterns."""
        issues = []

        # Check for list comprehension vs. loops
        if "for " in content and " in range" in content and ".append" in content:
            issues.append(
                {
                    "filename": file,
                    "line_number": 0,  # Would need more sophisticated parsing for exact line
                    "message": "Consider using list comprehension instead of loops with append for better performance",
                    "severity": "info",
                    "code": "performance_pattern",
                }
            )

        # Check for inefficient string concatenation
        if "+= " in content and '"' in content:
            issues.append(
                {
                    "filename": file,
                    "line_number": 0,
                    "message": "String concatenation in loops can be inefficient. Consider using ''.join() or string formatting",
                    "severity": "info",
                    "code": "performance_pattern",
                }
            )

        return issues

    def _analyze_js_performance(self, file: str, content: str) -> list[dict[str, Any]]:
        """Analyze JavaScript/TypeScript file for performance patterns."""
        issues = []

        # Check for console.log in production code
        if "console.log" in content:
            issues.append(
                {
                    "filename": file,
                    "line_number": 0,
                    "message": "console.log statements can impact performance in production. Consider removing or using a logger with levels",
                    "severity": "info",
                    "code": "performance_pattern",
                }
            )

        return issues
