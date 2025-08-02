import asyncio
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

    async def run(self, files: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Run the SonarQube scanner.
        This tool requires server configuration provided in the `config` dictionary.
        The results are not returned directly but are available on the SonarQube server.
        """
        server_url = config.get("server_url")
        login_token = config.get("login_token")
        project_key = config.get("project_key")

        if not all([server_url, login_token, project_key]):
            return [
                {
                    "error": "SonarQube is not configured. Please provide server_url, login_token, and project_key.",
                    "level": "warning",
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

        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_message = stderr.decode().strip()
            if not error_message and stdout:
                error_message = stdout.decode().strip()
            print(f"Error running SonarQube scanner: {error_message}")
            return [{"error": f"SonarQube scan failed: {error_message}"}]

        summary_message = f"SonarQube scan completed. View the report on the server: {server_url}/dashboard?id={project_key}"
        print(summary_message)

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
