#!/usr/bin/env python3
"""
Simple CLI script to run the AI Linting Fixer
"""

import argparse
from pathlib import Path
import sys


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
    print(f"Running AI Linting Fixer on {args.target_path}")
    print(f"Fix types: {kwargs.get('fix_types', 'all')}")
    print(f"Max fixes per run: {args.max_fixes_per_run}")
    print(f"Verbose: {args.verbose}")
    print(f"Dry run: {args.dry_run}")
    print("-" * 50)

    try:
        result = await ai_linting_fixer(inputs)

        print("\n" + "=" * 50)
        print("RESULTS SUMMARY")
        print("=" * 50)
        print(f"Success: {result.success}")
        print(f"Total issues found: {result.total_issues_found}")
        print(f"Issues fixed: {result.issues_fixed}")
        print(f"Files modified: {len(result.files_modified)}")

        if result.files_modified:
            print("\nModified files:")
            for file in result.files_modified:
                print(f"  - {file}")

        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")

        return 0 if result.success else 1

    except Exception as e:
        print(f"Error running AI linting fixer: {e}")
        return 1


if __name__ == "__main__":
    import asyncio

    sys.exit(asyncio.run(main()))
