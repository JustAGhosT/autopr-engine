import asyncio
import os
from typing import Any

from .tool_base import Tool


class SonarQubeTool(Tool):
    """
    A tool for running the SonarQube scanner to perform static code analysis.
    """

    @property
    def name(self) -> str:
        return "sonarqube"

    @property
    def description(self) -> str:
        return "A platform for continuous inspection of code quality."

    def is_available(self) -> bool:
        """Check if SonarQube scanner is available."""
        return self.check_command_availability("sonar-scanner")

    def get_required_command(self) -> str | None:
        """Get the required command for this tool."""
        return "sonar-scanner"

    async def run(
        self, files: list[str], config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Run the SonarQube scanner.
        This tool requires server configuration provided in the `config` dictionary.
        The results are not returned directly but are available on the SonarQube server.
        """
        # Check for configuration from environment variables first
        server_url = config.get("server_url") or os.getenv("SONAR_HOST_URL")
        login_token = config.get("login_token") or os.getenv("SONAR_TOKEN")
        project_key = config.get("project_key") or os.getenv("SONAR_PROJECT_KEY")

        if not all([server_url, login_token, project_key]):
            return [
                {
                    "error": (
                        "SonarQube is not configured. Please provide:\n"
                        "1. server_url, login_token, and project_key in config, OR\n"
                        "2. Environment variables: SONAR_HOST_URL, SONAR_TOKEN, SONAR_PROJECT_KEY\n"
                        "Example: export SONAR_HOST_URL=https://sonarqube.company.com"
                    ),
                    "level": "warning",
                    "code": "SONARQUBE_CONFIG_MISSING",
                    "filename": "N/A",
                }
            ]

        command = [
            "sonar-scanner",
            f"-Dsonar.host.url={server_url}",
            f"-Dsonar.login={login_token}",
            f"-Dsonar.projectKey={project_key}",
            "-Dsonar.sources=.",
        ]

        extra_args = config.get("args", [])
        command.extend(extra_args)

        try:
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_message = stderr.decode().strip()
                if not error_message and stdout:
                    error_message = stdout.decode().strip()
                return [{"error": f"SonarQube scan failed: {error_message}"}]

            summary_message = f"SonarQube scan completed. View the report on the server: {server_url}/dashboard?id={project_key}"

            # This tool does not produce file-specific issues, but a server-side report.
            # We return a general informational message.
            return [
                {
                    "filename": "N/A",
                    "code": "SONARQUBE_SCAN_COMPLETE",
                    "message": summary_message,
                    "level": "info",
                }
            ]

        except Exception as e:
            return [{"error": f"SonarQube execution error: {e!s}"}]
