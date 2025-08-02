#!/usr/bin/env python3
"""
Documentation link validation script for AutoPR Engine.

This script checks for broken links in documentation files after
reorganization.
"""

import os
import re
import sys


def find_markdown_files(directory: str) -> list[str]:
    """Find all Markdown files in the directory."""
    markdown_files = []
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and node_modules
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]

        for file in files:
            if file.endswith(".md"):
                markdown_files.append(os.path.join(root, file))

    return markdown_files


def extract_links(file_path: str) -> list[tuple[str, int, str]]:
    """Extract links from a Markdown file."""
    links = []

    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            # Match Markdown links: [text](url)
            link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
            matches = re.finditer(link_pattern, line)

            for match in matches:
                link_text = match.group(1)
                link_url = match.group(2)
                links.append((link_url, line_num, line.strip()))

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return links


def check_link_validity(link_url: str, file_path: str, project_root: str) -> bool:
    """Check if a link is valid."""
    # Skip external links (including incomplete URLs)
    if link_url.startswith(("http://", "https://", "mailto:", "#", "<http")):
        return True

    # Skip node_modules links
    if "node_modules" in link_url:
        return True

    # Skip template variables
    if "{{" in link_url or "}}" in link_url:
        return True

    # Handle relative links
    if link_url.startswith("../"):
        # Go up directories
        current_dir = os.path.dirname(file_path)
        target_path = os.path.normpath(os.path.join(current_dir, link_url))
    elif link_url.startswith("./"):
        # Same directory
        current_dir = os.path.dirname(file_path)
        target_path = os.path.join(current_dir, link_url[2:])
    else:
        # Relative to current file
        current_dir = os.path.dirname(file_path)
        target_path = os.path.join(current_dir, link_url)

    # Check if file exists
    if os.path.exists(target_path):
        return True

    # Check if it's a directory with README.md
    if os.path.isdir(target_path):
        readme_path = os.path.join(target_path, "README.md")
        if os.path.exists(readme_path):
            return True

    return False


def validate_links(project_root: str) -> dict[str, list[tuple[str, int, str]]]:
    """Validate all links in documentation files."""
    markdown_files = find_markdown_files(project_root)
    broken_links = {}

    print(f"Scanning {len(markdown_files)} Markdown files...")

    for file_path in markdown_files:
        links = extract_links(file_path)
        file_broken_links = []

        for link_url, line_num, line in links:
            if not check_link_validity(link_url, file_path, project_root):
                file_broken_links.append((link_url, line_num, line))

        if file_broken_links:
            broken_links[file_path] = file_broken_links

    return broken_links


def generate_link_report(broken_links: dict[str, list[tuple[str, int, str]]]) -> str:
    """Generate a report of broken links."""
    if not broken_links:
        return "✅ No broken links found!"

    report = ["❌ Broken Links Found:", ""]

    for file_path, links in broken_links.items():
        report.append(f"📁 {file_path}:")
        for link_url, line_num, line in links:
            report.append(f"  Line {line_num}: {link_url}")
            report.append(f"    Context: {line}")
        report.append("")

    return "\n".join(report)


def main():
    """Main function."""
    project_root = os.getcwd()

    print("🔍 AutoPR Engine Link Validation")
    print("=" * 50)

    # Validate links
    broken_links = validate_links(project_root)

    # Generate report
    report = generate_link_report(broken_links)
    print(report)

    # Save report to file
    report_file = os.path.join(project_root, "link_validation_report.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📄 Report saved to: {report_file}")

    if broken_links:
        print(f"\n⚠️  Found {len(broken_links)} files with broken links")
        return 1
    else:
        print("\n✅ All links are valid!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
