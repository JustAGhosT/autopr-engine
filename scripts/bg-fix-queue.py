#!/usr/bin/env python
"""
Background worker to process queued linting issues.

Behavior:
- Reads up to AUTOPR_BG_BATCH issues (default 20) from the queue
- Optional allowlist of error codes via AUTOPR_BG_TYPES (e.g., "E302,F401")
- Attempts lightweight fixes using Ruff for allowed codes
- Updates issue status in DB: completed/failed/skipped
- Respects DB path via AUTOPR_DB_PATH (default .autopr/ai_interactions.db)

This worker is safe to run at low volumes to continuously reduce trivial issues.
"""

from __future__ import annotations

from collections import defaultdict
import os
from pathlib import Path
import subprocess
import sys
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Iterable


def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True)
    return proc.returncode, proc.stdout, proc.stderr


def _get_env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _get_env_list(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _volume() -> int:
    for key in (
        "AUTOPR_PRECOMMIT_VOLUME",
        "AUTOPR_TEST_VOLUME_LEVEL",
        "AUTOPR_VOLUME_PR",
        "AUTOPR_VOLUME_DEV",
        "AUTOPR_VOLUME_CHECKIN",
    ):
        val = os.getenv(key)
        if val:
            try:
                return max(0, min(1000, int(val)))
            except Exception:
                continue
    return 500


def _group_issues_by_file_and_code(
    issues: Iterable[dict[str, Any]]
) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = defaultdict(set)
    for issue in issues:
        file_path = str(issue.get("file_path", ""))
        code = str(issue.get("error_code", "")).strip()
        if file_path and code:
            mapping[file_path].add(code)
    return mapping


def _remaining_issues_for_file(file_path: str, codes: list[str]) -> int:
    # Ask Ruff if any selected codes remain in this file
    if not codes:
        return 0
    ruff = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        "--select",
        ",".join(codes),
        file_path,
    ]
    rc, _out, _err = _run(ruff)
    # Non-zero means issues remain
    return 1 if rc != 0 else 0


def main() -> int:
    # Fast import inside function to avoid import cost when listing help
    from autopr.actions.ai_linting_fixer.database import (
        AIInteractionDB,
    )

    # type: ignore[import-not-found]
    from autopr.actions.ai_linting_fixer.queue_manager import (
        IssueQueueManager,
    )

    db_path = os.getenv("AUTOPR_DB_PATH", ".autopr/ai_interactions.db")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    db = AIInteractionDB(db_path=db_path)
    queue = IssueQueueManager(db)

    batch = _get_env_int("AUTOPR_BG_BATCH", 20)
    allowed = _get_env_list("AUTOPR_BG_TYPES")
    worker_id = os.getenv("AUTOPR_BG_WORKER_ID", "local")

    issues = queue.get_next_issues(
        limit=batch, worker_id=worker_id, filter_types=allowed or None
    )
    if not issues:
        return 0

    grouped = _group_issues_by_file_and_code(issues)
    len(issues)
    fixed = 0
    failed = 0
    skipped = 0

    # Decide if autofix is enabled based on env and volume
    vol = _volume()
    auto_fix_enabled = os.getenv("AUTOPR_ENABLE_AUTOFIX", "0") in {"1", "true", "True"}
    try:
        min_vol = int(os.getenv("AUTOPR_AUTOFIX_MIN_VOLUME", "600"))
    except Exception:
        min_vol = 600
    allow_fix = auto_fix_enabled and vol >= min_vol

    for file_path, codes in grouped.items():
        # If not allowed to fix, mark as skipped
        if not allow_fix:
            for issue in issues:
                if str(issue.get("file_path")) == file_path:
                    queue.update_issue_status(
                        int(issue["id"]),
                        "skipped",
                        {"error_message": "autofix disabled or below min volume"},
                    )
                    skipped += 1
            continue

        # Run Ruff fix for the selected codes on this file
        ruff_cmd = [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--fix",
            "--select",
            ",".join(sorted(codes)),
            file_path,
        ]
        _rc, _out, _err = _run(ruff_cmd)

        # Verify if issues remain for these codes
        remain = _remaining_issues_for_file(file_path, list(codes))
        success = remain == 0

        # Update all issues for this file
        for issue in issues:
            if str(issue.get("file_path")) != file_path:
                continue
            queue.update_issue_status(
                int(issue["id"]),
                "completed" if success else "failed",
                {"fix_successful": bool(success), "confidence_score": 0.0},
            )
            fixed += 1 if success else 0
            failed += 0 if success else 1

    # Non-zero exit if failures occurred
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
