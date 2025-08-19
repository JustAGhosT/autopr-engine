#!/usr/bin/env python3
"""Utility to find Markdown files in a directory tree."""

import argparse
from collections.abc import Callable
from pathlib import Path


# Default file extensions to consider as Markdown
DEFAULT_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd", ".mkdn"}


def find_markdown_files(
    root_dir: str,
    *,
    exclude_dirs: set[str] | None = None,
    exclude_files: set[str] | None = None,
    extensions: set[str] | None = None,
    file_filter: Callable[[Path], bool] | None = None,
    relative_to: str | None = None,
) -> list[Path]:
    """Find all markdown files in the given directory and its subdirectories.

    Args:
        root_dir: Root directory to search in
        exclude_dirs: Set of directory names to exclude (e.g., {'node_modules', '.git'})
        exclude_files: Set of file patterns to exclude (supports glob patterns)
        extensions: Set of file extensions to include (default: {'.md', '.markdown', ...})
        file_filter: Optional filter function that takes a Path and returns True to include it
        relative_to: If provided, return paths relative to this directory

    Returns:
        List of Path objects for matching markdown files
    """
    root_path = Path(root_dir).resolve()
    if not root_path.exists() or not root_path.is_dir():
        msg = f"Directory does not exist: {root_dir}"
        raise ValueError(msg)

    if extensions is None:
        extensions = DEFAULT_EXTENSIONS
    else:
        # Ensure extensions start with a dot
        extensions = {ext if ext.startswith(".") else f".{ext}" for ext in extensions}

    if exclude_dirs is None:
        exclude_dirs = set()

    if exclude_files is None:
        exclude_files = set()

    markdown_files = []

    for item in root_path.rglob("*"):
        # Skip excluded directories
        if any(part in exclude_dirs for part in item.parts):
            continue

        # Only process files
        if not item.is_file():
            continue

        # Check file extension
        if item.suffix.lower() not in extensions:
            continue

        # Check against exclude patterns
        if any(item.match(pattern) for pattern in exclude_files):
            continue

        # Apply custom filter if provided
        if file_filter is not None and not file_filter(item):
            continue

        # Make path relative if requested
        if relative_to is not None:
            try:
                item = item.relative_to(relative_to)
            except ValueError:
                # File is not under the relative_to directory
                continue

        markdown_files.append(item)

    return sorted(markdown_files)


def main():
    """Command-line interface for finding markdown files."""
    parser = argparse.ArgumentParser(
        description="Find Markdown files in a directory tree."
    )
    parser.add_argument(
        "root_dir",
        nargs="?",
        default=".",
        help="Root directory to search (default: current directory)",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=None,
        help=f"File extensions to include (default: {DEFAULT_EXTENSIONS})",
    )
    parser.add_argument(
        "--exclude-dirs",
        nargs="+",
        default=[".git", "node_modules", "__pycache__"],
        help="Directories to exclude (default: .git, node_modules, __pycache__)",
    )
    parser.add_argument(
        "--exclude-files",
        nargs="+",
        default=[],
        help="File patterns to exclude (supports glob patterns)",
    )
    parser.add_argument(
        "--relative",
        action="store_true",
        help="Show paths relative to the current directory",
    )

    args = parser.parse_args()

    try:
        files = find_markdown_files(
            args.root_dir,
            exclude_dirs=set(args.exclude_dirs) if args.exclude_dirs else None,
            exclude_files=set(args.exclude_files) if args.exclude_files else None,
            extensions=set(args.extensions) if args.extensions else None,
            relative_to=Path.cwd() if args.relative else None,
        )

        Path(args.root_dir).resolve()

        if not files:
            return 0

        for _file in files:
            pass

        return 0

    except Exception:
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
