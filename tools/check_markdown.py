from pathlib import Path
import re
import sys


# Configuration
MAX_LINE_LENGTH = 120
REQUIRE_BLANK_LINE_BEFORE_HEADING = True
REQUIRE_BLANK_LINE_AFTER_HEADING = True
ALLOW_MULTIPLE_BLANK_LINES = False

# Patterns
HEADING_PATTERN = re.compile(r"^#{1,6}\s+.+")
CODE_BLOCK_PATTERN = re.compile(r"^```")


class MarkdownLinter:
    """Simple markdown linter for checking common issues."""

    def __init__(self, root_dir: Path):
        """Initialize the linter with root directory."""
        self.root_dir = root_dir
        self.issues = []

    def check_file(self, file_path: Path) -> None:
        """Check a single markdown file for issues."""
        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.issues.append(f"Error reading {file_path}: {e}")
            return

        lines = content.splitlines()

        # Check for common issues
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 120:
                self.issues.append(f"{file_path}:{i}: Line too long ({len(line)} characters)")

            # Check for trailing whitespace
            if line.rstrip() != line:
                self.issues.append(f"{file_path}:{i}: Trailing whitespace")

            # Check for tabs
            if "\t" in line:
                self.issues.append(f"{file_path}:{i}: Use spaces instead of tabs")

    def check_directory(self) -> None:
        """Check all markdown files in the directory."""
        for file_path in self.root_dir.rglob("*.md"):
            self.check_file(file_path)

    def report_issues(self) -> int:
        """Report all issues and return count."""
        if self.issues:
            for _issue in self.issues:
                pass
            return len(self.issues)
        return 0


def main():
    """Main function."""
    root_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    linter = MarkdownLinter(root_dir)
    linter.check_directory()

    issue_count = linter.report_issues()
    sys.exit(issue_count)


if __name__ == "__main__":
    main()
