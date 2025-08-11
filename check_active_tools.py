#!/usr/bin/env python3

import argparse
import os
import sys

# Add scripts/volume-control to path
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts", "volume-control"))

def main() -> None:
    """
    Main function to check active tools at a specified volume level.
    
    The volume level can be specified via command line argument (--volume).
    Default volume is 200 if not specified.
    """
    parser = argparse.ArgumentParser(
        description="Check which tools are active at a given volume level.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--volume",
        type=int,
        default=200,
        help="Volume level (0-1000) to check active tools for",
        metavar="VOLUME"
    )
    args = parser.parse_args()

    # Validate volume range
    if not 0 <= args.volume <= 1000:
        print(f"Error: Volume must be between 0 and 1000, got {args.volume}", file=sys.stderr)
        sys.exit(1)

    try:
        from config_loader import VolumeConfigLoader
        loader = VolumeConfigLoader()
        active_tools = loader.get_active_tools(args.volume)

        if not active_tools:
            print(f"No active tools found at volume {args.volume}.")
        else:
            print(f"Active tools at volume {args.volume}:")
            for tool in active_tools:
                print(f"  - {tool}")

    except ImportError as e:
        print(f"Error: Could not import required module: {e}", file=sys.stderr)
        print("Please ensure the volume-control scripts are in the correct location.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error checking active tools: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
