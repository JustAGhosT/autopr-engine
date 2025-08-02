#!/usr/bin/env python3
"""
Build system validation script for AutoPR Engine.

This script validates the build system configuration and checks for
consistency, completeness, and proper organization.
"""

import os
import sys
import tomllib
from typing import Any


def find_build_files(directory: str) -> dict[str, list[str]]:
    """Find all build-related files in the directory."""
    build_files = {"toml": [], "yaml": [], "json": [], "lock": [], "cache": []}

    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and node_modules
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".") and d not in ["__pycache__", "node_modules", ".venv"]
        ]

        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".toml"):
                build_files["toml"].append(file_path)
            elif file.endswith((".yaml", ".yml")):
                build_files["yaml"].append(file_path)
            elif file.endswith(".json"):
                build_files["json"].append(file_path)
            elif file.endswith(".lock"):
                build_files["lock"].append(file_path)
            elif file.endswith((".cache", ".coverage")):
                build_files["cache"].append(file_path)

    return build_files


def validate_pyproject_toml(file_path: str) -> tuple[bool, str]:
    """Validate pyproject.toml configuration."""
    try:
        with open(file_path, "rb") as f:
            config = tomllib.load(f)

        # Check for required sections
        required_sections = ["project", "build-system"]
        missing_sections = []

        for section in required_sections:
            if section not in config:
                missing_sections.append(section)

        if missing_sections:
            return False, f"Missing required sections: {', '.join(missing_sections)}"

        # Check project metadata
        project = config.get("project", {})
        required_fields = ["name", "version", "description"]
        missing_fields = []

        for field in required_fields:
            if field not in project:
                missing_fields.append(field)

        if missing_fields:
            return False, f"Missing required project fields: {', '.join(missing_fields)}"

        # Check dependencies
        if "dependencies" not in project:
            return False, "Missing dependencies section"

        return True, "Valid pyproject.toml"
    except Exception as e:
        return False, f"Error reading pyproject.toml: {e}"


def check_build_artifacts(build_files: dict[str, list[str]]) -> list[str]:
    """Check for build artifact issues."""
    issues = []

    # Check for build artifacts in wrong locations
    for cache_file in build_files["cache"]:
        if "build-artifacts" not in cache_file and os.path.basename(cache_file).startswith("."):
            issues.append(f"Build artifact in wrong location: {cache_file}")

    # Check for missing build-artifacts directory
    if not os.path.exists("build-artifacts"):
        issues.append("Missing build-artifacts directory")

    return issues


def check_package_management(build_files: dict[str, list[str]]) -> list[str]:
    """Check for package management issues."""
    issues = []

    # Check for redundant requirements files
    redundant_files = ["requirements.txt", "requirements-dev.txt", "setup.py", "setup.cfg"]
    for file in redundant_files:
        if os.path.exists(file):
            issues.append(f"Redundant package management file: {file}")

    # Check for pyproject.toml
    if not os.path.exists("pyproject.toml"):
        issues.append("Missing pyproject.toml (primary package configuration)")

    return issues


def validate_build_system(build_files: dict[str, list[str]]) -> dict[str, Any]:
    """Validate the build system."""
    results = {
        "valid_files": [],
        "invalid_files": [],
        "build_artifact_issues": [],
        "package_management_issues": [],
    }

    # Validate pyproject.toml
    pyproject_path = "pyproject.toml"
    if os.path.exists(pyproject_path):
        is_valid, message = validate_pyproject_toml(pyproject_path)
        if is_valid:
            results["valid_files"].append(pyproject_path)
        else:
            results["invalid_files"].append((pyproject_path, message))

    # Check build artifacts
    results["build_artifact_issues"] = check_build_artifacts(build_files)

    # Check package management
    results["package_management_issues"] = check_package_management(build_files)

    return results


def generate_build_report(results: dict[str, Any]) -> str:
    """Generate a build system validation report."""
    report = ["🔧 AutoPR Engine Build System Validation Report", ""]

    # Valid files
    if results["valid_files"]:
        report.append(f"✅ Valid Build Files ({len(results['valid_files'])}):")
        for file_path in results["valid_files"]:
            report.append(f"  - {file_path}")
        report.append("")

    # Invalid files
    if results["invalid_files"]:
        report.append(f"❌ Invalid Build Files ({len(results['invalid_files'])}):")
        for file_path, error in results["invalid_files"]:
            report.append(f"  - {file_path}: {error}")
        report.append("")

    # Build artifact issues
    if results["build_artifact_issues"]:
        report.append(f"🔍 Build Artifact Issues ({len(results['build_artifact_issues'])}):")
        for issue in results["build_artifact_issues"]:
            report.append(f"  - {issue}")
        report.append("")

    # Package management issues
    if results["package_management_issues"]:
        report.append(
            f"📦 Package Management Issues ({len(results['package_management_issues'])}):"
        )
        for issue in results["package_management_issues"]:
            report.append(f"  - {issue}")
        report.append("")

    if not any(
        [
            results["invalid_files"],
            results["build_artifact_issues"],
            results["package_management_issues"],
        ]
    ):
        report.append("🎉 Build system is properly configured!")

    return "\n".join(report)


def main():
    """Main function."""
    project_root = os.getcwd()

    print("🔧 AutoPR Engine Build System Validation")
    print("=" * 50)

    # Find build files
    build_files = find_build_files(project_root)

    print("Found build files:")
    for file_type, files in build_files.items():
        print(f"  {file_type.upper()}: {len(files)} files")
    print("")

    # Validate build system
    results = validate_build_system(build_files)

    # Generate and display report
    report = generate_build_report(results)
    print(report)

    # Save report to file
    report_file = os.path.join(project_root, "build_system_validation_report.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📄 Report saved to: {report_file}")

    # Return appropriate exit code
    if (
        results["invalid_files"]
        or results["build_artifact_issues"]
        or results["package_management_issues"]
    ):
        print(
            f"\n⚠️  Found {len(results['invalid_files'])} invalid files, "
            f"{len(results['build_artifact_issues'])} build artifact issues, and "
            f"{len(results['package_management_issues'])} package management issues"
        )
        return 1
    else:
        print("\n✅ Build system is properly configured!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
