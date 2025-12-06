"""FastAPI Dashboard Router.

Provides dashboard UI and API endpoints for the AutoPR Engine.
"""

import asyncio
import json
import logging
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from autopr.actions.quality_engine.models import QualityMode

# Version - single source of truth, imported by server.py
__version__ = "1.0.1"

logger = logging.getLogger(__name__)


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
    """Manages dashboard state and data.

    Note: State is stored in memory and will be lost on restart.
    For production, consider backing with Redis or database.
    """

    def __init__(self):
        self._lock = threading.Lock()  # Thread-safe state updates
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
        self._allowed_directories = self._get_allowed_directories()

    def get_uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

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
        with self._lock:
            uptime = datetime.now() - self.start_time
            return {
                "uptime_seconds": uptime.total_seconds(),
                "uptime_formatted": str(uptime).split(".")[0],
                "total_checks": self.total_checks,
                "total_issues": self.total_issues,
                "success_rate": self.success_rate,
                "average_processing_time": self.average_processing_time,
                "quality_stats": self.quality_stats.copy(),
            }

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics data for charts.

        Note: Returns actual historical data from recent_activity when available,
        otherwise returns placeholder data for chart rendering.
        """
        with self._lock:
            return {
                "processing_times": self._get_processing_times_data(),
                "issue_counts": self._get_issue_counts_data(),
                "quality_mode_usage": self._get_quality_mode_usage_data(),
            }

    def _get_processing_times_data(self) -> list[dict[str, Any]]:
        """Get processing times data for charts from recent activity."""
        # Return actual data from recent activity if available
        if self.recent_activity:
            return [
                {
                    "timestamp": activity["timestamp"],
                    "processing_time": activity.get("processing_time", 0),
                }
                for activity in self.recent_activity[-24:]
            ]
        # Return empty list when no data (frontend should handle empty state)
        return []

    def _get_issue_counts_data(self) -> list[dict[str, Any]]:
        """Get issue counts data for charts from recent activity."""
        # Return actual data from recent activity if available
        if self.recent_activity:
            return [
                {
                    "timestamp": activity["timestamp"],
                    "issues": activity.get("issues_found", 0),
                }
                for activity in self.recent_activity[-24:]
            ]
        # Return empty list when no data
        return []

    def _get_quality_mode_usage_data(self) -> dict[str, int]:
        """Get quality mode usage data."""
        return {
            mode: stats["count"]
            for mode, stats in self.quality_stats.items()
        }

    def update_with_result(self, result: dict[str, Any], mode: str):
        """Update dashboard data with quality check result (thread-safe)."""
        with self._lock:
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


def _get_config_path() -> Path:
    """Get configuration file path, handling container environments."""
    # Check for explicit config directory
    config_dir = os.getenv("AUTOPR_CONFIG_DIR")
    if config_dir:
        return Path(config_dir) / "dashboard_config.json"

    # Try XDG config directory (Linux standard)
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "autopr" / "dashboard_config.json"

    # Try home directory
    try:
        home = Path.home()
        return home / ".autopr" / "dashboard_config.json"
    except (RuntimeError, OSError):
        # Fallback for containers without home directory
        return Path("/tmp") / ".autopr" / "dashboard_config.json"


# Create router and state
router = APIRouter(tags=["dashboard"])
dashboard_state = DashboardState()

# Set up templates with error handling
templates_dir = Path(__file__).parent / "templates"
templates: Jinja2Templates | None = None

if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))
else:
    logger.warning(f"Templates directory not found: {templates_dir}")


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Serve the main dashboard page."""
    if templates is None:
        return HTMLResponse(
            content="<html><body><h1>Dashboard templates not found</h1>"
            "<p>Please ensure the templates directory exists.</p></body></html>",
            status_code=503
        )

    try:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "data": dashboard_state.get_status()}
        )
    except Exception as e:
        logger.error(f"Failed to render dashboard template: {e}")
        return HTMLResponse(
            content=f"<html><body><h1>Template Error</h1><p>{e}</p></body></html>",
            status_code=500
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
    return dashboard_state.recent_activity.copy()


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
    files = list(request.files)  # Copy to avoid mutation
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
        except OSError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid directory path: {directory} - {e}"
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

        # Validate scanned files to ensure they're within allowed directories
        validated_files = []
        for scanned_file in scanned_files:
            is_valid, _ = dashboard_state.validate_path(scanned_file)
            if is_valid:
                validated_files.append(scanned_file)

        if not validated_files:
            raise HTTPException(
                status_code=403,
                detail="No accessible files found in directory"
            )
        files = validated_files

    # Run quality check using the actual engine
    result = await _run_quality_check(files, normalized_mode)

    # Update dashboard state
    dashboard_state.update_with_result(result, normalized_mode)

    return result


async def _run_quality_check(files: list[str], mode: str) -> dict[str, Any]:
    """Run quality check using the actual QualityEngine.

    Falls back to simulation if engine is not available.
    """
    import time

    try:
        from autopr.actions.quality_engine.engine import QualityEngine
        from autopr.actions.quality_engine.models import QualityInputs

        start_time = time.time()

        engine = QualityEngine()
        inputs = QualityInputs(
            mode=QualityMode(mode),
            files=files,
            enable_ai_agents=(mode == "ai_enhanced"),
        )

        # Run the quality check
        result = await asyncio.to_thread(engine.run, inputs)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "total_issues_found": getattr(result, 'total_issues', 0),
            "processing_time": processing_time,
            "mode": mode,
            "files_checked": len(files),
            "issues_by_tool": getattr(result, 'issues_by_tool', {}),
            "details": getattr(result, 'details', None),
        }
    except ImportError:
        logger.warning("QualityEngine not available, using simulation")
        return await _simulate_quality_check(files, mode)
    except Exception as e:
        logger.error(f"Quality check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_issues_found": 0,
            "processing_time": 0,
            "mode": mode,
            "files_checked": len(files),
        }


async def _simulate_quality_check(files: list[str], mode: str) -> dict[str, Any]:
    """Simulate a quality check result (fallback when engine unavailable)."""
    import random

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
        "simulated": True,  # Flag to indicate this is simulated data
    }


@router.get("/api/config")
async def get_config():
    """Get current configuration."""
    config_path = _get_config_path()
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid config file: {e}")
        except OSError as e:
            logger.warning(f"Could not read config file: {e}")

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
    config_path = _get_config_path()

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config.model_dump(), f, indent=2)
        return {"success": True}
    except OSError as e:
        logger.error(f"Failed to save config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save config: {e}")
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to serialize config: {e}")


# Export for use by server.py
__all__ = ["router", "dashboard_state", "DashboardState", "__version__"]
