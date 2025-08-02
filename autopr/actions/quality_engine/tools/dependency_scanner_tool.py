import asyncio
import json
from typing import Any

from .tool_base import Tool


class DependencyScannerTool(Tool):
    """
    A tool for scanning dependencies for vulnerabilities using safety.
    """

    @property
    def name(self) -> str:
        return "dependency_scanner"

    @property
    def description(self) -> str:
        return "Scans Python dependencies for known vulnerabilities using safety."

    async def run(self, files: list[str], config: dict[str, Any]) -> dict[str, Any]:
        """
        Run safety check on project dependencies.
        """
        # Find requirements files in the project
        req_files = [f for f in files if f.endswith("requirements.txt")]
        if not req_files and "requirements.txt" not in files:
            # Try to find any requirements file in the project directory
            try:
                process = await asyncio.create_subprocess_exec(
                    "find",
                    ".",
                    "-name",
                    "requirements*.txt",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                req_files = stdout.decode().strip().split("\n")
                req_files = [f for f in req_files if f]  # Filter out empty lines
            except Exception as e:
                print(f"Error finding requirements files: {e}")
                req_files = []

        issues = []
        files_with_issues = []
        summary_lines = []

        # If we found requirements files, scan each of them
        if req_files:
            for req_file in req_files:
                cmd = ["safety", "check", "-r", req_file, "--json"]

                try:
                    process = await asyncio.create_subprocess_exec(
                        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()

                    if stderr:
                        error = stderr.decode().strip()
                        if "safety: command not found" in error:
                            summary_lines.append("Safety is not installed. Run: pip install safety")
                            continue
                        else:
                            print(f"Error running safety: {error}")

                    # Parse safety output
                    if stdout:
                        try:
                            results = json.loads(stdout)
                            if results and isinstance(results, list) and len(results) > 0:
                                files_with_issues.append(req_file)

                                for vuln in results:
                                    issue = {
                                        "file": req_file,
                                        "line": 0,  # Safety doesn't provide line numbers
                                        "message": f"Vulnerability in {vuln[0]}: {vuln[3]}",
                                        "severity": "high",
                                        "package": vuln[0],
                                        "installed_version": vuln[1],
                                        "vulnerable_below": vuln[2],
                                        "vulnerability_id": vuln[4],
                                    }
                                    issues.append(issue)
                        except json.JSONDecodeError:
                            print(f"Failed to parse safety output: {stdout.decode()}")

                except Exception as e:
                    print(f"Exception running safety: {e}")
        else:
            summary_lines.append("No requirements files found to scan.")

        # Summary creation
        if issues:
            summary_lines.append(
                f"Found {len(issues)} vulnerabilities in {len(files_with_issues)} files."
            )
        else:
            summary_lines.append("No vulnerabilities found in dependencies.")

        # Return the issues list directly, not wrapped in a dict
        return issues
