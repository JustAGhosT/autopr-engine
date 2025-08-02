#!/usr/bin/env python3
"""
Configuration validation script for AutoPR Engine.

This script validates configuration files and checks for duplicates,
inconsistencies, and missing required configurations.
"""

import json
import os
import sys
from typing import Any

import yaml


def find_config_files(directory: str) -> dict[str, list[str]]:
    """Find all configuration files in the directory."""
    config_files = {"yaml": [], "json": [], "ini": [], "toml": []}

    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and node_modules
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]

        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith((".yaml", ".yml")):
                config_files["yaml"].append(file_path)
            elif file.endswith(".json"):
                config_files["json"].append(file_path)
            elif file.endswith(".ini"):
                config_files["ini"].append(file_path)
            elif file.endswith(".toml"):
                config_files["toml"].append(file_path)

    return config_files


def validate_yaml_file(file_path: str) -> tuple[bool, str]:
    """Validate a YAML file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            yaml.safe_load(f)
        return True, "Valid YAML"
    except yaml.YAMLError as e:
        return False, f"YAML Error: {e}"
    except Exception as e:
        return False, f"File Error: {e}"


def validate_json_file(file_path: str) -> tuple[bool, str]:
    """Validate a JSON file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            json.load(f)
        return True, "Valid JSON"
    except json.JSONDecodeError as e:
        return False, f"JSON Error: {e}"
    except Exception as e:
        return False, f"File Error: {e}"


def check_duplicate_workflows(config_files: dict[str, list[str]]) -> list[tuple[str, str]]:
    """Check for duplicate workflow configurations."""
    duplicates = []
    workflow_names = {}

    for yaml_file in config_files["yaml"]:
        if "workflows" in yaml_file:
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                    if content and "name" in content:
                        name = content["name"]
                        if name in workflow_names:
                            duplicates.append((workflow_names[name], yaml_file))
                        else:
                            workflow_names[name] = yaml_file
            except Exception:
                continue

    return duplicates


def check_configuration_consistency(config_files: dict[str, list[str]]) -> list[str]:
    """Check for configuration consistency issues."""
    issues = []

    # Check for required configuration files
    required_configs = ["configs/config.yaml", "configs/mypy.ini", "configs/.flake8"]

    for config in required_configs:
        if not os.path.exists(config):
            issues.append(f"Missing required configuration: {config}")

    # Check for configuration file naming consistency
    for yaml_file in config_files["yaml"]:
        if "configs/workflows" in yaml_file:
            filename = os.path.basename(yaml_file)
            if filename.startswith("phase") and "-" in filename and "_" in filename:
                issues.append(f"Inconsistent naming in workflow: {yaml_file}")

    return issues


def validate_configurations(config_files: dict[str, list[str]]) -> dict[str, Any]:
    """Validate all configuration files."""
    results = {"valid_files": [], "invalid_files": [], "duplicates": [], "issues": []}

    # Validate YAML files
    for yaml_file in config_files["yaml"]:
        is_valid, message = validate_yaml_file(yaml_file)
        if is_valid:
            results["valid_files"].append(yaml_file)
        else:
            results["invalid_files"].append((yaml_file, message))

    # Validate JSON files
    for json_file in config_files["json"]:
        is_valid, message = validate_json_file(json_file)
        if is_valid:
            results["valid_files"].append(json_file)
        else:
            results["invalid_files"].append((json_file, message))

    # Check for duplicates
    results["duplicates"] = check_duplicate_workflows(config_files)

    # Check for consistency issues
    results["issues"] = check_configuration_consistency(config_files)

    return results


def generate_config_report(results: dict[str, Any]) -> str:
    """Generate a configuration validation report."""
    report = ["🔧 AutoPR Engine Configuration Validation Report", ""]

    # Valid files
    if results["valid_files"]:
        report.append(f"✅ Valid Configuration Files ({len(results['valid_files'])}):")
        for file_path in results["valid_files"]:
            report.append(f"  - {file_path}")
        report.append("")

    # Invalid files
    if results["invalid_files"]:
        report.append(f"❌ Invalid Configuration Files ({len(results['invalid_files'])}):")
        for file_path, error in results["invalid_files"]:
            report.append(f"  - {file_path}: {error}")
        report.append("")

    # Duplicates
    if results["duplicates"]:
        report.append(f"⚠️  Duplicate Workflows ({len(results['duplicates'])}):")
        for file1, file2 in results["duplicates"]:
            report.append(f"  - {file1}")
            report.append(f"    {file2}")
        report.append("")

    # Issues
    if results["issues"]:
        report.append(f"🔍 Configuration Issues ({len(results['issues'])}):")
        for issue in results["issues"]:
            report.append(f"  - {issue}")
        report.append("")

    if not any([results["invalid_files"], results["duplicates"], results["issues"]]):
        report.append("🎉 All configurations are valid and consistent!")

    return "\n".join(report)


def main():
    """Main function."""
    project_root = os.getcwd()
    configs_dir = os.path.join(project_root, "configs")

    print("🔧 AutoPR Engine Configuration Validation")
    print("=" * 50)

    # Find configuration files
    config_files = find_config_files(configs_dir)

    print("Found configuration files:")
    for file_type, files in config_files.items():
        print(f"  {file_type.upper()}: {len(files)} files")
    print("")

    # Validate configurations
    results = validate_configurations(config_files)

    # Generate and display report
    report = generate_config_report(results)
    print(report)

    # Save report to file
    report_file = os.path.join(project_root, "config_validation_report.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📄 Report saved to: {report_file}")

    # Return appropriate exit code
    if results["invalid_files"] or results["duplicates"] or results["issues"]:
        print(
            f"\n⚠️  Found {len(results['invalid_files'])} invalid files, "
            f"{len(results['duplicates'])} duplicates, and {len(results['issues'])} issues"
        )
        return 1
    else:
        print("\n✅ All configurations are valid!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
