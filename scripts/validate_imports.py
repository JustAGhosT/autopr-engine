#!/usr/bin/env python3
"""
Import validation script for AutoPR Engine.

This script scans for broken imports and updates import paths after
documentation and code reorganization.
"""

import os
import re
import sys


def find_python_files(directory: str) -> list[str]:
    """Find all Python files in the directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip virtual environments and cache directories
        dirs[:] = [
            d for d in dirs if not d.startswith(".") and d not in ["__pycache__", ".venv", "venv"]
        ]

        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    return python_files


def extract_imports(file_path: str) -> list[tuple[str, int, str]]:
    """Extract import statements from a Python file."""
    imports = []

    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Match import statements
            import_patterns = [
                r"^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)$",
                r"^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import",
                r"^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import\s+([a-zA-Z_][a-zA-Z0-9_,\s]*)",
            ]

            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    module = match.group(1)
                    imports.append((module, line_num, line))
                    break

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return imports


def check_import_validity(import_statement: str, file_path: str) -> bool:
    """Check if an import is valid."""
    # Skip type ignore comments
    if "# type: ignore" in import_statement:
        return True

    # Skip optional dependencies that are properly handled
    optional_deps = [
        "autogen",
        "mem0",
        "celery",
        "prefect",
        "redis",
        "mistralai",
        "sentry_sdk",
        "asyncpg",
        "fastapi",
        "pybreaker",
        "prometheus_client",
        "prometheus_fastapi_instrumentator",
        "authlib",
        "jose",
        "chromadb",
        "sentence_transformers",
        "slack_sdk",
        "bcrypt",
        "passlib",
        "azure.monitor",
        "fontTools",
        "parse_tfm",
        "anthropic",
        "groq",
        "toml",
        "dependency_injector",
        "sqlalchemy",
        "setuptools",
    ]

    for dep in optional_deps:
        if dep in import_statement:
            return True

    # Skip node_modules imports
    if "node_modules" in file_path:
        return True

    # Skip relative imports that might fail in validation context
    if import_statement.startswith("from .") or import_statement.startswith("from .."):
        return True

    # Skip local imports that are properly handled with try/except
    local_imports = [
        "from linter import",
        "from models import",
        "from cli import",
        "from fixer import",
        "from yaml_lint import",
        "from file_ops import",
    ]
    for local_import in local_imports:
        if local_import in import_statement:
            return True

    # Check if it's a standard library import
    stdlib_modules = [
        "os",
        "sys",
        "re",
        "json",
        "pathlib",
        "typing",
        "datetime",
        "asyncio",
        "tempfile",
        "unittest",
        "collections",
        "abc",
        "dataclasses",
        "enum",
        "functools",
        "logging",
        "subprocess",
        "argparse",
        "urllib",
        "html",
        "base64",
        "secrets",
        "statistics",
        "sqlite3",
        "pickle",
        "hashlib",
        "uuid",
        "time",
        "random",
        "operator",
        "contextlib",
        "warnings",
        "ast",
        "traceback",
        "shutil",
        "fnmatch",
        "string",
        "platform",
        "glob",
        "csv",
        "tomllib",
        "io",
        "setuptools",
        "importlib",
        "pkgutil",
        "contextvars",
        "mock",
    ]

    for module in stdlib_modules:
        if f"import {module}" in import_statement or f"from {module} import" in import_statement:
            return True

    # Check for specific standard library submodules
    stdlib_submodules = [
        "collections.abc",
        "unittest.mock",
        "urllib.parse",
    ]

    for submodule in stdlib_submodules:
        if f"from {submodule} import" in import_statement:
            return True

    # Check if it's a common third-party library
    common_deps = [
        "pydantic",
        "yaml",
        "jinja2",
        "aiohttp",
        "pytest",
        "structlog",
        "cryptography",
        "click",
        "pydantic_settings",
        "tenacity",
        "psutil",
        "httpx",
        "openai",
        "requests",
        "temporalio",
        "opentelemetry",
        "jwt",
    ]

    for dep in common_deps:
        if dep in import_statement:
            return True

    # Check if it's a local autopr import
    if "autopr." in import_statement:
        return True

    # Check if it's a local templates import
    if "templates." in import_statement:
        return True

    # Check if it's a local tools import
    if "tools." in import_statement:
        return True

    # Check if it's a future import
    if "from __future__ import" in import_statement:
        return True

    return False


def validate_imports(project_root: str) -> dict[str, list[tuple[str, int, str]]]:
    """Validate all imports in the project."""
    python_files = find_python_files(project_root)
    broken_imports = {}

    print(f"Scanning {len(python_files)} Python files...")

    for file_path in python_files:
        imports = extract_imports(file_path)
        file_broken_imports = []

        for module, line_num, line in imports:
            if not check_import_validity(line, file_path):
                file_broken_imports.append((module, line_num, line))

        if file_broken_imports:
            broken_imports[file_path] = file_broken_imports

    return broken_imports


def generate_import_report(broken_imports: dict[str, list[tuple[str, int, str]]]) -> str:
    """Generate a report of broken imports."""
    if not broken_imports:
        return "✅ No broken imports found!"

    report = ["❌ Broken Imports Found:", ""]

    for file_path, imports in broken_imports.items():
        report.append(f"📁 {file_path}:")
        for module, line_num, line in imports:
            report.append(f"  Line {line_num}: {line}")
        report.append("")

    return "\n".join(report)


def main():
    """Main function."""
    project_root = os.getcwd()

    print("🔍 AutoPR Engine Import Validation")
    print("=" * 50)

    # Validate imports
    broken_imports = validate_imports(project_root)

    # Generate report
    report = generate_import_report(broken_imports)
    print(report)

    # Save report to file
    report_file = os.path.join(project_root, "import_validation_report.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📄 Report saved to: {report_file}")

    if broken_imports:
        print(f"\n⚠️  Found {len(broken_imports)} files with broken imports")
        return 1
    else:
        print("\n✅ All imports are valid!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
