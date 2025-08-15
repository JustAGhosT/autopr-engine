"""
Command-line interface for the Quality Engine.
"""

import argparse
import asyncio
import glob
import sys

from .di import container, get_engine
from .engine import QualityInputs, QualityMode


def main() -> None:
    """Main CLI entry point for the Quality Engine."""
    parser = argparse.ArgumentParser(description="AutoPR Quality Engine")
    parser.add_argument(
        "--mode",
        choices=["fast", "comprehensive", "ai_enhanced", "smart"],
        default="smart",
        help="Quality check mode",
    )
    parser.add_argument("--files", nargs="*", help="Files to check (supports glob patterns)")
    parser.add_argument("--config", default="pyproject.toml", help="Path to configuration file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--ai-provider", help="AI provider to use for AI-enhanced mode")
    parser.add_argument("--ai-model", help="AI model to use for AI-enhanced mode")
    parser.add_argument("--skip-windows-check", action="store_true", help="Skip Windows compatibility warnings and checks")
    parser.add_argument("--continue-on-errors", action="store_true", help="Continue execution even if some tools fail or are not available")
    
    # Auto-fix options
    parser.add_argument("--auto-fix", action="store_true", help="Automatically fix issues using AI")
    parser.add_argument("--fix-types", nargs="+", help="Types of issues to fix (e.g., E501 F401 F841)")
    parser.add_argument("--max-fixes", type=int, default=50, help="Maximum number of fixes to apply")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without making changes")

    args = parser.parse_args()

    # Configure the DI container
    container.config_path.override(args.config)

    # Handle file globs
    all_files = []
    if args.files:
        for pattern in args.files:
            matched_files = glob.glob(pattern, recursive=True)
            all_files.extend(matched_files)

    # Create input object
    inputs = QualityInputs(
        mode=QualityMode(args.mode),
        files=all_files,
        config_path=args.config,
        verbose=args.verbose,
        ai_provider=args.ai_provider,
        ai_model=args.ai_model,
        # Auto-fix parameters
        auto_fix=args.auto_fix,
        fix_types=args.fix_types,
        max_fixes=args.max_fixes,
        dry_run=args.dry_run,
    )

    # Get the engine from the DI container
    engine = get_engine(skip_windows_check=args.skip_windows_check)

    # Run the engine and output results
    try:
        result = asyncio.run(engine.run(inputs))

        # Determine exit code based on arguments and results
        if args.continue_on_errors:
            # Always exit with success if continue-on-errors is specified
            sys.exit(0)
        else:
            # Exit with success code if no issues, otherwise error
            sys.exit(0 if result.success else 1)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
