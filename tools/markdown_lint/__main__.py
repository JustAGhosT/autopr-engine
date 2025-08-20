"""Markdown linter entry point."""

try:
    from tools.markdown_lint.cli import main
except ImportError:
    from cli import main

if __name__ == "__main__":
    main()
