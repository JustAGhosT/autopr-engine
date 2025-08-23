"""
AutoPR Dashboard Server

Flask-based web server for AutoPR monitoring and configuration.
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

from autopr.quality.metrics_collector import MetricsCollector
from autopr.actions.quality_engine.engine import QualityEngine, QualityInputs
from autopr.actions.quality_engine.models import QualityMode


class AutoPRDashboard:
    """AutoPR Dashboard server for monitoring and configuration."""

    def __init__(self, host: str = "localhost", port: int = 8080, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug

        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)

        # Initialize components
        self.metrics_collector = MetricsCollector()
        self.quality_engine = QualityEngine()

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
                data = request.get_json()
                mode = data.get("mode", "fast")
                files = data.get("files", [])
                directory = data.get("directory", "")

                if not files and not directory:
                    return jsonify({"error": "No files or directory specified"}), 400

                # Normalize mode: lowercase and replace hyphens with underscores
                normalized_mode = mode.lower().replace("-", "_").strip()

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

                    # Scan directory for relevant files
                    extensions = ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"]
                    scanned_files = []
                    for ext in extensions:
                        pattern = str(Path(directory) / "**" / ext)
                        scanned_files.extend(glob.glob(pattern, recursive=True))

                    if not scanned_files:
                        return (
                            jsonify(
                                {
                                    "error": f"No relevant files found in directory: {directory}"
                                }
                            ),
                            400,
                        )

                    files = scanned_files

                # Run quality check
                inputs = QualityInputs(
                    mode=quality_mode,
                    files=files,
                    enable_ai_agents=enable_ai_agents,
                )

                # Note: This would need to be async in a real implementation
                # For now, we'll simulate the result
                result = self._simulate_quality_check(inputs)

                # Update dashboard data with normalized mode
                self._update_dashboard_data(result, normalized_mode)

                return jsonify(result)

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/config", methods=["GET", "POST"])
        def api_config():
            """API endpoint for configuration management."""
            if request.method == "GET":
                return jsonify(self._get_config())
            else:
                try:
                    config = request.get_json()
                    self._save_config(config)
                    return jsonify({"success": True})
                except Exception as e:
                    return jsonify({"error": str(e)}), 500

        @self.app.route("/api/history")
        def api_history():
            """API endpoint for activity history."""
            return jsonify(self._get_history())

        @self.app.route("/api/health")
        def api_health():
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "uptime": (
                        datetime.now() - self.dashboard_data["start_time"]
                    ).total_seconds(),
                    "version": "1.0.0",
                }
            )

    def _get_status(self) -> Dict[str, Any]:
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

    def _get_metrics(self) -> Dict[str, Any]:
        """Get metrics data."""
        # In a real implementation, this would fetch from MetricsCollector
        return {
            "processing_times": self._get_processing_times_data(),
            "issue_counts": self._get_issue_counts_data(),
            "quality_mode_usage": self._get_quality_mode_usage_data(),
        }

    def _get_processing_times_data(self) -> List[Dict[str, Any]]:
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

    def _get_issue_counts_data(self) -> List[Dict[str, Any]]:
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

    def _get_quality_mode_usage_data(self) -> Dict[str, int]:
        """Get quality mode usage data."""
        return {
            mode: stats["count"]
            for mode, stats in self.dashboard_data["quality_stats"].items()
        }

    def _simulate_quality_check(self, inputs: QualityInputs) -> Dict[str, Any]:
        """Simulate a quality check result."""
        # In a real implementation, this would call the actual quality engine
        import random

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

    def _update_dashboard_data(self, result: Dict[str, Any], mode: str):
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

    def _get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        config_path = Path.home() / ".autopr" / "dashboard_config.json"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass

        return self._get_default_config()

    def _save_config(self, config: Dict[str, Any]):
        """Save configuration."""
        config_path = Path.home() / ".autopr" / "dashboard_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "quality_mode": "fast",
            "auto_fix": False,
            "notifications": True,
            "max_file_size": 10000,
            "refresh_interval": 30,
        }

    def _get_history(self) -> List[Dict[str, Any]]:
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
                except Exception as e:
                    print(f"Error in background metrics update: {e}")

        metrics_thread = threading.Thread(target=update_metrics, daemon=True)
        metrics_thread.start()

    def run(self):
        """Run the dashboard server."""
        print(f"🚀 Starting AutoPR Dashboard on http://{self.host}:{self.port}")
        print("📊 Dashboard features:")
        print("   - Real-time quality metrics")
        print("   - Quality check execution")
        print("   - Configuration management")
        print("   - Activity history")
        print("   - Health monitoring")

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
