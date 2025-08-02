#!/usr/bin/env python3
"""Entry point for the whitespace fixer module."""

try:
    from .fixer import main
except ImportError:
    from fixer import main

if __name__ == "__main__":
    main()
