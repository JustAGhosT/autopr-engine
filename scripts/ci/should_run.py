#!/usr/bin/env python
"""
Universal CI gate based on volume.

Usage examples (GitHub Actions steps):

  - name: Decide if typecheck should run (>=300)
    run: python scripts/ci/should_run.py --min-volume 300 --context pr

  - name: Run typecheck
    if: ${{ success() }}
    run: python -m mypy autopr

Exit codes:
  0  -> run the job
  78 -> skip the job (commonly interpreted as "no-op"/skipped)
"""

from __future__ import annotations

import argparse
import os
import sys


def detect_volume(context: str | None) -> int:
    # Priority: explicit override for CI/pre-commit/test
    for key in ("AUTOPR_PRECOMMIT_VOLUME", "AUTOPR_TEST_VOLUME_LEVEL"):
        val = os.getenv(key)
        if val:
            try:
                return max(0, min(1000, int(val)))
            except Exception:
                pass

    # Context-specific defaults
    if context:
        ctx = context.lower()
        env_key = {
            "pr": "AUTOPR_VOLUME_PR",
            "dev": "AUTOPR_VOLUME_DEV",
            "checkin": "AUTOPR_VOLUME_CHECKIN",
        }.get(ctx)
        if env_key:
            val = os.getenv(env_key)
            if val:
                try:
                    return max(0, min(1000, int(val)))
                except Exception:
                    pass

    # Any of the known defaults
    for key in ("AUTOPR_VOLUME_PR", "AUTOPR_VOLUME_DEV", "AUTOPR_VOLUME_CHECKIN"):
        val = os.getenv(key)
        if val:
            try:
                return max(0, min(1000, int(val)))
            except Exception:
                pass

    # Fallback
    return 500


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Decide whether a CI job should run based on volume."
    )
    parser.add_argument(
        "--min-volume", type=int, required=True, help="Minimum volume required to run (0-1000)"
    )
    parser.add_argument(
        "--context",
        choices=["pr", "dev", "checkin"],
        default=None,
        help="Optional context to select context-specific default volume",
    )
    parser.add_argument("--verbose", action="store_true", help="Print detected values")
    args = parser.parse_args(argv)

    min_vol = max(0, min(1000, int(args.min_volume)))
    current = detect_volume(args.context)

    if args.verbose:
        print(f"Min volume required: {min_vol}")
        print(f"Detected volume:     {current}")
        if args.context:
            print(f"Context:             {args.context}")

    if current >= min_vol:
        if args.verbose:
            print("Decision: RUN (exit 0)")
        return 0

    if args.verbose:
        print("Decision: SKIP (exit 78)")
    # 78 is conventionally used as a neutral/skip code in some CIs; safe non-zero skip
    return 78


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
