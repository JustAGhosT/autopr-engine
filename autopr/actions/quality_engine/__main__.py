"""
Command-line interface for the Quality Engine.
"""

import argparse
import asyncio
import glob
import json
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
    )

    # Get the engine from the DI container
    engine = get_engine()

    # Run the engine and output results
    try:
        result = asyncio.run(engine.run(inputs))
        print(json.dumps(result.model_dump(), indent=2))
        # Exit with success code if no issues, otherwise error
        sys.exit(0 if result.success else 1)
    except KeyboardInterrupt:
        print("Operation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"Error running quality engine: {e!s}")
        sys.exit(1)


if __name__ == "__main__":
    main()
