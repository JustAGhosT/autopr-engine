#!/usr/bin/env python
"""
Volume-aware pre-commit wrapper.

Decides which tools to run based on current volume level.

Priority of volume sources (first hit wins):
- AUTOPR_PRECOMMIT_VOLUME
- AUTOPR_TEST_VOLUME_LEVEL
- AUTOPR_VOLUME_PR / AUTOPR_VOLUME_DEV / AUTOPR_VOLUME_CHECKIN (any present)
- Fallback to 500

Tool tiers:
- volume < 300: ruff (fix), black, isort, optional prettier (if available)
- 300 <= volume < 600: above + bandit (exit-zero), mypy (lenient)
- volume >= 600: above + quality engine (comprehensive, stricter)
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    return subprocess.call(cmd)


def _run_with_timeout(cmd: list[str], timeout_seconds: int) -> tuple[int, str, str]:
    """Run a command with a timeout; return (rc, stdout, stderr)."""
    print("+", " ".join(cmd), f"(timeout={timeout_seconds}s)")
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=max(1, int(timeout_seconds)),
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", e.stderr or ""


def _select_files_by_ext(files: list[str], exts: list[str]) -> list[str]:
    if not files:
        return []
    extensions = tuple(exts)
    return [f for f in files if f.lower().endswith(extensions)]


def _is_test_file(path_str: str) -> bool:
    p = Path(path_str)
    name = p.name.lower()
    parts = [part.lower() for part in p.parts]
    if "tests" in parts:
        return True
    if name.startswith("test_") or name.endswith("_test.py") or name.endswith(".test.py"):
        return True
    return False


def _get_volume() -> int:
    for key in ("AUTOPR_PRECOMMIT_VOLUME", "AUTOPR_TEST_VOLUME_LEVEL"):
        val = os.getenv(key)
        if val:
            try:
                return max(0, min(1000, int(val)))
            except Exception:
                pass
    for key in ("AUTOPR_VOLUME_PR", "AUTOPR_VOLUME_DEV", "AUTOPR_VOLUME_CHECKIN"):
        val = os.getenv(key)
        if val:
            try:
                return max(0, min(1000, int(val)))
            except Exception:
                pass
    return 500


def _get_unstaged_changes() -> set[str]:
    try:
        rc, out, _ = _run_with_timeout(["git", "diff", "--name-only"], timeout_seconds=5)
        if rc == 0 and out:
            return {line.strip() for line in out.splitlines() if line.strip()}
    except Exception:
        pass
    return set()


def _run_ruff_black_isort(py_files: list[str], volume: int, apply_fixes: bool) -> int:
    """Run Ruff (fix), Black, and isort. Respect volume for Ruff blocking behavior."""
    rc = 0
    if not py_files:
        return rc
    # Ruff
    ruff_rc = 0
    if importlib.util.find_spec("ruff") is not None:
        ruff_cmd = [sys.executable, "-m", "ruff", "check"]
        if apply_fixes:
            ruff_cmd.append("--fix")
        ruff_rc = _run([*ruff_cmd, *py_files])
    elif shutil.which("ruff"):
        ruff_cmd = [shutil.which("ruff"), "check"]  # type: ignore[arg-type]
        if apply_fixes:
            ruff_cmd.append("--fix")
        ruff_rc = _run([*ruff_cmd, *py_files])  # type: ignore[arg-type]
    else:
        print("ruff not installed; skipping.")
    if volume >= 300:
        rc |= ruff_rc
    elif ruff_rc != 0:
        print("Ruff found violations; ignoring exit code at low volume < 300.")
    # Black
    if importlib.util.find_spec("black") is not None:
        black_cmd = [sys.executable, "-m", "black", "-l", "100"]
        if not apply_fixes:
            black_cmd.insert(black_cmd.index("-l"), "--check")
        rc |= _run([*black_cmd, *py_files])
    elif shutil.which("black"):
        black_cmd = [shutil.which("black"), "-l", "100"]  # type: ignore[arg-type]
        if not apply_fixes:
            black_cmd.insert(1, "--check")
        rc |= _run([*black_cmd, *py_files])  # type: ignore[arg-type]
    else:
        print("black not installed; skipping.")
    # isort
    if importlib.util.find_spec("isort") is not None:
        isort_cmd = [sys.executable, "-m", "isort", "--profile", "black"]
        if not apply_fixes:
            isort_cmd.append("--check-only")
        rc |= _run([*isort_cmd, *py_files])
    elif shutil.which("isort"):
        isort_cmd = [shutil.which("isort"), "--profile", "black"]  # type: ignore[arg-type]
        if not apply_fixes:
            isort_cmd.append("--check-only")
        rc |= _run([*isort_cmd, *py_files])  # type: ignore[arg-type]
    else:
        print("isort not installed; skipping.")
    return rc


def _run_prettier(text_files: list[str]) -> int:
    """Run Prettier on text files if available and not disabled."""
    if not text_files or os.getenv("PRECOMMIT_DISABLE_PRETTIER", "0") in {"1", "true", "True"}:
        return 0
    prettier = shutil.which("prettier") or shutil.which("npx")
    if prettier:
        if prettier.endswith("npx"):
            return _run([prettier, "prettier", "--write", *text_files])
        return _run([prettier, "--write", *text_files])
    print("Prettier not found; skipping.")
    return 0


def _run_security_and_typing(py_files: list[str]) -> int:
    """Run Bandit (non-blocking) and Mypy (lenient)."""
    rc = 0
    rc |= _run(
        [
            sys.executable,
            "-m",
            "bandit",
            "-r",
            ".",
            "-c",
            ".bandit",
            "--exit-zero",
            "--severity-level=medium",
        ]
    )
    targets = py_files if py_files else ["autopr"]
    rc |= _run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--ignore-missing-imports",
            "--show-error-codes",
            "--no-strict-optional",
            *targets,
        ]
    )
    return rc


def _persist_ruff_findings(py_files: list[str]) -> int:
    """Persist Ruff findings to DB using the queue manager (non-blocking). Returns queued count."""
    if not py_files:
        return 0
    try:
        _rc, out_json, _err = _run_with_timeout(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--output-format",
                "json",
                *py_files,
            ],
            timeout_seconds=8,
        )
        if not out_json.strip():
            return 0
        import json

        from autopr.actions.ai_linting_fixer.database import (
            AIInteractionDB,  # type: ignore
        )
        from autopr.actions.ai_linting_fixer.queue_manager import (
            IssueQueueManager,  # type: ignore
        )

        findings = json.loads(out_json)
        issues: list[dict[str, object]] = []
        for f in findings:
            loc = f.get("location") or {}
            issues.append(
                {
                    "file_path": f.get("filename", ""),
                    "line_number": int(loc.get("row", 0) or 0),
                    "column_number": int(loc.get("column", 0) or 0),
                    "error_code": str(f.get("code", "RUFF")),
                    "message": str(f.get("message", ""))[:500],
                    "priority": 5,
                    "line_content": "",
                }
            )
        if not issues:
            return 0
        db_path = os.getenv("AUTOPR_DB_PATH", ".autopr/ai_interactions.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        db = AIInteractionDB(db_path=db_path)
        q = IssueQueueManager(db)
        session_id = os.getenv("GITHUB_RUN_ID") or os.getenv("CI") or "local"
        limit = int(os.getenv("AUTOPR_PRECOMMIT_QUEUE_LIMIT", "100"))
        queued = q.queue_issues(session_id, issues[: max(1, limit)])
        print(f"Queued {queued} issues to DB (non-blocking), limit={limit}")
        return int(queued)
    except Exception as e:
        print(f"Queueing issues failed (non-blocking): {e}")
        return 0


def _run_quality_engine(files: list[str]) -> int:
    """Run comprehensive quality engine (blocking)."""
    cmd = [sys.executable, "-m", "autopr.actions.quality_engine", "--mode", "comprehensive"]
    if files:
        cmd.extend(["--files", *files])
    return _run(cmd)


def _run_ai_suggestions(py_files: list[str]) -> None:
    """Run AI-enhanced suggestions in non-blocking mode."""
    if os.getenv("AUTOPR_DISABLE_LLM_INIT", "0") in {"1", "true", "True"}:
        print("AI suggest skipped: AUTOPR_DISABLE_LLM_INIT=1")
        return
    ai_timeout = int(os.getenv("AUTOPR_PRECOMMIT_AI_TIMEOUT", "5"))
    ai_provider: str | None = os.getenv("AUTOPR_PRECOMMIT_AI_PROVIDER")
    ai_model: str | None = os.getenv("AUTOPR_PRECOMMIT_AI_MODEL")
    cmd = [
        sys.executable,
        "-m",
        "autopr.actions.quality_engine",
        "--mode",
        "ai_enhanced",
    ]
    if py_files:
        cmd.extend(["--files", *py_files])
    if ai_provider:
        cmd.extend(["--ai-provider", ai_provider])
    if ai_model:
        cmd.extend(["--ai-model", ai_model])
    _rc, out, err = _run_with_timeout(cmd, ai_timeout)
    max_findings = int(os.getenv("AUTOPR_PRECOMMIT_AI_MAX_FINDINGS", "20"))
    if out:
        lines = [ln for ln in out.splitlines() if ln.strip()]
        if max_findings > 0 and len(lines) > max_findings:
            print("AI suggestions (truncated):")
            print("\n".join(lines[:max_findings]))
            print(f"... ({len(lines) - max_findings} more lines)")
        else:
            print(out)
    if err:
        print(err)


def _print_low_volume_note() -> None:
    print(
        "Completed in low-volume mode (<300): non-blocking.\n"
        "Next steps:\n"
        "  - Apply fixes across the repo: pre-commit run volume-precommit --all-files --hook-stage manual\n"
        "  - Increase strictness temporarily (bash): AUTOPR_PRECOMMIT_VOLUME=300 npm run precommit\n"
        "  - Increase strictness temporarily (PowerShell): $env:AUTOPR_PRECOMMIT_VOLUME='300'; npm run precommit\n"
        "  - Make volume persistent: set AUTOPR_VOLUME_DEV=300 (or AUTOPR_VOLUME_CHECKIN/AUTOPR_VOLUME_PR) in your environment\n"
    )


def main(argv: list[str]) -> int:
    files = argv[:]
    volume = _get_volume()
    print(f"Detected volume: {volume}")

    # Group files
    py_files = _select_files_by_ext(files, [".py"])
    if volume < 300:
        py_files = [f for f in py_files if not _is_test_file(f)]
    text_files = _select_files_by_ext(
        files, [".json", ".yml", ".yaml", ".md", ".markdown"]
    )  # prettier

    rc = 0
    # Avoid rollback mishaps: if unstaged changes overlap with target files, run in read-only mode
    unstaged = _get_unstaged_changes()
    overlapping = [f for f in py_files if f in unstaged]
    apply_fixes = True
    if overlapping and os.getenv("AUTOPR_PRECOMMIT_ALLOW_STASH_CONFLICTS", "0") not in {
        "1",
        "true",
        "True",
    }:
        apply_fixes = False
        print(
            "Unstaged changes detected in files being formatted; running in read-only mode.\n"
            "Stage your changes or stash them to allow auto-fixes."
        )

    rc |= _run_ruff_black_isort(py_files, volume, apply_fixes)
    rc |= _run_prettier(text_files)

    if 200 <= volume < 600:
        rc |= _run_security_and_typing(py_files)
        queued = 0
        if os.getenv("AUTOPR_PRECOMMIT_QUEUE_ISSUES", "0") in {"1", "true", "True"}:
            queued = _persist_ruff_findings(py_files)
            # Optionally kick off background fixer immediately (non-blocking)
            if os.getenv("AUTOPR_BG_FIX", "0") in {"1", "true", "True"}:
                _run_with_timeout([sys.executable, "scripts/bg-fix-queue.py"], timeout_seconds=120)

    if volume >= 600:
        rc |= _run_quality_engine(files)

    if volume < 300 and os.getenv("AUTOPR_PRECOMMIT_AI_SUGGEST", "0") in {"1", "true", "True"}:
        _run_ai_suggestions(py_files)

    if volume < 300:
        _print_low_volume_note()
        return 0

    # Final concise summary
    print("Pre-commit summary:")
    print(f"  Volume: {volume}")
    if py_files:
        print(f"  Python files checked: {len(py_files)}")
    if text_files:
        print(f"  Text files formatted: {len(text_files)}")
    if 200 <= volume < 600 and os.getenv("AUTOPR_PRECOMMIT_QUEUE_ISSUES", "0") in {
        "1",
        "true",
        "True",
    }:
        print(f"  Issues persisted to DB: {queued}")
        next_hint = os.getenv("AUTOPR_BG_FIX", "0")
        if next_hint in {"1", "true", "True"}:
            print("  Background fixer: enabled (will process queue).")
        else:
            print("  Background fixer: disabled. Set AUTOPR_BG_FIX=1 to process queue locally now.")
    if rc != 0:
        print(
            "  Result: issues remain. Consider AUTOPR_PRECOMMIT_VOLUME=600 for stricter checks, or run background fixer."
        )
    else:
        print("  Result: clean.")

    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
