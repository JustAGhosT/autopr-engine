#!/usr/bin/env python3
"""
Comprehensive Whitespace and Line Ending Fixer
Automatically fixes:
- Trailing whitespace on all lines
- Mixed line endings (normalize to LF or CRLF)
- Missing final newline
- Multiple consecutive blank lines
- Tabs vs spaces (configurable)
"""

import argparse
from pathlib import Path
import re


class WhitespaceFixer:
    """Fixes whitespace and line ending issues in files."""

    # Common file extensions to process
    DEFAULT_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".html",
        ".htm",
        ".xml",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".md",
        ".txt",
        ".rst",
        ".sh",
        ".bat",
        ".ps1",
        ".cmd",
        ".sql",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".java",
        ".cs",
        ".php",
        ".rb",
        ".go",
        ".rs",
        ".kt",
        ".swift",
        ".dart",
        ".vue",
        ".svelte",
        ".dockerfile",
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
    }

    # Binary file extensions to skip
    BINARY_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".ico",
        ".tiff",
        ".webp",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".mp3",
        ".mp4",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".app",
        ".dmg",
        ".msi",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".eot",
    }

    def __init__(
        self,
        line_ending: str = "lf",
        max_consecutive_blank_lines: int = 2,
        tab_size: int = 4,
        convert_tabs_to_spaces: bool = False,
        extensions: set[str] | None = None,
    ):
        """
        Initialize the whitespace fixer.

        Args:
            line_ending: 'lf', 'crlf', or 'auto' (detect from file)
            max_consecutive_blank_lines: Maximum consecutive blank lines allowed
            tab_size: Tab size for tab-to-space conversion
            convert_tabs_to_spaces: Whether to convert tabs to spaces
            extensions: File extensions to process (None = use defaults)
        """
        self.line_ending = line_ending
        self.max_consecutive_blank_lines = max_consecutive_blank_lines
        self.tab_size = tab_size
        self.convert_tabs_to_spaces = convert_tabs_to_spaces
        self.extensions = extensions or self.DEFAULT_EXTENSIONS

        # Set line ending character
        if line_ending == "lf":
            self.target_line_ending = "\n"
        elif line_ending == "crlf":
            self.target_line_ending = "\r\n"
        else:  # auto
            self.target_line_ending = None

    def should_process_file(self, file_path: Path) -> bool:
        """Check if a file should be processed."""
        # Skip if file doesn't exist
        if not file_path.exists():
            return False

        # Skip directories
        if file_path.is_dir():
            return False

        # Skip binary files by extension
        if file_path.suffix.lower() in self.BINARY_EXTENSIONS:
            return False

        # Check if extension is in our list (or no extension filtering)
        if self.extensions and file_path.suffix.lower() not in self.extensions:
            # Also check files without extensions but with specific names
            if file_path.name not in {"Dockerfile", "Makefile", "README", "LICENSE", "CHANGELOG"}:
                return False

        # Try to detect if file is binary by reading a small chunk
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
                if b"\x00" in chunk:  # Null bytes indicate binary
                    return False
        except (PermissionError, OSError):
            return False

        return True

    def detect_line_ending(self, content: str) -> str:
        """Detect the most common line ending in content."""
        crlf_count = content.count("\r\n")
        lf_count = content.count("\n") - crlf_count
        cr_count = content.count("\r") - crlf_count

        if crlf_count > lf_count and crlf_count > cr_count:
            return "\r\n"
        if cr_count > lf_count and cr_count > crlf_count:
            return "\r"
        return "\n"

    def fix_content(self, content: str, file_path: Path) -> tuple[str, list[str]]:
        """
        Fix whitespace issues in content.

        Returns:
            Tuple of (fixed_content, list_of_issues_fixed)
        """
        issues_fixed = []
        original_content = content

        # Detect original line ending if using auto mode
        if self.target_line_ending is None:
            detected_ending = self.detect_line_ending(content)
            line_ending = detected_ending
        else:
            line_ending = self.target_line_ending

        # Normalize line endings first
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Split into lines
        lines = content.split("\n")
        fixed_lines = []

        # Track consecutive blank lines
        consecutive_blank = 0

        for i, line in enumerate(lines):
            # Fix trailing whitespace
            if line.rstrip() != line:
                issues_fixed.append(f"Line {i + 1}: Removed trailing whitespace")
            line = line.rstrip()

            # Convert tabs to spaces if requested
            if self.convert_tabs_to_spaces and "\t" in line:
                spaces = " " * self.tab_size
                new_line = line.replace("\t", spaces)
                if new_line != line:
                    issues_fixed.append(f"Line {i + 1}: Converted tabs to spaces")
                line = new_line

            # Handle consecutive blank lines
            if line.strip() == "":
                consecutive_blank += 1
                if consecutive_blank <= self.max_consecutive_blank_lines:
                    fixed_lines.append(line)
                else:
                    issues_fixed.append(f"Line {i + 1}: Removed excessive blank line")
            else:
                consecutive_blank = 0
                fixed_lines.append(line)

        # Ensure file ends with exactly one newline
        while fixed_lines and fixed_lines[-1].strip() == "":
            fixed_lines.pop()

        # Join with target line ending
        fixed_content = line_ending.join(fixed_lines)

        # Add final newline if file is not empty
        if fixed_content and not fixed_content.endswith(("\n", "\r\n")):
            fixed_content += line_ending
            issues_fixed.append("Added missing final newline")

        # Check if line endings were changed
        if self.target_line_ending is not None:
            original_ending = self.detect_line_ending(original_content)
            if original_ending != self.target_line_ending and original_content:
                ending_name = {"\\n": "LF", "\\r\\n": "CRLF", "\\r": "CR"}
                target_name = ending_name.get(
                    repr(self.target_line_ending), self.target_line_ending
                )
                original_name = ending_name.get(repr(original_ending), original_ending)
                issues_fixed.append(
                    f"Normalized line endings from {original_name} to {target_name}"
                )

        return fixed_content, issues_fixed

    def fix_file(self, file_path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
        """
        Fix whitespace issues in a single file.

        Returns:
            Tuple of (was_modified, list_of_issues_fixed)
        """
        if not self.should_process_file(file_path):
            return False, []

        try:
            # Read file content
            with open(file_path, encoding="utf-8", newline="") as f:
                original_content = f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ["latin-1", "cp1252", "iso-8859-1"]:
                try:
                    with open(file_path, encoding=encoding, newline="") as f:
                        original_content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return False, ["Could not decode file with any encoding"]
        except (PermissionError, OSError) as e:
            return False, [f"Could not read file: {e}"]

        # Fix the content
        fixed_content, issues_fixed = self.fix_content(original_content, file_path)

        # Check if content was actually changed
        if fixed_content == original_content:
            return False, []

        # Write fixed content if not dry run
        if not dry_run:
            try:
                with open(file_path, "w", encoding="utf-8", newline="") as f:
                    f.write(fixed_content)
            except (PermissionError, OSError) as e:
                return False, [f"Could not write file: {e}"]

        return True, issues_fixed

    def fix_directory(
        self, directory: Path, dry_run: bool = False, exclude_patterns: list[str] | None = None
    ) -> dict:
        """
        Fix whitespace issues in all files in a directory recursively.

        Returns:
            Dictionary with statistics and results
        """
        exclude_patterns = exclude_patterns or []
        exclude_compiled = [re.compile(pattern) for pattern in exclude_patterns]

        results = {
            "files_processed": 0,
            "files_modified": 0,
            "total_issues": 0,
            "files_with_issues": {},
            "errors": [],
        }

        # Walk through all files
        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue

            # Check exclude patterns
            relative_path = file_path.relative_to(directory)
            if any(pattern.search(str(relative_path)) for pattern in exclude_compiled):
                continue

            # Process file
            was_modified, issues = self.fix_file(file_path, dry_run)
            results["files_processed"] += 1

            if was_modified:
                results["files_modified"] += 1
                results["files_with_issues"][str(relative_path)] = issues
                results["total_issues"] += len(issues)
            elif issues:  # Errors
                results["errors"].extend([f"{relative_path}: {issue}" for issue in issues])

        return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Fix whitespace and line ending issues in files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s .                     # Fix all files in current directory
  %(prog)s file.py file.js       # Fix specific files
  %(prog)s . --dry-run           # Preview changes without applying
  %(prog)s . --line-ending crlf  # Use Windows line endings
  %(prog)s . --convert-tabs      # Convert tabs to spaces
  %(prog)s . --exclude "*.min.js" --exclude "node_modules/*"
        """,
    )

    parser.add_argument("paths", nargs="+", help="Files or directories to process")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be changed without modifying files"
    )
    parser.add_argument(
        "--line-ending",
        choices=["lf", "crlf", "auto"],
        default="lf",
        help="Target line ending (default: lf)",
    )
    parser.add_argument(
        "--max-blank-lines",
        type=int,
        default=2,
        help="Maximum consecutive blank lines (default: 2)",
    )
    parser.add_argument(
        "--tab-size", type=int, default=4, help="Tab size for conversion (default: 4)"
    )
    parser.add_argument("--convert-tabs", action="store_true", help="Convert tabs to spaces")
    parser.add_argument(
        "--extensions", nargs="*", help="File extensions to process (default: common text files)"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Exclude patterns (can be used multiple times)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Set up extensions
    extensions = None
    if args.extensions is not None:
        extensions = {ext if ext.startswith(".") else f".{ext}" for ext in args.extensions}

    # Create fixer
    fixer = WhitespaceFixer(
        line_ending=args.line_ending,
        max_consecutive_blank_lines=args.max_blank_lines,
        tab_size=args.tab_size,
        convert_tabs_to_spaces=args.convert_tabs,
        extensions=extensions,
    )

    # Process each path
    total_files_processed = 0
    total_files_modified = 0
    total_issues = 0

    for path_str in args.paths:
        path = Path(path_str)

        if not path.exists():
            continue

        if path.is_file():
            # Process single file
            was_modified, issues = fixer.fix_file(path, args.dry_run)
            total_files_processed += 1

            if was_modified:
                total_files_modified += 1
                total_issues += len(issues)

                if args.verbose or args.dry_run:
                    for _issue in issues:
                        pass
            elif issues:  # Errors
                for _issue in issues:
                    pass

        elif path.is_dir():
            # Process directory
            results = fixer.fix_directory(path, args.dry_run, args.exclude)
            total_files_processed += results["files_processed"]
            total_files_modified += results["files_modified"]
            total_issues += results["total_issues"]

            if args.verbose or args.dry_run:
                for issues in results["files_with_issues"].values():
                    for _issue in issues:
                        pass

            if results["errors"]:
                for _error in results["errors"]:
                    pass

    # Print summary

    if args.dry_run and total_files_modified > 0:
        pass


if __name__ == "__main__":
    main()
