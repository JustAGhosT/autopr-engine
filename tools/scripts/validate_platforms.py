"""
Platform Configuration Validator

Validates platform configuration files for AutoPR.
Checks both platform index files and individual platform configurations.
"""

import json
import sys
from pathlib import Path
from typing import Any

# Project directories
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "configs" / "platforms"

# Required fields
REQUIRED_PLATFORM_FIELDS = [
    "id",
    "name",
    "category",
    "description",
    "version",
    "status",
    "type",
    "source",
    "is_active",
]

REQUIRED_INDEX_FIELDS = ["version", "platforms"]


def print_section(title: str) -> None:
    """Print a section header."""


def load_json_file(file_path: Path) -> tuple[bool, dict[str, Any] | None, list[str]]:
    """Load and parse a JSON file with detailed error reporting."""
    if not file_path.exists():
        return False, None, [f"File does not exist: {file_path}"]

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return False, None, ["File is empty"]
            try:
                data = json.loads(content)
                if not isinstance(data, dict):
                    return False, None, [f"Expected JSON object, got {type(data).__name__}"]
                return True, data, []
            except json.JSONDecodeError as e:
                return False, None, [f"Invalid JSON: {e!s}"]
    except Exception as e:
        return False, None, [f"Error reading file: {e!s}"]


def is_platform_index(file_path: Path) -> bool:
    """Check if file is a platform index."""
    return file_path.name.endswith("_platforms.json")


def find_config_files() -> list[Path]:
    """Find all JSON config files in platforms directory."""
    if not CONFIG_DIR.exists():
        return []
    return [f for f in CONFIG_DIR.glob("**/*.json") if f.is_file()]


def validate_platform_config(config: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate platform config against schema."""
    errors = [f"Missing required field: {f}" for f in REQUIRED_PLATFORM_FIELDS if f not in config]
    return len(errors) == 0, errors


def validate_platform_index(index: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate platform index against schema."""
    errors = [f"Missing required field: {f}" for f in REQUIRED_INDEX_FIELDS if f not in index]
    return len(errors) == 0, errors


def validate_file(file_path: Path) -> tuple[bool, list[str]]:
    """Validate a single configuration file with detailed error reporting."""
    if not file_path.exists():
        return False, [f"File does not exist: {file_path}"]

    success, data, errors = load_json_file(file_path)
    if not success:
        return False, errors

    if not isinstance(data, dict):
        return False, [f"Expected JSON object, got {type(data).__name__}"]

    # Check if this is an index file or platform config
    try:
        if is_platform_index(file_path):
            return validate_platform_index(data)
        return validate_platform_config(data)
    except Exception as e:
        return False, [f"Validation error: {e!s}"]


def print_validation_result(file_path: Path, is_valid: bool, errors: list[str]) -> int:
    """Print validation result and return error count."""
    file_path.relative_to(PROJECT_ROOT)
    if is_valid:
        return 0
    for _error in errors:
        pass
    return len(errors)


def main() -> int:
    """Main entry point for the validation script."""
    config_files = find_config_files()
    if not config_files:
        return 1

    # Categorize files
    index_files = [f for f in config_files if is_platform_index(f)]
    platform_files = [f for f in config_files if not is_platform_index(f)]

    total_errors = 0
    files_with_errors = 0

    # Validate index files
    if index_files:
        print_section("🔖 Validating Index Files")
        for file_path in index_files:
            is_valid, errors = validate_file(file_path)
            error_count = print_validation_result(file_path, is_valid, errors)
            total_errors += error_count
            if error_count > 0:
                files_with_errors += 1

    # Validate platform files
    if platform_files:
        print_section("🖥️  Validating Platform Files")
        for file_path in platform_files:
            is_valid, errors = validate_file(file_path)
            error_count = print_validation_result(file_path, is_valid, errors)
            total_errors += error_count
            if error_count > 0:
                files_with_errors += 1

    # Print summary
    if total_errors == 0:
        pass

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
