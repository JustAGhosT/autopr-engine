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

    async def run(self, files: list[str], config: dict[str, Any]) -> dict[str, Any]:
        """
        Run performance analysis checks.
        For Python, we'll use scalene if available.
        """
        python_files = [f for f in files if f.endswith(".py")]
        js_ts_files = [f for f in files if f.endswith((".js", ".ts", ".jsx", ".tsx"))]

        issues = []
        files_with_issues = []
        summary_lines = ["Performance Analysis Results:"]

        # Python performance analysis with scalene if available
        if python_files:
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
                    summary_lines.append("Found Scalene for Python performance profiling.")

                    for py_file in python_files[:5]:  # Limit to 5 files for quicker profiling
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
                                            files_with_issues.append(py_file)
                                            issue = {
                                                "file": py_file,
                                                "line": line,
                                                "message": f"Performance hotspot: {cpu_pct:.1f}% CPU, {mem:.1f}MB memory",
                                                "severity": "info",
                                                "cpu_percent": cpu_pct,
                                                "memory_mb": mem,
                                            }
                                            issues.append(issue)

                                # Clean up the temp file
                                os.remove(out_file)
                            except Exception as e:
                                print(f"Error processing Scalene output: {e}")
                else:
                    summary_lines.append(
                        "Scalene not installed. For Python performance profiling, install with: pip install scalene"
                    )
            except Exception as e:
                summary_lines.append(f"Error running Python performance analysis: {e}")

        # Static performance analysis (check for common patterns)
        for file in files:
            try:
                with open(file) as f:
                    content = f.read()

                    # Check for python performance issues
                    if file.endswith(".py"):
                        # Check for list comprehension vs. loops
                        if "for " in content and " in range" in content and ".append" in content:
                            issues.append(
                                {
                                    "file": file,
                                    "line": 0,  # Would need more sophisticated parsing for exact line
                                    "message": "Consider using list comprehension instead of loops with append for better performance",
                                    "severity": "info",
                                    "category": "performance_pattern",
                                }
                            )
                            files_with_issues.append(file)

                        # Check for inefficient string concatenation
                        if "+= " in content and '"' in content:
                            issues.append(
                                {
                                    "file": file,
                                    "line": 0,
                                    "message": "String concatenation in loops can be inefficient. Consider using ''.join() or string formatting",
                                    "severity": "info",
                                    "category": "performance_pattern",
                                }
                            )
                            files_with_issues.append(file)

                    # Check for JavaScript/TypeScript performance issues
                    elif file.endswith((".js", ".ts", ".jsx", ".tsx")):
                        # Check for console.log in production code
                        if "console.log" in content:
                            issues.append(
                                {
                                    "file": file,
                                    "line": 0,
                                    "message": "console.log statements can impact performance in production. Consider removing or using a logger with levels",
                                    "severity": "info",
                                    "category": "performance_pattern",
                                }
                            )
                            files_with_issues.append(file)
            except Exception as e:
                print(f"Error analyzing {file} for performance: {e}")

        # Create summary
        if issues:
            summary_lines.append(
                f"Found {len(issues)} performance considerations in {len(set(files_with_issues))} files."
            )
        else:
            summary_lines.append("No significant performance issues detected.")

        return {
            "issues": issues,
            "files_with_issues": list(set(files_with_issues)),
            "summary": "\n".join(summary_lines),
        }
