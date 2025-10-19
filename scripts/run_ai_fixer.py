#!/usr/bin/env python3
"""
Simple CLI script to run the AI Linting Fixer
"""

import argparse
import os
from pathlib import Path
import sys


# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not available, try to load .env manually
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from autopr.actions.ai_linting_fixer.main import ai_linting_fixer
from autopr.actions.ai_linting_fixer.models import AILintingFixerInputs


async def main():
    parser = argparse.ArgumentParser(description="AI Linting Fixer CLI")
    parser.add_argument("--target-path", default=".", help="Target path to fix")
    parser.add_argument("--fix-types", help="Comma-separated list of fix types")
    parser.add_argument(
        "--max-fixes-per-run", type=int, default=50, help="Maximum fixes per run"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--provider", default="azure_openai", help="LLM provider")
    parser.add_argument("--model", default="gpt-35-turbo", help="LLM model")

    args = parser.parse_args()

    # Build input kwargs dynamically
    kwargs = {
        "target_path": args.target_path,
        "max_fixes_per_run": args.max_fixes_per_run,
        "dry_run": args.dry_run,
        "provider": args.provider,
        "model": args.model,
        "max_workers": 2,
        "use_specialized_agents": True,
        "create_backups": True,
        "quiet": not args.verbose,
        "verbose_metrics": args.verbose,
    }

    # Only include fix_types if provided
    if args.fix_types:
        kwargs["fix_types"] = [ft.strip() for ft in args.fix_types.split(",")]

    # Create inputs
    inputs = AILintingFixerInputs(**kwargs)

    # Run the fixer

    try:
        result = await ai_linting_fixer(inputs)

        if result.files_modified:
            for _file in result.files_modified:
                pass

        if result.errors:
            for _error in result.errors:
                pass

        return 0 if result.success else 1

    except Exception:
        return 1


if __name__ == "__main__":
    import asyncio

    sys.exit(asyncio.run(main()))
