"""FastAPI Dashboard Router.

Provides dashboard UI and API endpoints for the AutoPR Engine.
"""

import asyncio
import json
import logging
import os
import secrets
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from autopr.actions.quality_engine.models import QualityMode

# Version - single source of truth, imported by server.py
__version__ = "1.0.1"

logger = logging.getLogger(__name__)


# =============================================================================
# Response Models (for OpenAPI documentation)
# =============================================================================

class QualityModeStats(BaseModel):
    """Statistics for a quality mode."""
    count: int = Field(description="Number of checks run in this mode")
    avg_time: float = Field(description="Average processing time in seconds")


class StatusResponse(BaseModel):
    """Response model for dashboard status."""
    uptime_seconds: float = Field(description="Server uptime in seconds")
    uptime_formatted: str = Field(description="Human-readable uptime string")
    total_checks: int = Field(description="Total quality checks performed")
    total_issues: int = Field(description="Total issues found across all checks")
    success_rate: float = Field(description="Success rate (0.0 to 1.0)")
    average_processing_time: float = Field(description="Average processing time in seconds")
    quality_stats: dict[str, QualityModeStats] = Field(description="Stats per quality mode")


class MetricsResponse(BaseModel):
    """Response model for metrics data."""
    processing_times: list[dict[str, Any]] = Field(description="Processing time history")
    issue_counts: list[dict[str, Any]] = Field(description="Issue count history")
    quality_mode_usage: dict[str, int] = Field(description="Usage count per quality mode")


class ActivityRecord(BaseModel):
    """Single activity record."""
    timestamp: str = Field(description="ISO timestamp of the check")
    mode: str = Field(description="Quality mode used")
    files_checked: int = Field(description="Number of files checked")
    issues_found: int = Field(description="Number of issues found")
    processing_time: float = Field(description="Processing time in seconds")
    success: bool = Field(description="Whether the check succeeded")


class QualityCheckRequest(BaseModel):
    """Request model for quality check endpoint."""
    mode: str = Field(default="fast", description="Quality check mode (ultra-fast, fast, smart, comprehensive, ai_enhanced)")
    files: list[str] = Field(default_factory=list, description="List of file paths to check")
    directory: str = Field(default="", description="Directory to scan for files")

    model_config = {"json_schema_extra": {
        "example": {
            "mode": "fast",
            "files": ["src/main.py", "src/utils.py"],
            "directory": ""
        }
    }}


class QualityCheckResponse(BaseModel):
    """Response model for quality check results."""
    success: bool = Field(description="Whether the check completed successfully")
    total_issues_found: int = Field(description="Total number of issues found")
    processing_time: float = Field(description="Processing time in seconds")
    mode: str = Field(description="Quality mode that was used")
    files_checked: int = Field(description="Number of files checked")
    issues_by_tool: dict[str, int] = Field(default_factory=dict, description="Issue counts per tool")
    simulated: bool = Field(default=False, description="Whether results are simulated")
    error: str | None = Field(default=None, description="Error message if failed")
    details: Any | None = Field(default=None, description="Detailed results")


class ConfigRequest(BaseModel):
    """Request model for configuration endpoint."""
    quality_mode: str = Field(default="fast", description="Default quality mode")
    auto_fix: bool = Field(default=False, description="Enable auto-fix")
    max_file_size: int = Field(default=10000, description="Max file size in lines")
    notifications: bool = Field(default=True, description="Enable notifications")
    refresh_interval: int = Field(default=30, description="Dashboard refresh interval in seconds")


class ConfigResponse(BaseModel):
    """Response model for configuration."""
    quality_mode: str
    auto_fix: bool
    notifications: bool
    max_file_size: int
    refresh_interval: int


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = Field(description="Operation success status")


# =============================================================================
# Rate Limiting
# =============================================================================

# Use the existing rate limiter from security module
from autopr.security.rate_limiting import RateLimiter as SecurityRateLimiter


class RateLimiter:
    """Rate limiter wrapper for dashboard endpoints.

    Provides a simplified API on top of the security module's RateLimiter.
    Limits requests per IP address within a time window.
    """

    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self._limiter = SecurityRateLimiter(
            default_limit=requests_per_minute,
            window_seconds=60
        )
        self._last_info: dict[str, dict] = {}  # Store last info for get_retry_after
        self._max_cached_ips = 10000  # Prevent unbounded memory growth

    def is_allowed(self, client_ip: str) -> bool:
        """Check if request from client IP is allowed."""
        allowed, info = self._limiter.is_allowed(client_ip, limit=self.requests_per_minute)
        # Evict oldest entries if cache is too large
        if len(self._last_info) >= self._max_cached_ips:
            # Simple eviction: clear half the cache (dict maintains insertion order in Python 3.7+)
            keys_to_remove = list(self._last_info.keys())[:len(self._last_info) // 2]
            for key in keys_to_remove:
                del self._last_info[key]
        self._last_info[client_ip] = info
        return allowed

    def get_retry_after(self, client_ip: str) -> int:
        """Get seconds until next request is allowed."""
        if client_ip in self._last_info:
            return self._last_info[client_ip].get("retry_after", 0)
        # If no cached info, check current state
        _, info = self._limiter.is_allowed(client_ip, limit=self.requests_per_minute)
        return info.get("retry_after", 0)


# Rate limiter for quality check endpoint (configurable via env var)
_rate_limit = int(os.getenv("AUTOPR_RATE_LIMIT", "10"))
quality_check_limiter = RateLimiter(requests_per_minute=_rate_limit)


# =============================================================================
# Authentication
# =============================================================================

def get_api_key() -> str | None:
    """Get configured API key from environment."""
    return os.getenv("AUTOPR_API_KEY")


async def verify_api_key(
    x_api_key: str | None = Header(default=None, description="API key for authentication")
) -> str | None:
    """Verify API key if authentication is enabled.

    If AUTOPR_API_KEY is set, requests must include matching X-API-Key header.
    If not set, all requests are allowed (open access).
    """
    required_key = get_api_key()

    if required_key is None:
        # No authentication required
        return None

    if x_api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API key required. Set X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Use timing-safe comparison to prevent timing attacks
    if not secrets.compare_digest(x_api_key, required_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )

    return x_api_key


# =============================================================================
# Dashboard State
# =============================================================================

# Import storage after it's defined to avoid circular imports
from autopr.dashboard.storage import get_storage, StorageBackend


class DashboardState:
    """Manages dashboard state and data.

    Supports multiple storage backends:
    - In-memory (default): Fast but not persistent
    - Redis: Persistent and shareable across instances

    Configure via AUTOPR_STORAGE_BACKEND and REDIS_URL environment variables.
    """

    # Storage keys
    KEY_START_TIME = "start_time"
    KEY_TOTAL_CHECKS = "total_checks"
    KEY_TOTAL_ISSUES = "total_issues"
    KEY_TOTAL_SUCCESSFUL_CHECKS = "total_successful_checks"
    KEY_SUCCESS_RATE = "success_rate"
    KEY_AVG_PROCESSING_TIME = "avg_processing_time"
    KEY_RECENT_ACTIVITY = "recent_activity"
    KEY_QUALITY_STATS = "quality_stats"
    KEY_CONFIG = "config"

    # Default quality stats structure
    DEFAULT_QUALITY_STATS = {
        "ultra-fast": {"count": 0, "avg_time": 0.0},
        "fast": {"count": 0, "avg_time": 0.0},
        "smart": {"count": 0, "avg_time": 0.0},
        "comprehensive": {"count": 0, "avg_time": 0.0},
        "ai_enhanced": {"count": 0, "avg_time": 0.0},
    }

    # Default configuration
    DEFAULT_CONFIG = {
        "quality_mode": "fast",
        "auto_fix": False,
        "notifications": True,
        "max_file_size": 10000,
        "refresh_interval": 30,
    }

    def __init__(self, storage: StorageBackend | None = None):
        self._storage = storage or get_storage()
        self._lock = threading.Lock()  # For local operations
        self._allowed_directories = self._get_allowed_directories()

        # Initialize storage with defaults if empty
        self._initialize_storage()

    def _initialize_storage(self) -> None:
        """Initialize storage with default values if empty."""
        self._storage.initialize_if_empty(self.KEY_START_TIME, datetime.now().isoformat())
        self._storage.initialize_if_empty(self.KEY_TOTAL_CHECKS, 0)
        self._storage.initialize_if_empty(self.KEY_TOTAL_ISSUES, 0)
        self._storage.initialize_if_empty(self.KEY_TOTAL_SUCCESSFUL_CHECKS, 0)
        self._storage.initialize_if_empty(self.KEY_SUCCESS_RATE, 0.0)
        self._storage.initialize_if_empty(self.KEY_AVG_PROCESSING_TIME, 0.0)

        # Initialize quality stats
        for mode, stats in self.DEFAULT_QUALITY_STATS.items():
            self._storage.initialize_if_empty(f"{self.KEY_QUALITY_STATS}:{mode}", stats)

    @property
    def start_time(self) -> datetime:
        """Get server start time."""
        time_str = self._storage.get(self.KEY_START_TIME)
        if time_str:
            try:
                return datetime.fromisoformat(time_str)
            except (ValueError, TypeError):
                pass
        return datetime.now()

    @property
    def total_checks(self) -> int:
        """Get total number of checks."""
        return self._storage.get(self.KEY_TOTAL_CHECKS, 0)

    @property
    def total_issues(self) -> int:
        """Get total number of issues found."""
        return self._storage.get(self.KEY_TOTAL_ISSUES, 0)

    @property
    def success_rate(self) -> float:
        """Get success rate."""
        return self._storage.get(self.KEY_SUCCESS_RATE, 0.0)

    @property
    def average_processing_time(self) -> float:
        """Get average processing time."""
        return self._storage.get(self.KEY_AVG_PROCESSING_TIME, 0.0)

    @property
    def recent_activity(self) -> list[dict[str, Any]]:
        """Get recent activity list."""
        return self._storage.get_list(self.KEY_RECENT_ACTIVITY)

    @property
    def quality_stats(self) -> dict[str, dict[str, Any]]:
        """Get quality stats for all modes."""
        stats = {}
        for mode in self.DEFAULT_QUALITY_STATS:
            mode_stats = self._storage.get(f"{self.KEY_QUALITY_STATS}:{mode}")
            stats[mode] = mode_stats if mode_stats else {"count": 0, "avg_time": 0.0}
        return stats

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
        """Get metrics data for charts.

        Note: Returns actual historical data from recent_activity when available,
        otherwise returns empty lists for chart rendering.
        """
        recent = self.recent_activity
        return {
            "processing_times": self._get_processing_times_data(recent),
            "issue_counts": self._get_issue_counts_data(recent),
            "quality_mode_usage": self._get_quality_mode_usage_data(),
        }

    def _get_processing_times_data(self, recent: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Get processing times data for charts from recent activity."""
        if recent:
            return [
                {
                    "timestamp": activity["timestamp"],
                    "processing_time": activity.get("processing_time", 0),
                }
                for activity in recent[-24:]
            ]
        return []

    def _get_issue_counts_data(self, recent: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Get issue counts data for charts from recent activity."""
        if recent:
            return [
                {
                    "timestamp": activity["timestamp"],
                    "issues": activity.get("issues_found", 0),
                }
                for activity in recent[-24:]
            ]
        return []

    def _get_quality_mode_usage_data(self) -> dict[str, int]:
        """Get quality mode usage data."""
        return {
            mode: stats["count"]
            for mode, stats in self.quality_stats.items()
        }

    def update_with_result(self, result: dict[str, Any], mode: str):
        """Update dashboard data with quality check result."""
        with self._lock:
            # Increment counters
            new_total_checks = self._storage.increment(self.KEY_TOTAL_CHECKS, 1)
            issues_found = result.get("total_issues_found", 0)
            self._storage.increment(self.KEY_TOTAL_ISSUES, issues_found)

            # Calculate and update success rate using persistent counter
            if result.get("success", False):
                total_successful = self._storage.increment(
                    self.KEY_TOTAL_SUCCESSFUL_CHECKS, 1
                )
            else:
                total_successful = self._storage.get(
                    self.KEY_TOTAL_SUCCESSFUL_CHECKS, 0
                )
            new_success_rate = (
                total_successful / new_total_checks if new_total_checks > 0 else 0.0
            )
            self._storage.set(self.KEY_SUCCESS_RATE, new_success_rate)

            # Update average processing time
            new_time = result.get("processing_time", 0)
            old_avg = self.average_processing_time
            if new_total_checks > 1:
                new_avg = (old_avg * (new_total_checks - 1) + new_time) / new_total_checks
            else:
                new_avg = new_time
            self._storage.set(self.KEY_AVG_PROCESSING_TIME, new_avg)

            # Update quality mode stats
            if mode in self.DEFAULT_QUALITY_STATS:
                mode_key = f"{self.KEY_QUALITY_STATS}:{mode}"
                current_stats = self._storage.get(mode_key, {"count": 0, "avg_time": 0.0})
                new_count = current_stats["count"] + 1
                if new_count > 1:
                    new_mode_avg = (current_stats["avg_time"] * (new_count - 1) + new_time) / new_count
                else:
                    new_mode_avg = new_time
                self._storage.set(mode_key, {"count": new_count, "avg_time": new_mode_avg})

            # Add to recent activity
            activity = {
                "timestamp": datetime.now().isoformat(),
                "mode": mode,
                "files_checked": result.get("files_checked", 0),
                "issues_found": issues_found,
                "processing_time": result.get("processing_time", 0),
                "success": result.get("success", False),
            }
            self._storage.append_to_list(self.KEY_RECENT_ACTIVITY, activity, max_length=50)

    def get_config(self) -> dict[str, Any]:
        """Get dashboard configuration from storage.

        Falls back to file system config for backwards compatibility,
        then to defaults if neither exists.
        """
        # Try storage backend first
        config = self._storage.get(self.KEY_CONFIG)
        if config:
            return {**self.DEFAULT_CONFIG, **config}

        # Fall back to file system for backwards compatibility
        config_path = _get_config_path()
        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = json.load(f)
                    # Migrate to storage backend
                    self._storage.set(self.KEY_CONFIG, data)
                    return {**self.DEFAULT_CONFIG, **data}
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Could not read config file: {e}")

        return dict(self.DEFAULT_CONFIG)

    def set_config(self, config: dict[str, Any]) -> None:
        """Save dashboard configuration to storage."""
        self._storage.set(self.KEY_CONFIG, config)


# =============================================================================
# Helpers
# =============================================================================

def _get_config_path() -> Path:
    """Get configuration file path, handling container environments."""
    config_dir = os.getenv("AUTOPR_CONFIG_DIR")
    if config_dir:
        return Path(config_dir) / "dashboard_config.json"

    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "autopr" / "dashboard_config.json"

    try:
        home = Path.home()
        return home / ".autopr" / "dashboard_config.json"
    except (RuntimeError, OSError):
        # Use system temp directory when home is not available
        return Path(tempfile.gettempdir()) / ".autopr" / "dashboard_config.json"


def _get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    # Check for forwarded header (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# =============================================================================
# Router Setup
# =============================================================================

router = APIRouter(
    tags=["Dashboard"],
    responses={
        401: {"description": "API key required"},
        403: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
    },
)
dashboard_state = DashboardState()

# Set up templates with error handling
templates_dir = Path(__file__).parent / "templates"
templates: Jinja2Templates | None = None

if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))
else:
    logger.warning(f"Templates directory not found: {templates_dir}")


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "/",
    response_class=HTMLResponse,
    summary="Dashboard UI",
    description="Serves the main dashboard web interface.",
    include_in_schema=False,  # Hide from API docs since it's HTML
)
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
    except Exception:
        logger.exception("Failed to render dashboard template")
        return HTMLResponse(
            content="<html><body><h1>Template Error</h1><p>Internal server error</p></body></html>",
            status_code=500
        )


@router.get(
    "/api/status",
    response_model=StatusResponse,
    summary="Get Dashboard Status",
    description="Returns current dashboard status including uptime, check counts, and statistics.",
)
async def api_status(_: str | None = Depends(verify_api_key)) -> StatusResponse:
    """Get dashboard status."""
    return StatusResponse(**dashboard_state.get_status())


@router.get(
    "/api/metrics",
    response_model=MetricsResponse,
    summary="Get Metrics Data",
    description="Returns metrics data for dashboard charts including processing times and issue counts.",
)
async def api_metrics(_: str | None = Depends(verify_api_key)) -> MetricsResponse:
    """Get metrics data for charts."""
    return MetricsResponse(**dashboard_state.get_metrics())


@router.get(
    "/api/history",
    response_model=list[ActivityRecord],
    summary="Get Activity History",
    description="Returns recent quality check activity history with optional pagination.",
)
async def api_history(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    _: str | None = Depends(verify_api_key),
) -> list[ActivityRecord]:
    """Get activity history with pagination support."""
    all_activity = dashboard_state.recent_activity
    # Apply pagination (newest first, so reverse the list)
    paginated = all_activity[::-1][offset:offset + limit]
    return [ActivityRecord(**record) for record in paginated]


@router.post(
    "/api/quality-check",
    response_model=QualityCheckResponse,
    summary="Run Quality Check",
    description="Run a quality check on specified files or directory. Rate limited to 10 requests per minute.",
    responses={
        429: {"description": "Rate limit exceeded. Retry after the specified time."},
    },
)
async def api_quality_check(
    request: Request,
    body: QualityCheckRequest,
    _: str | None = Depends(verify_api_key),
) -> QualityCheckResponse:
    """Run a quality check on specified files or directory."""
    import glob as glob_module

    # Rate limiting
    client_ip = _get_client_ip(request)
    if not quality_check_limiter.is_allowed(client_ip):
        retry_after = quality_check_limiter.get_retry_after(client_ip)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    mode = body.mode
    files = list(body.files)
    directory = body.directory

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

    # Normalize mode to match QualityMode enum values
    # Enum values: "ultra-fast", "fast", "smart", "comprehensive", "ai_enhanced"
    normalized_mode = mode.lower().strip()

    # Map alternative formats to canonical enum values
    mode_aliases = {
        "ultra_fast": "ultra-fast",
        "ultrafast": "ultra-fast",
        "ai-enhanced": "ai_enhanced",
        "aienhanced": "ai_enhanced",
    }
    normalized_mode = mode_aliases.get(normalized_mode, normalized_mode)

    # Validate mode
    try:
        QualityMode(normalized_mode)
    except ValueError:
        valid_modes = [m.value for m in QualityMode]
        raise HTTPException(
            status_code=400,
            detail=f"Unknown quality mode: {mode}. Valid modes: {', '.join(valid_modes)}"
        )

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

        # Validate scanned files
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

    # Run quality check
    result = await _run_quality_check(files, normalized_mode)

    # Update dashboard state
    dashboard_state.update_with_result(result, normalized_mode)

    return QualityCheckResponse(**result)


async def _run_quality_check(files: list[str], mode: str) -> dict[str, Any]:
    """Run quality check using the actual QualityEngine."""
    import time as time_module

    try:
        from autopr.actions.quality_engine.engine import QualityEngine
        from autopr.actions.quality_engine.models import QualityInputs

        start_time = time_module.time()

        engine = QualityEngine()
        inputs = QualityInputs(
            mode=QualityMode(mode),
            files=files,
            enable_ai_agents=(mode == "ai_enhanced"),
        )

        result = await asyncio.to_thread(engine.run, inputs)
        processing_time = time_module.time() - start_time

        return {
            "success": True,
            "total_issues_found": getattr(result, 'total_issues', 0),
            "processing_time": processing_time,
            "mode": mode,
            "files_checked": len(files),
            "issues_by_tool": getattr(result, 'issues_by_tool', {}),
            "details": getattr(result, 'details', None),
            "simulated": False,
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
            "issues_by_tool": {},
            "simulated": False,
        }


async def _simulate_quality_check(files: list[str], mode: str) -> dict[str, Any]:
    """Simulate a quality check result (fallback when engine unavailable).

    Note: Uses standard random for demo/simulation data only - not for security.
    """
    import random  # noqa: S311 - not used for security, just simulation data

    await asyncio.sleep(0.1)
    processing_time = random.uniform(1.0, 5.0)  # noqa: S311
    total_issues = random.randint(0, 20)  # noqa: S311

    return {
        "success": True,
        "total_issues_found": total_issues,
        "processing_time": processing_time,
        "mode": mode,
        "files_checked": len(files),
        "issues_by_tool": {
            "ruff": random.randint(0, 5),  # noqa: S311
            "mypy": random.randint(0, 3),  # noqa: S311
            "bandit": random.randint(0, 2),  # noqa: S311
        },
        "simulated": True,
    }


@router.get(
    "/api/config",
    response_model=ConfigResponse,
    summary="Get Configuration",
    description="Returns current dashboard configuration settings. Uses storage backend with file system fallback.",
)
async def api_get_config(_: str | None = Depends(verify_api_key)) -> ConfigResponse:
    """Get current configuration from storage backend."""
    config_data = dashboard_state.get_config()
    return ConfigResponse(**config_data)


@router.post(
    "/api/config",
    response_model=SuccessResponse,
    summary="Save Configuration",
    description="Save dashboard configuration settings to storage backend.",
)
async def api_save_config(
    config: ConfigRequest,
    _: str | None = Depends(verify_api_key),
) -> SuccessResponse:
    """Save configuration to storage backend."""
    try:
        dashboard_state.set_config(config.model_dump())
        return SuccessResponse(success=True)
    except Exception as e:
        logger.exception("Failed to save config")
        raise HTTPException(status_code=500, detail="Failed to save config") from e


# =============================================================================
# Comment Filtering Endpoints
# =============================================================================

class CommentFilterSettingsRequest(BaseModel):
    """Request model for comment filter settings."""
    enabled: bool = Field(description="Enable comment filtering")
    auto_add_commenters: bool = Field(description="Automatically add new commenters")
    auto_reply_enabled: bool = Field(description="Enable auto-reply to new commenters")
    auto_reply_message: str = Field(description="Template for auto-reply message")
    whitelist_mode: bool = Field(description="Use whitelist mode (True) or blacklist (False)")


class CommentFilterSettingsResponse(BaseModel):
    """Response model for comment filter settings."""
    enabled: bool
    auto_add_commenters: bool
    auto_reply_enabled: bool
    auto_reply_message: str
    whitelist_mode: bool


class AllowedCommenterRequest(BaseModel):
    """Request model for adding an allowed commenter."""
    github_username: str = Field(description="GitHub username")
    github_user_id: int | None = Field(default=None, description="GitHub user ID")
    notes: str | None = Field(default=None, description="Optional notes")


class AllowedCommenterResponse(BaseModel):
    """Response model for allowed commenter."""
    github_username: str
    github_user_id: int | None
    enabled: bool
    comment_count: int
    last_comment_at: str | None
    created_at: str
    notes: str | None


@router.get(
    "/api/comment-filter/settings",
    response_model=CommentFilterSettingsResponse,
    summary="Get Comment Filter Settings",
    description="Get current comment filtering settings.",
)
async def api_get_comment_filter_settings(
    _: str | None = Depends(verify_api_key),
) -> CommentFilterSettingsResponse:
    """Get comment filter settings."""
    from autopr.database.config import get_db
    from autopr.services.comment_filter import CommentFilterService
    
    try:
        db = next(get_db())
        try:
            service = CommentFilterService(db)
            settings = await service.get_settings()
            
            if settings is None:
                # Return default settings
                return CommentFilterSettingsResponse(
                    enabled=True,
                    auto_add_commenters=False,
                    auto_reply_enabled=True,
                    auto_reply_message="Thank you for your comment! User @{username} has been added to the allowed commenters list.",
                    whitelist_mode=True,
                )
            
            return CommentFilterSettingsResponse(
                enabled=settings.enabled,
                auto_add_commenters=settings.auto_add_commenters,
                auto_reply_enabled=settings.auto_reply_enabled,
                auto_reply_message=settings.auto_reply_message,
                whitelist_mode=settings.whitelist_mode,
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to get comment filter settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {e}")


@router.post(
    "/api/comment-filter/settings",
    response_model=SuccessResponse,
    summary="Update Comment Filter Settings",
    description="Update comment filtering settings.",
)
async def api_update_comment_filter_settings(
    settings: CommentFilterSettingsRequest,
    _: str | None = Depends(verify_api_key),
) -> SuccessResponse:
    """Update comment filter settings."""
    from autopr.database.config import get_db
    from autopr.services.comment_filter import CommentFilterService
    
    try:
        db = next(get_db())
        try:
            service = CommentFilterService(db)
            await service.update_settings(
                enabled=settings.enabled,
                auto_add_commenters=settings.auto_add_commenters,
                auto_reply_enabled=settings.auto_reply_enabled,
                auto_reply_message=settings.auto_reply_message,
                whitelist_mode=settings.whitelist_mode,
            )
            return SuccessResponse(success=True)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to update comment filter settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {e}")


@router.get(
    "/api/comment-filter/commenters",
    response_model=list[AllowedCommenterResponse],
    summary="List Allowed Commenters",
    description="Get list of allowed commenters with pagination.",
)
async def api_list_commenters(
    enabled_only: bool = Query(default=True, description="Only show enabled commenters"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    _: str | None = Depends(verify_api_key),
) -> list[AllowedCommenterResponse]:
    """List allowed commenters."""
    from autopr.database.config import get_db
    from autopr.services.comment_filter import CommentFilterService
    
    try:
        db = next(get_db())
        try:
            service = CommentFilterService(db)
            commenters = await service.list_commenters(
                enabled_only=enabled_only,
                limit=limit,
                offset=offset,
            )
            
            return [
                AllowedCommenterResponse(
                    github_username=c.github_username,
                    github_user_id=c.github_user_id,
                    enabled=c.enabled,
                    comment_count=c.comment_count,
                    last_comment_at=c.last_comment_at.isoformat() if c.last_comment_at else None,
                    created_at=c.created_at.isoformat(),
                    notes=c.notes,
                )
                for c in commenters
            ]
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to list commenters: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list commenters: {e}")


@router.post(
    "/api/comment-filter/commenters",
    response_model=SuccessResponse,
    summary="Add Allowed Commenter",
    description="Add a user to the allowed commenters list.",
)
async def api_add_commenter(
    commenter: AllowedCommenterRequest,
    _: str | None = Depends(verify_api_key),
) -> SuccessResponse:
    """Add an allowed commenter."""
    from autopr.database.config import get_db
    from autopr.services.comment_filter import CommentFilterService
    
    try:
        db = next(get_db())
        try:
            service = CommentFilterService(db)
            await service.add_commenter(
                github_username=commenter.github_username,
                github_user_id=commenter.github_user_id,
                added_by="dashboard",
                notes=commenter.notes,
            )
            return SuccessResponse(success=True)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to add commenter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add commenter: {e}")


@router.delete(
    "/api/comment-filter/commenters/{username}",
    response_model=SuccessResponse,
    summary="Remove Allowed Commenter",
    description="Remove a user from the allowed commenters list.",
)
async def api_remove_commenter(
    username: str,
    _: str | None = Depends(verify_api_key),
) -> SuccessResponse:
    """Remove an allowed commenter."""
    from autopr.database.config import get_db
    from autopr.services.comment_filter import CommentFilterService
    
    try:
        db = next(get_db())
        try:
            service = CommentFilterService(db)
            success = await service.remove_commenter(username)
            if not success:
                raise HTTPException(status_code=404, detail=f"Commenter not found: {username}")
            return SuccessResponse(success=True)
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove commenter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove commenter: {e}")


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "router",
    "dashboard_state",
    "DashboardState",
    "RateLimiter",
    "StatusResponse",
    "MetricsResponse",
    "ActivityRecord",
    "QualityCheckRequest",
    "QualityCheckResponse",
    "ConfigRequest",
    "ConfigResponse",
    "SuccessResponse",
    "__version__",
]
