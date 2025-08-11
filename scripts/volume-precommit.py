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


def main(argv: list[str]) -> int:
    files = argv[:]
    volume = _get_volume()
    print(f"Detected volume: {volume}")

    # Group files by type
    py_files = _select_files_by_ext(files, [".py"])
    if volume < 300:
        # Skip test files at low volumes
        py_files = [f for f in py_files if not _is_test_file(f)]
    text_files = _select_files_by_ext(
        files, [".json", ".yml", ".yaml", ".md", ".markdown"]
    )  # prettier

    rc = 0

    # Tier 1: fast formatters/linters
    if py_files:
        # Ruff (use 'check' subcommand for modern CLI)
        ruff_rc = 0
        if importlib.util.find_spec("ruff") is not None:
            ruff_rc = _run([sys.executable, "-m", "ruff", "check", "--fix", *py_files])
        elif shutil.which("ruff"):
            ruff_rc = _run([shutil.which("ruff"), "check", "--fix", *py_files])  # type: ignore[arg-type]
        else:
            print("ruff not installed; skipping.")

        # At low volumes, don't block on remaining ruff violations
        if volume >= 300:
            rc |= ruff_rc
        elif ruff_rc != 0:
            print("Ruff found violations; ignoring exit code at low volume < 300.")

        # Black
        if importlib.util.find_spec("black") is not None:
            rc |= _run([sys.executable, "-m", "black", "-l", "100", *py_files])
        elif shutil.which("black"):
            rc |= _run([shutil.which("black"), "-l", "100", *py_files])  # type: ignore[arg-type]
        else:
            print("black not installed; skipping.")

        # isort
        if importlib.util.find_spec("isort") is not None:
            rc |= _run([sys.executable, "-m", "isort", "--profile", "black", *py_files])
        elif shutil.which("isort"):
            rc |= _run([shutil.which("isort"), "--profile", "black", *py_files])  # type: ignore[arg-type]
        else:
            print("isort not installed; skipping.")

    # Prettier if available
    if text_files and os.getenv("PRECOMMIT_DISABLE_PRETTIER", "0") not in {"1", "true", "True"}:
        prettier = shutil.which("prettier") or shutil.which("npx")
        if prettier:
            if prettier.endswith("npx"):
                rc |= _run([prettier, "prettier", "--write", *text_files])
            else:
                rc |= _run([prettier, "--write", *text_files])
        else:
            print("Prettier not found; skipping.")

    # Tier 2: security + typing
    if 300 <= volume < 600:
        # Bandit (non-blocking)
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
        # Mypy (lenient)
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

    # Tier 3: comprehensive quality engine
    if volume >= 600:
        # Use comprehensive mode, stricter; pass filenames if any
        qe_cmd = [sys.executable, "-m", "autopr.actions.quality_engine", "--mode", "comprehensive"]
        if files:
            qe_cmd.extend(["--files", *files])
        rc |= _run(qe_cmd)

    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
