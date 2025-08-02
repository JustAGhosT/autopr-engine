"""
Command-line interface for the Quality Engine.
"""

import argparse
import sys

from .engine import QualityEngine
from .models import QualityInputs, QualityMode
from .platform_detector import PlatformDetector


def ask_windows_confirmation() -> bool:
    """Ask user for confirmation to continue on Windows."""
    print("\n" + "=" * 60)
    print("WINDOWS DETECTED - QUALITY ENGINE")
    print("=" * 60)
    print("Some quality tools may have limitations on Windows.")
    print("The engine will automatically adapt and use Windows-compatible alternatives.")
    print()

    while True:
        response = input("Continue with Windows-adapted quality analysis? (y/n): ").lower().strip()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' or 'n'.")


def main(args: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Quality Engine CLI")
    parser.add_argument(
        "--mode",
        choices=["fast", "smart", "comprehensive", "ai_enhanced"],
        default="smart",
        help="Quality analysis mode",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Files or directories to analyze",
    )
    parser.add_argument(
        "--ai-provider",
        default="openai",
        help="AI provider for enhanced analysis",
    )
    parser.add_argument(
        "--ai-model",
        default="gpt-4",
        help="AI model for enhanced analysis",
    )
    parser.add_argument(
        "--enable-ai",
        action="store_true",
        help="Enable AI-enhanced analysis",
    )
    parser.add_argument(
        "--config",
        default="pyproject.toml",
        help="Configuration file path",
    )
    parser.add_argument(
        "--skip-windows-check",
        action="store_true",
        help="Skip Windows compatibility check",
    )

    parsed_args = parser.parse_args(args)

    # Platform detection and confirmation
    platform_detector = PlatformDetector()

    if platform_detector.is_windows and not parsed_args.skip_windows_check:
        if not ask_windows_confirmation():
            print("Quality analysis cancelled by user.")
            return 0

    # Create quality engine
    engine = QualityEngine(config_path=parsed_args.config)

    # Create inputs
    inputs = QualityInputs(
        mode=QualityMode(parsed_args.mode),
        files=parsed_args.files,
        ai_provider=parsed_args.ai_provider,
        ai_model=parsed_args.ai_model,
        enable_ai_agents=parsed_args.enable_ai,
    )

    # Run analysis
    try:
        import asyncio

        result = asyncio.run(engine.run(inputs))

        # Print results
        print("\n" + "=" * 60)
        print("QUALITY ANALYSIS RESULTS")
        print("=" * 60)
        print(f"Success: {result.success}")
        print(f"Total Issues Found: {result.total_issues_found}")
        print(f"Files with Issues: {len(set().union(*result.files_by_tool.values()))}")
        print()

        if result.issues_by_tool:
            print("Issues by Tool:")
            for tool, issues in result.issues_by_tool.items():
                print(f"  {tool}: {len(issues)} issues")
        print()

        print("Summary:")
        print(result.summary)

        return 0 if result.success else 1

    except Exception as e:
        print(f"Error running quality analysis: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
