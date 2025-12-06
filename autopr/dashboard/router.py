"""FastAPI Dashboard Router.

Provides dashboard UI and API endpoints for the AutoPR Engine.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from autopr.actions.quality_engine.models import QualityMode
from autopr.health.health_checker import HealthChecker


# Pydantic models for request/response validation
class QualityCheckRequest(BaseModel):
    """Request model for quality check endpoint."""
    mode: str = Field(default="fast", description="Quality check mode")
    files: list[str] = Field(default_factory=list, description="List of files to check")
    directory: str = Field(default="", description="Directory to scan")


class ConfigRequest(BaseModel):
    """Request model for configuration endpoint."""
    quality_mode: str = Field(default="fast", description="Default quality mode")
    auto_fix: bool = Field(default=False, description="Enable auto-fix")
    max_file_size: int = Field(default=10000, description="Max file size in lines")
    notifications: bool = Field(default=True, description="Enable notifications")
    refresh_interval: int = Field(default=30, description="Dashboard refresh interval")


class DashboardState:
    """Manages dashboard state and data."""

    def __init__(self):
        self.start_time = datetime.now()
        self.total_checks = 0
        self.total_issues = 0
        self.success_rate = 0.0
        self.average_processing_time = 0.0
        self.recent_activity: list[dict[str, Any]] = []
        # Note: ai_enhanced uses underscore to match QualityMode enum
        self.quality_stats = {
            "ultra-fast": {"count": 0, "avg_time": 0.0},
            "fast": {"count": 0, "avg_time": 0.0},
            "smart": {"count": 0, "avg_time": 0.0},
            "comprehensive": {"count": 0, "avg_time": 0.0},
            "ai_enhanced": {"count": 0, "avg_time": 0.0},
        }
        self.health_checker = HealthChecker()
        self._allowed_directories = self._get_allowed_directories()

    def _get_allowed_directories(self) -> list[Path]:
        """Get list of allowed directories for file operations."""
        cwd = Path.cwd().resolve()
        home = Path.home().resolve()
        return [cwd, home]

    def validate_path(self, path_str: str) -> tuple[bool, str | None]:
        """Validate path to prevent directory traversal attacks."""
        try:
            path = Path(path_str).expanduser().resolve(strict=False)
            is_allowed = any(
                path.is_relative_to(allowed_dir)
                for allowed_dir in self._allowed_directories
            )
            if not is_allowed:
                return False, "Access denied: Path outside allowed directories"
            if not path.exists():
                return False, f"Path does not exist: {path}"
            return True, None
        except (ValueError, OSError, RuntimeError) as e:
            return False, f"Invalid path: {e}"

    def sanitize_file_list(self, files: list[str]) -> tuple[list[str], list[str]]:
        """Validate and sanitize a list of file paths.

        Args:
            files: List of file paths to validate

        Returns:
            Tuple of (valid_files, error_messages)
        """
        valid_files = []
        errors = []

        for file_path in files:
            is_valid, error = self.validate_path(file_path)
            if is_valid:
                valid_files.append(str(Path(file_path).resolve()))
            else:
                errors.append(f"{file_path}: {error}")

        return valid_files, errors

    def get_status(self) -> dict[str, Any]:
        """Get current dashboard status."""
        uptime = datetime.now() - self.start_time
        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_formatted": str(uptime).split(".")[0],
            "total_checks": self.total_checks,
            "total_issues": self.total_issues,
            "success_rate": self.success_rate,
            "average_processing_time": self.average_processing_time,
            "quality_stats": self.quality_stats,
        }

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics data for charts."""
        return {
            "processing_times": self._get_processing_times_data(),
            "issue_counts": self._get_issue_counts_data(),
            "quality_mode_usage": self._get_quality_mode_usage_data(),
        }

    def _get_processing_times_data(self) -> list[dict[str, Any]]:
        """Get processing times data for charts."""
        data = []
        for i in range(24):
            timestamp = datetime.now() - timedelta(hours=23 - i)
            data.append({
                "timestamp": timestamp.isoformat(),
                "processing_time": 2.5 + (i % 3) * 0.5,
            })
        return data

    def _get_issue_counts_data(self) -> list[dict[str, Any]]:
        """Get issue counts data for charts."""
        data = []
        for i in range(24):
            timestamp = datetime.now() - timedelta(hours=23 - i)
            data.append({
                "timestamp": timestamp.isoformat(),
                "issues": 5 + (i % 5),
            })
        return data

    def _get_quality_mode_usage_data(self) -> dict[str, int]:
        """Get quality mode usage data."""
        return {
            mode: stats["count"]
            for mode, stats in self.quality_stats.items()
        }

    def update_with_result(self, result: dict[str, Any], mode: str):
        """Update dashboard data with quality check result."""
        self.total_checks += 1
        self.total_issues += result.get("total_issues_found", 0)

        # Update success rate
        successful_checks = sum(
            1 for activity in self.recent_activity if activity.get("success", False)
        )
        if result.get("success", False):
            successful_checks += 1
        if self.total_checks > 0:
            self.success_rate = successful_checks / self.total_checks
        else:
            self.success_rate = 0.0

        # Update average processing time
        new_time = result.get("processing_time", 0)
        if self.total_checks > 1:
            self.average_processing_time = (
                self.average_processing_time * (self.total_checks - 1) + new_time
            ) / self.total_checks
        else:
            self.average_processing_time = new_time

        # Update quality mode stats
        if mode in self.quality_stats:
            stats = self.quality_stats[mode]
            stats["count"] += 1
            if stats["count"] > 1:
                stats["avg_time"] = (
                    stats["avg_time"] * (stats["count"] - 1) + new_time
                ) / stats["count"]
            else:
                stats["avg_time"] = new_time

        # Add to recent activity
        activity = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "files_checked": result.get("files_checked", 0),
            "issues_found": result.get("total_issues_found", 0),
            "processing_time": result.get("processing_time", 0),
            "success": result.get("success", False),
        }
        self.recent_activity.append(activity)

        # Keep only last 50 activities
        if len(self.recent_activity) > 50:
            self.recent_activity = self.recent_activity[-50:]


# Create router and state
router = APIRouter(tags=["dashboard"])
dashboard_state = DashboardState()

# Set up templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Serve the main dashboard page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "data": dashboard_state.get_status()}
    )


@router.get("/api/status")
async def api_status():
    """Get dashboard status."""
    return dashboard_state.get_status()


@router.get("/api/metrics")
async def api_metrics():
    """Get metrics data."""
    return dashboard_state.get_metrics()


@router.get("/api/history")
async def api_history():
    """Get activity history."""
    return dashboard_state.recent_activity


@router.get("/api/health")
async def api_health(detailed: bool = Query(False, description="Return detailed health info")):
    """
    Health check endpoint for dashboard.

    Args:
        detailed: If True, perform comprehensive health check.

    Returns:
        Health status with uptime and version info.
    """
    if detailed:
        health_result = await dashboard_state.health_checker.check_all(use_cache=True)
    else:
        health_result = await dashboard_state.health_checker.check_quick()

    health_result["uptime"] = (
        datetime.now() - dashboard_state.start_time
    ).total_seconds()
    health_result["version"] = "1.0.0"
    return health_result


@router.post("/api/quality-check")
async def api_quality_check(request: QualityCheckRequest):
    """
    Run a quality check on specified files or directory.

    Args:
        request: Quality check request with mode, files, and directory.

    Returns:
        Quality check results.
    """
    import glob as glob_module

    mode = request.mode
    files = request.files
    directory = request.directory

    if not files and not directory:
        raise HTTPException(status_code=400, detail="No files or directory specified")

    # Validate file paths
    if files:
        valid_files = []
        for file_path in files:
            is_valid, error = dashboard_state.validate_path(file_path)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid file path: {error}")
            valid_files.append(str(Path(file_path).resolve()))
        files = valid_files

    # Normalize mode - convert hyphens to underscores for ai-enhanced -> ai_enhanced
    normalized_mode = mode.lower().strip().replace("-", "_")
    # But keep ultra-fast as hyphenated (it's the enum value)
    if normalized_mode == "ultra_fast":
        normalized_mode = "ultra-fast"

    # Validate mode
    try:
        QualityMode(normalized_mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown quality mode: {mode}")

    # Handle directory scanning
    if not files and directory:
        is_valid, error = dashboard_state.validate_path(directory)
        if not is_valid:
            raise HTTPException(status_code=403, detail=error)

        try:
            resolved_dir = Path(directory).expanduser().resolve()
            if not resolved_dir.is_dir():
                raise HTTPException(
                    status_code=400,
                    detail=f"Path is not a directory: {directory}"
                )
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid directory path: {directory}"
            )

        # Scan directory for relevant files
        max_scan_files = 1000
        extensions = ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"]
        scanned_files = []

        for ext in extensions:
            pattern = str(resolved_dir / "**" / ext)
            scanned_files.extend(glob_module.glob(pattern, recursive=True))
            if len(scanned_files) >= max_scan_files:
                scanned_files = scanned_files[:max_scan_files]
                break

        if not scanned_files:
            raise HTTPException(
                status_code=400,
                detail=f"No relevant files found in directory: {directory}"
            )
        files = scanned_files

    # Simulate quality check (replace with actual engine call in production)
    result = await _simulate_quality_check(files, normalized_mode)

    # Update dashboard state
    dashboard_state.update_with_result(result, normalized_mode)

    return result


async def _simulate_quality_check(files: list[str], mode: str) -> dict[str, Any]:
    """Simulate a quality check result.

    TODO: Replace with actual async quality engine call in production.
    """
    await asyncio.sleep(0.1)
    processing_time = random.uniform(1.0, 5.0)
    total_issues = random.randint(0, 20)

    return {
        "success": True,
        "total_issues_found": total_issues,
        "processing_time": processing_time,
        "mode": mode,
        "files_checked": len(files),
        "issues_by_tool": {
            "ruff": random.randint(0, 5),
            "mypy": random.randint(0, 3),
            "bandit": random.randint(0, 2),
        },
    }


@router.get("/api/config")
async def get_config():
    """Get current configuration."""
    config_path = Path.home() / ".autopr" / "dashboard_config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "quality_mode": "fast",
        "auto_fix": False,
        "notifications": True,
        "max_file_size": 10000,
        "refresh_interval": 30,
    }


@router.post("/api/config")
async def save_config(config: ConfigRequest):
    """Save configuration."""
    config_path = Path.home() / ".autopr" / "dashboard_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, "w") as f:
            json.dump(config.model_dump(), f, indent=2)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {e}")
