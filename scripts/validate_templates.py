#!/usr/bin/env python3
"""
Template validation script for AutoPR Engine.

This script validates template files and checks for consistency,
completeness, and proper organization.
"""

import json
import os
import sys
from typing import Any

import yaml


def find_template_files(directory: str) -> dict[str, list[str]]:
    """Find all template files in the directory."""
    template_files = {"yaml": [], "json": [], "py": [], "md": []}

    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and cache
        dirs[:] = [
            d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "node_modules"]
        ]

        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith((".yaml", ".yml")):
                template_files["yaml"].append(file_path)
            elif file.endswith(".json"):
                template_files["json"].append(file_path)
            elif file.endswith(".py"):
                template_files["py"].append(file_path)
            elif file.endswith(".md"):
                template_files["md"].append(file_path)

    return template_files


def validate_yaml_template(file_path: str) -> tuple[bool, str]:
    """Validate a YAML template file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = yaml.safe_load(f)

        # Basic template validation
        if not content:
            return False, "Empty template file"

        # Check for required template fields
        if isinstance(content, dict):
            if "name" in content and not content["name"]:
                return False, "Template name is empty"
            if "description" in content and not content["description"]:
                return False, "Template description is empty"

        return True, "Valid YAML template"
    except yaml.YAMLError as e:
        return False, f"YAML Error: {e}"
    except Exception as e:
        return False, f"File Error: {e}"


def validate_json_template(file_path: str) -> tuple[bool, str]:
    """Validate a JSON template file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = json.load(f)

        # Basic template validation
        if not content:
            return False, "Empty template file"

        # Check for required template fields
        if isinstance(content, dict):
            if "name" in content and not content["name"]:
                return False, "Template name is empty"
            if "description" in content and not content["description"]:
                return False, "Template description is empty"

        return True, "Valid JSON template"
    except json.JSONDecodeError as e:
        return False, f"JSON Error: {e}"
    except Exception as e:
        return False, f"File Error: {e}"


def check_template_organization(template_files: dict[str, list[str]]) -> list[str]:
    """Check for template organization issues."""
    issues = []

    # Check for templates in wrong locations
    for yaml_file in template_files["yaml"]:
        if "templates/" in yaml_file:
            # Check if template is in appropriate subdirectory
            if "platforms/" in yaml_file:
                # Platform templates should have platform-specific content
                try:
                    with open(yaml_file, encoding="utf-8") as f:
                        content = yaml.safe_load(f)
                    if content and isinstance(content, dict):
                        if "platform" not in content and "type" not in content:
                            issues.append(f"Platform template missing platform info: {yaml_file}")
                except Exception:
                    pass

    return issues


def check_template_consistency(template_files: dict[str, list[str]]) -> list[str]:
    """Check for template consistency issues."""
    issues = []

    # Check for consistent naming patterns
    for yaml_file in template_files["yaml"]:
        if "templates/" in yaml_file:
            filename = os.path.basename(yaml_file)
            if filename.startswith("template_") and not filename.endswith(".py"):
                issues.append(f"Inconsistent template naming: {yaml_file}")

    return issues


def validate_templates(template_files: dict[str, list[str]]) -> dict[str, Any]:
    """Validate all template files."""
    results = {
        "valid_files": [],
        "invalid_files": [],
        "organization_issues": [],
        "consistency_issues": [],
    }

    # Validate YAML templates
    for yaml_file in template_files["yaml"]:
        is_valid, message = validate_yaml_template(yaml_file)
        if is_valid:
            results["valid_files"].append(yaml_file)
        else:
            results["invalid_files"].append((yaml_file, message))

    # Validate JSON templates
    for json_file in template_files["json"]:
        is_valid, message = validate_json_template(json_file)
        if is_valid:
            results["valid_files"].append(json_file)
        else:
            results["invalid_files"].append((json_file, message))

    # Check organization and consistency
    results["organization_issues"] = check_template_organization(template_files)
    results["consistency_issues"] = check_template_consistency(template_files)

    return results


def generate_template_report(results: dict[str, Any]) -> str:
    """Generate a template validation report."""
    report = ["📋 AutoPR Engine Template Validation Report", ""]

    # Valid files
    if results["valid_files"]:
        report.append(f"✅ Valid Template Files ({len(results['valid_files'])}):")
        for file_path in results["valid_files"]:
            report.append(f"  - {file_path}")
        report.append("")

    # Invalid files
    if results["invalid_files"]:
        report.append(f"❌ Invalid Template Files ({len(results['invalid_files'])}):")
        for file_path, error in results["invalid_files"]:
            report.append(f"  - {file_path}: {error}")
        report.append("")

    # Organization issues
    if results["organization_issues"]:
        report.append(f"🔍 Organization Issues ({len(results['organization_issues'])}):")
        for issue in results["organization_issues"]:
            report.append(f"  - {issue}")
        report.append("")

    # Consistency issues
    if results["consistency_issues"]:
        report.append(f"⚠️  Consistency Issues ({len(results['consistency_issues'])}):")
        for issue in results["consistency_issues"]:
            report.append(f"  - {issue}")
        report.append("")

    if not any(
        [results["invalid_files"], results["organization_issues"], results["consistency_issues"]]
    ):
        report.append("🎉 All templates are valid and well-organized!")

    return "\n".join(report)


def main():
    """Main function."""
    project_root = os.getcwd()
    templates_dir = os.path.join(project_root, "templates")

    print("📋 AutoPR Engine Template Validation")
    print("=" * 50)

    # Find template files
    template_files = find_template_files(templates_dir)

    print("Found template files:")
    for file_type, files in template_files.items():
        print(f"  {file_type.upper()}: {len(files)} files")
    print("")

    # Validate templates
    results = validate_templates(template_files)

    # Generate and display report
    report = generate_template_report(results)
    print(report)

    # Save report to file
    report_file = os.path.join(project_root, "template_validation_report.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📄 Report saved to: {report_file}")

    # Return appropriate exit code
    if results["invalid_files"] or results["organization_issues"] or results["consistency_issues"]:
        print(
            f"\n⚠️  Found {len(results['invalid_files'])} invalid files, "
            f"{len(results['organization_issues'])} organization issues, and "
            f"{len(results['consistency_issues'])} consistency issues"
        )
        return 1
    else:
        print("\n✅ All templates are valid!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
