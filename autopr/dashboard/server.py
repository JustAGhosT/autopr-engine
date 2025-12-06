"""AutoPR Dashboard Server

Flask-based web server for AutoPR monitoring and configuration.
"""

import asyncio
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import threading
import time
from typing import Any

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from autopr.actions.quality_engine.engine import QualityEngine, QualityInputs
from autopr.actions.quality_engine.models import QualityMode
from autopr.health.health_checker import HealthChecker
from autopr.quality.metrics_collector import MetricsCollector


class AutoPRDashboard:
    """AutoPR Dashboard server for monitoring and configuration."""

    def __init__(self, host: str = "localhost", port: int = 8080, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug

        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # TODO: SECURITY - Configure allowed directories in production from config
        # This prevents path traversal attacks
        self.allowed_directories = self._get_allowed_directories()

        # Initialize components
        self.metrics_collector = MetricsCollector()
        self.quality_engine = QualityEngine()
        self.health_checker = HealthChecker()

        # Dashboard data
        self.dashboard_data = {
            "start_time": datetime.now(),
            "total_checks": 0,
            "total_issues": 0,
            "success_rate": 0.0,
            "average_processing_time": 0.0,
            "recent_activity": [],
            "quality_stats": {
                "ultra_fast": {"count": 0, "avg_time": 0.0},
                "fast": {"count": 0, "avg_time": 0.0},
                "smart": {"count": 0, "avg_time": 0.0},
                "comprehensive": {"count": 0, "avg_time": 0.0},
                "ai_enhanced": {"count": 0, "avg_time": 0.0},
            },
        }

        # Setup routes
        self._setup_routes()

        # Background tasks
        self._start_background_tasks()
    
    def _get_allowed_directories(self) -> list[Path]:
        """
        Get list of allowed directories for file operations.
        
        TODO: PRODUCTION - Load from configuration or environment variables
        
        Returns:
            List of absolute paths that are safe to access
        """
        # Default to current working directory and user's home directory
        cwd = Path.cwd().resolve()
        home = Path.home().resolve()
        
        # TODO: Add configuration for additional allowed directories
        return [cwd, home]
    
    def _validate_path(self, path_str: str) -> tuple[bool, str | None]:
        """
        Validate and sanitize file path to prevent directory traversal attacks.
        
        Args:
            path_str: Path string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Resolve path to absolute canonical form
            path = Path(path_str).expanduser().resolve(strict=False)
            
            # Check if path is within allowed directories
            is_allowed = any(
                path.is_relative_to(allowed_dir) 
                for allowed_dir in self.allowed_directories
            )
            
            if not is_allowed:
                return False, f"Access denied: Path outside allowed directories"
            
            # Additional checks
            if not path.exists():
                return False, f"Path does not exist: {path}"
            
            return True, None
            
        except (ValueError, OSError, RuntimeError) as e:
            return False, f"Invalid path: {e}"
    
    def _sanitize_file_list(self, files: list[str]) -> tuple[list[str], list[str]]:
        """
        Validate and sanitize a list of file paths.
        
        Args:
            files: List of file paths to validate
            
        Returns:
            Tuple of (valid_files, error_messages)
        """
        valid_files = []
        errors = []
        
        for file_path in files:
            is_valid, error = self._validate_path(file_path)
            if is_valid:
                valid_files.append(str(Path(file_path).resolve()))
            else:
                errors.append(f"{file_path}: {error}")
        
        return valid_files, errors

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route("/")
        def index():
            """Main dashboard page."""
            return render_template("index.html", data=self.dashboard_data)

        @self.app.route("/api/status")
        def api_status():
            """API endpoint for dashboard status."""
            return jsonify(self._get_status())

        @self.app.route("/api/metrics")
        def api_metrics():
            """API endpoint for metrics data."""
            return jsonify(self._get_metrics())

        @self.app.route("/api/quality-check", methods=["POST"])
        def api_quality_check():
            """API endpoint for running quality checks."""
            try:
                # Get JSON data with fallback to empty dict
                data = request.get_json(silent=True) or {}

                # Extract and validate parameters
                mode = data.get("mode", "fast")
                files = data.get("files", [])
                directory = data.get("directory", "")

                # Validate types
                if not isinstance(files, list):
                    return jsonify({"error": "files must be a list"}), 400
                if not isinstance(directory, str):
                    return jsonify({"error": "directory must be a string"}), 400

                if not files and not directory:
                    return jsonify({"error": "No files or directory specified"}), 400
                
                # TODO: SECURITY - Validate file paths before processing
                if files:
                    valid_files, file_errors = self._sanitize_file_list(files)
                    if file_errors:
                        return jsonify({
                            "error": "Invalid file paths detected",
                            "details": file_errors
                        }), 400
                    files = valid_files

                # Normalize mode to lowercase, preserving hyphens for enum compatibility
                normalized_mode = mode.lower().strip()

                # Map normalized mode to QualityMode enum
                try:
                    quality_mode = QualityMode(normalized_mode)
                except ValueError:
                    return jsonify({"error": f"Unknown quality mode: {mode}"}), 400

                # Set AI flag based on normalized mode
                enable_ai_agents = normalized_mode == "ai_enhanced"

                # Handle directory scanning if no files provided
                if not files and directory:
                    import glob

                    # TODO: SECURITY - Validate directory path
                    is_valid, error_msg = self._validate_path(directory)
                    if not is_valid:
                        return jsonify({"error": error_msg}), 403
                    
                    # Validate and resolve directory
                    try:
                        resolved_dir = Path(directory).expanduser().resolve()
                        if not resolved_dir.is_dir():
                            return (
                                jsonify(
                                    {"error": f"Path is not a directory: {directory}"}
                                ),
                                400,
                            )
                    except Exception:
                        return (
                            jsonify({"error": f"Invalid directory path: {directory}"}),
                            400,
                        )

                    # Scan directory for relevant files with limit
                    max_scan_files = 1000
                    extensions = ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"]
                    scanned_files = []

                    for ext in extensions:
                        pattern = str(resolved_dir / "**" / ext)
                        scanned_files.extend(glob.glob(pattern, recursive=True))

                        # Check if we've hit the limit
                        if len(scanned_files) >= max_scan_files:
                            scanned_files = scanned_files[:max_scan_files]
                            break

                    if not scanned_files:
                        return (
                            jsonify(
                                {
                                    "error": f"No relevant files found in directory: {directory}"
                                }
                            ),
                            400,
                        )

                    # Warn if results were limited
                    if len(scanned_files) == max_scan_files:
                        self.app.logger.warning(
                            "Directory scan limited to %d files for: %s",
                            max_scan_files,
                            directory,
                        )

                    files = scanned_files

                # Run quality check
                inputs = QualityInputs(
                    mode=quality_mode,
                    files=files,
                    enable_ai_agents=enable_ai_agents,
                )

                # TODO: PERFORMANCE - Flask doesn't natively support async routes
                # In production, consider migrating to FastAPI or use asyncio.run()
                result = asyncio.run(self._simulate_quality_check(inputs))

                # Update dashboard data with normalized mode
                self._update_dashboard_data(result, normalized_mode)

                return jsonify(result)

            except Exception:
                # Log the full exception for debugging
                self.app.logger.exception("Error in quality check endpoint")
                return jsonify({"error": "Internal server error"}), 500

        @self.app.route("/api/config", methods=["GET", "POST"])
        def api_config():
            """API endpoint for configuration management."""
            if request.method == "GET":
                # TODO: PERFORMANCE - Use async/await properly
                config = asyncio.run(self._get_config())
                return jsonify(config)
            else:
                # Handle malformed JSON as client error
                try:
                    config = request.get_json()
                    if config is None:
                        return jsonify({"error": "Invalid JSON"}), 400
                except Exception:
                    return jsonify({"error": "Invalid JSON"}), 400

                # Handle internal errors
                try:
                    # TODO: PERFORMANCE - Use async/await properly
                    asyncio.run(self._save_config(config))
                    return jsonify({"success": True})
                except Exception:
                    # Log the full exception for debugging
                    self.app.logger.exception("Error saving configuration")
                    return jsonify({"error": "Internal server error"}), 500

        @self.app.route("/api/history")
        def api_history():
            """API endpoint for activity history."""
            return jsonify(self._get_history())

        @self.app.route("/api/health")
        def api_health():
            """
            Health check endpoint.

            Query params:
                detailed: If 'true', perform comprehensive health check.
                         Otherwise, perform quick check for low latency.

            Returns:
                Health status with uptime and version info.
            """
            detailed = request.args.get("detailed", "false").lower() == "true"

            # Get health status from checker
            if detailed:
                health_result = asyncio.run(
                    self.health_checker.check_all(use_cache=True)
                )
            else:
                health_result = asyncio.run(self.health_checker.check_quick())

            # Add dashboard-specific info
            health_result["uptime"] = (
                datetime.now() - self.dashboard_data["start_time"]
            ).total_seconds()
            health_result["version"] = "1.0.0"

            return jsonify(health_result)

    def _get_status(self) -> dict[str, Any]:
        """Get current dashboard status."""
        uptime = datetime.now() - self.dashboard_data["start_time"]

        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_formatted": str(uptime).split(".")[0],
            "total_checks": self.dashboard_data["total_checks"],
            "total_issues": self.dashboard_data["total_issues"],
            "success_rate": self.dashboard_data["success_rate"],
            "average_processing_time": self.dashboard_data["average_processing_time"],
            "quality_stats": self.dashboard_data["quality_stats"],
        }

    def _get_metrics(self) -> dict[str, Any]:
        """Get metrics data."""
        # In a real implementation, this would fetch from MetricsCollector
        return {
            "processing_times": self._get_processing_times_data(),
            "issue_counts": self._get_issue_counts_data(),
            "quality_mode_usage": self._get_quality_mode_usage_data(),
        }

    def _get_processing_times_data(self) -> list[dict[str, Any]]:
        """Get processing times data for charts."""
        # Simulate processing times data
        data = []
        for i in range(24):
            timestamp = datetime.now() - timedelta(hours=23 - i)
            data.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "processing_time": 2.5 + (i % 3) * 0.5,  # Simulated data
                }
            )
        return data

    def _get_issue_counts_data(self) -> list[dict[str, Any]]:
        """Get issue counts data for charts."""
        # Simulate issue counts data
        data = []
        for i in range(24):
            timestamp = datetime.now() - timedelta(hours=23 - i)
            data.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "issues": 5 + (i % 5),  # Simulated data
                }
            )
        return data

    def _get_quality_mode_usage_data(self) -> dict[str, int]:
        """Get quality mode usage data."""
        return {
            mode: stats["count"]
            for mode, stats in self.dashboard_data["quality_stats"].items()
        }

    async def _simulate_quality_check(self, inputs: QualityInputs) -> dict[str, Any]:
        """
        Simulate a quality check result.
        
        TODO: PRODUCTION - Replace with actual async quality engine call:
        result = await self.quality_engine.run_async(inputs)
        """
        # In a real implementation, this would call the actual quality engine
        import random
        
        # Simulate async processing delay
        await asyncio.sleep(0.1)

        processing_time = random.uniform(1.0, 5.0)
        total_issues = random.randint(0, 20)

        return {
            "success": True,
            "total_issues_found": total_issues,
            "processing_time": processing_time,
            "mode": inputs.mode.value,
            "files_checked": len(inputs.files),
            "issues_by_tool": {
                "ruff": random.randint(0, 5),
                "mypy": random.randint(0, 3),
                "bandit": random.randint(0, 2),
            },
        }

    def _update_dashboard_data(self, result: dict[str, Any], mode: str):
        """Update dashboard data with new quality check result."""
        self.dashboard_data["total_checks"] += 1
        self.dashboard_data["total_issues"] += result.get("total_issues_found", 0)

        # Update success rate (unconditionally)
        successful_checks = sum(
            1
            for activity in self.dashboard_data["recent_activity"]
            if activity.get("success", False)
        )
        # Add 1 if current result is successful (since recent_activity excludes current result)
        if result.get("success", False):
            successful_checks += 1

        # Guard against division by zero
        if self.dashboard_data["total_checks"] > 0:
            self.dashboard_data["success_rate"] = (
                successful_checks / self.dashboard_data["total_checks"]
            )
        else:
            self.dashboard_data["success_rate"] = 0.0

        # Update average processing time
        current_avg = self.dashboard_data["average_processing_time"]
        new_time = result.get("processing_time", 0)
        total_checks = self.dashboard_data["total_checks"]
        self.dashboard_data["average_processing_time"] = (
            current_avg * (total_checks - 1) + new_time
        ) / total_checks

        # Update quality mode stats
        if mode in self.dashboard_data["quality_stats"]:
            stats = self.dashboard_data["quality_stats"][mode]
            stats["count"] += 1
            stats["avg_time"] = (
                stats["avg_time"] * (stats["count"] - 1) + new_time
            ) / stats["count"]

        # Add to recent activity
        activity = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "files_checked": result.get("files_checked", 0),
            "issues_found": result.get("total_issues_found", 0),
            "processing_time": result.get("processing_time", 0),
            "success": result.get("success", False),
        }

        self.dashboard_data["recent_activity"].append(activity)

        # Keep only last 50 activities
        if len(self.dashboard_data["recent_activity"]) > 50:
            self.dashboard_data["recent_activity"] = self.dashboard_data[
                "recent_activity"
            ][-50:]

    async def _get_config(self) -> dict[str, Any]:
        """
        Get current configuration.
        
        TODO: PERFORMANCE - Use aiofiles for async file I/O in production
        """
        config_path = Path.home() / ".autopr" / "dashboard_config.json"
        if config_path.exists():
            try:
                # TODO: Replace with async file I/O: async with aiofiles.open(...)
                with open(config_path) as f:
                    return json.load(f)
            except Exception:
                pass

        return self._get_default_config()

    async def _save_config(self, config: dict[str, Any]):
        """
        Save configuration.
        
        TODO: PERFORMANCE - Use aiofiles for async file I/O in production
        """
        config_path = Path.home() / ".autopr" / "dashboard_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # TODO: Replace with async file I/O: async with aiofiles.open(...)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        return {
            "quality_mode": "fast",
            "auto_fix": False,
            "notifications": True,
            "max_file_size": 10000,
            "refresh_interval": 30,
        }

    def _get_history(self) -> list[dict[str, Any]]:
        """Get activity history."""
        return self.dashboard_data["recent_activity"]

    def _start_background_tasks(self):
        """Start background tasks."""

        def update_metrics():
            while True:
                try:
                    # Update metrics every 30 seconds
                    time.sleep(30)
                    # In a real implementation, this would update from MetricsCollector
                except Exception:
                    pass

        metrics_thread = threading.Thread(target=update_metrics, daemon=True)
        metrics_thread.start()

    def run(self):
        """Run the dashboard server."""

        self.app.run(
            host=self.host, port=self.port, debug=self.debug, use_reloader=False
        )


def create_dashboard(
    host: str = "localhost", port: int = 8080, debug: bool = False
) -> AutoPRDashboard:
    """Create and return a dashboard instance."""
    return AutoPRDashboard(host=host, port=port, debug=debug)


def run_dashboard(host: str = "localhost", port: int = 8080, debug: bool = False):
    """Run the AutoPR dashboard."""
    dashboard = create_dashboard(host=host, port=port, debug=debug)
    dashboard.run()


if __name__ == "__main__":
    run_dashboard()
