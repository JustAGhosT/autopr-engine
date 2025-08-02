import asyncio
import json
import os
import shutil
import tempfile
from typing import Any

from .tool_base import Tool


class CodeQLTool(Tool):
    """
    A tool for running CodeQL, a static analysis engine for vulnerability scanning.
    """

    @property
    def name(self) -> str:
        return "codeql"

    @property
    def description(self) -> str:
        return "A static analysis engine for vulnerability scanning."

    async def run(self, files: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Run CodeQL on the project. This involves:
        1. Creating a CodeQL database from the source code.
        2. Analyzing the database with a query suite.
        3. Parsing the SARIF output.
        """
        # Check if CodeQL is available
        if not shutil.which("codeql"):
            print("CodeQL is not available on this system. Skipping CodeQL analysis.")
            return [{"warning": "CodeQL is not available on this system"}]

        project_root = "."  # Assuming we run from the project root.
        language = config.get("language", "python")
        query_suite = config.get("query_suite", "python-security-and-quality.qls")

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "codeql_db")
            results_path = os.path.join(temp_dir, "results.sarif")

            # 1. Create the database
            db_create_cmd = [
                "codeql",
                "database",
                "create",
                db_path,
                f"--language={language}",
                f"--source-root={project_root}",
                "--overwrite",
            ]

            process_db = await asyncio.create_subprocess_exec(
                *db_create_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _, stderr_db = await process_db.communicate()

            if process_db.returncode != 0:
                error_message = stderr_db.decode().strip()
                print(f"Error creating CodeQL database: {error_message}")
                return [{"error": f"CodeQL database creation failed: {error_message}"}]

            # 2. Analyze the database
            analyze_cmd = [
                "codeql",
                "database",
                "analyze",
                db_path,
                query_suite,
                "--format=sarif-latest",
                f"--output={results_path}",
            ]

            process_analyze = await asyncio.create_subprocess_exec(
                *analyze_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _, stderr_analyze = await process_analyze.communicate()

            if process_analyze.returncode != 0:
                error_message = stderr_analyze.decode().strip()
                print(f"Error analyzing CodeQL database: {error_message}")
                return [{"error": f"CodeQL analysis failed: {error_message}"}]

            # 3. Parse the SARIF output
            if not os.path.exists(results_path):
                return []

            try:
                with open(results_path) as f:
                    sarif_data = json.load(f)
                return self._parse_sarif(sarif_data)
            except (json.JSONDecodeError, FileNotFoundError):
                print("Failed to parse CodeQL SARIF output.")
                return [{"error": "Failed to parse CodeQL SARIF output"}]

        return []

    def _parse_sarif(self, sarif_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Parses a SARIF log to extract a simplified list of issues.
        """
        issues = []
        if not sarif_data.get("runs"):
            return []

        for run in sarif_data["runs"]:
            if not run.get("results"):
                continue

            for result in run["results"]:
                # Extract location information
                location = result.get("locations", [{}])[0]
                physical_location = location.get("physicalLocation", {})
                artifact_location = physical_location.get("artifactLocation", {})
                region = physical_location.get("region", {})

                filename = artifact_location.get("uri", "unknown")
                line_number = region.get("startLine")
                column_number = region.get("startColumn")

                # Extract message
                message = result.get("message", {})
                if isinstance(message, dict):
                    text = message.get("text", "No message provided")
                else:
                    text = str(message)

                # Extract rule information
                rule = result.get("rule", {})
                rule_id = rule.get("id", "unknown") if isinstance(rule, dict) else "unknown"

                issues.append(
                    {
                        "filename": filename,
                        "line_number": line_number,
                        "column_number": column_number,
                        "code": rule_id,
                        "message": text,
                        "severity": result.get("level", "warning"),
                        "details": {
                            "rule_id": rule_id,
                            "rule_name": (
                                rule.get("name", "Unknown") if isinstance(rule, dict) else "Unknown"
                            ),
                            "help_uri": rule.get("helpUri", "") if isinstance(rule, dict) else "",
                        },
                    }
                )

        return issues
