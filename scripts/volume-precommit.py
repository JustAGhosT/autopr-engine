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
- volume <= 300: persist-only (no file modifications). Run Ruff check-only/Black --check, queue findings to DB, exclude tests from scope, skip Prettier.
- 300 < volume < 600: above + bandit (exit-zero), mypy (lenient)
- volume >= 600: above + quality engine (comprehensive, stricter)
"""

from __future__ import annotations

from collections import Counter
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def _run_with_timeout(cmd: list[str], timeout_seconds: int) -> tuple[int, str, str]:
    """Run a command with a timeout; return (rc, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
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
    return bool(name.startswith("test_") or name.endswith(("_test.py", ".test.py")))


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
        rc, out, _ = _run_with_timeout(
            ["git", "diff", "--name-only"], timeout_seconds=5
        )
        if rc == 0 and out:
            return {line.strip() for line in out.splitlines() if line.strip()}
    except Exception:
        pass
    return set()


def _run_ruff_black(py_files: list[str], volume: int, apply_fixes: bool) -> int:
    """Run Ruff (fix) and Black. Respect volume for Ruff blocking behavior; Ruff handles import sorting."""
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
        pass
    if volume >= 300:
        rc |= ruff_rc
    elif ruff_rc != 0:
        pass
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
        pass
    return rc


def _run_prettier(text_files: list[str]) -> int:
    """Run Prettier on text files if available and not disabled."""
    if not text_files or os.getenv("PRECOMMIT_DISABLE_PRETTIER", "0") in {
        "1",
        "true",
        "True",
    }:
        return 0
    prettier = shutil.which("prettier") or shutil.which("npx")
    if prettier:
        if prettier.endswith("npx"):
            return _run([prettier, "prettier", "--write", *text_files])
        return _run([prettier, "--write", *text_files])
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
        return int(queued)
    except Exception:
        return 0


def _collect_ruff_findings(targets: list[str]) -> list[dict]:
    """Run ruff in JSON mode and return parsed findings list."""
    try:
        # Prefer python -m ruff if available; otherwise fall back to CLI
        cmd: list[str]
        if importlib.util.find_spec("ruff") is not None:
            cmd = [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--output-format",
                "json",
                *targets,
            ]
        elif shutil.which("ruff"):
            ruff_bin = shutil.which("ruff")  # type: ignore[assignment]
            cmd = [str(ruff_bin), "check", "--output-format", "json", *targets]
        else:
            return []
        _rc, out_json, _err = _run_with_timeout(cmd, timeout_seconds=25)
        if not out_json.strip():
            return []
        import json

        return list(json.loads(out_json))
    except Exception:
        return []


def _persist_findings(findings: list[dict]) -> int:
    """Persist pre-collected ruff findings to DB. Returns queued count."""
    if not findings:
        return 0
    try:
        from autopr.actions.ai_linting_fixer.database import (
            AIInteractionDB,  # type: ignore
        )
        from autopr.actions.ai_linting_fixer.queue_manager import (
            IssueQueueManager,  # type: ignore
        )

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
        return int(queued)
    except Exception:
        return 0


def _run_quality_engine(files: list[str]) -> int:
    """Run comprehensive quality engine (blocking)."""
    cmd = [
        sys.executable,
        "-m",
        "autopr.actions.quality_engine",
        "--mode",
        "comprehensive",
    ]
    if files:
        cmd.extend(["--files", *files])
    return _run(cmd)


def _run_ai_suggestions(py_files: list[str]) -> None:
    """Run AI-enhanced suggestions in non-blocking mode."""
    if os.getenv("AUTOPR_DISABLE_LLM_INIT", "0") in {"1", "true", "True"}:
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
            pass
        else:
            pass
    if err:
        pass


def _print_low_volume_note() -> None:
    pass


def main(argv: list[str]) -> int:
    files = argv[:]
    volume = _get_volume()

    # Group files
    py_files = _select_files_by_ext(files, [".py"])
    # Exclude helper scripts from lint scope to avoid noisy utility output
    py_files = [f for f in py_files if not (f.startswith(("scripts/", "scripts\\")))]
    if volume <= 300:
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

    # Persist-only at low volumes: never modify files, just collect/persist and show feedback
    if volume <= 300:
        apply_fixes = False
    rc |= _run_ruff_black(py_files, volume, apply_fixes)
    if volume > 300:
        rc |= _run_prettier(text_files)

    # For summary details
    rule_counts: Counter[str] = Counter()
    file_counts: Counter[str] = Counter()
    repo_scope_env = os.getenv("AUTOPR_REPO_SCOPE", "0") in {"1", "true", "True"}
    repo_scope = repo_scope_env

    if volume <= 300:
        # Persist-only path: always queue for repository scope for meaningful progress
        if os.getenv("AUTOPR_PRECOMMIT_QUEUE_ISSUES", "1") in {"1", "true", "True"}:
            queue_targets = ["autopr"]
            repo_scope = True
            findings = _collect_ruff_findings(queue_targets)
            for f in findings:
                code = str(f.get("code", "RUFF"))
                filename = str(f.get("filename", ""))
                if code:
                    rule_counts[code] += 1
                if filename:
                    file_counts[filename] += 1
            _persist_findings(findings)
            if os.getenv("AUTOPR_BG_FIX", "0") in {"1", "true", "True"}:
                _run_with_timeout(
                    [sys.executable, "scripts/bg-fix-queue.py"], timeout_seconds=120
                )
    elif 300 < volume < 600:
        rc |= _run_security_and_typing(py_files)
        if os.getenv("AUTOPR_PRECOMMIT_QUEUE_ISSUES", "1") in {"1", "true", "True"}:
            # If no explicit files passed, queue for repository scope
            queue_targets = ["autopr"] if repo_scope_env or not py_files else py_files
            repo_scope = repo_scope or (not bool(py_files))
            findings = _collect_ruff_findings(queue_targets)
            for f in findings:
                code = str(f.get("code", "RUFF"))
                filename = str(f.get("filename", ""))
                if code:
                    rule_counts[code] += 1
                if filename:
                    file_counts[filename] += 1
            _persist_findings(findings)
            if os.getenv("AUTOPR_BG_FIX", "0") in {"1", "true", "True"}:
                _run_with_timeout(
                    [sys.executable, "scripts/bg-fix-queue.py"], timeout_seconds=120
                )

    if volume >= 600:
        rc |= _run_quality_engine(files)

    if volume < 300 and os.getenv("AUTOPR_PRECOMMIT_AI_SUGGEST", "0") in {
        "1",
        "true",
        "True",
    }:
        _run_ai_suggestions(py_files)

    if volume <= 300:
        # Concise low-volume summary with top rules/files and next-step hint
        if os.getenv("AUTOPR_PRECOMMIT_QUEUE_ISSUES", "1") in {"1", "true", "True"}:
            if rule_counts:
                ", ".join(
                    [f"{code}:{count}" for code, count in rule_counts.most_common(5)]
                )
            if file_counts:
                from pathlib import Path as _P

                ", ".join(
                    [
                        f"{_P(fp).as_posix()}:{cnt}"
                        for fp, cnt in file_counts.most_common(5)
                    ]
                )
        _print_low_volume_note()
        return 0

    # Final concise summary
    (
        "all files (repo)"
        if repo_scope
        else (f"{len(py_files)} Python files" if py_files else "no python files")
    )
    if text_files:
        pass
    if 200 <= volume < 600 and os.getenv("AUTOPR_PRECOMMIT_QUEUE_ISSUES", "1") in {
        "1",
        "true",
        "True",
    }:
        if rule_counts:
            ", ".join([f"{code}:{count}" for code, count in rule_counts.most_common(5)])
        if file_counts:
            from pathlib import Path as _P

            ", ".join(
                [f"{_P(fp).as_posix()}:{cnt}" for fp, cnt in file_counts.most_common(5)]
            )
        next_hint = os.getenv("AUTOPR_BG_FIX", "0")
        if next_hint in {"1", "true", "True"}:
            pass
        else:
            pass
    if rc != 0:
        pass
    else:
        pass

    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
