#!/usr/bin/env python3
"""Setup script for the markdown-lint package."""

from setuptools import find_packages, setup

# Read the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Read requirements
with open("requirements.txt", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="markdown-lint",
    version="0.1.0",
    description="A markdown linter and fixer with support for common style issues.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="VeritasVault Team",
    author_email="dev@veritasvault.net",
    url="https://github.com/yourusername/markdown-lint",
    packages=find_packages(),
    package_data={
        "markdown_lint": ["py.typed"],
    },
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mdlint=markdown_lint.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Text Processing :: Markup :: Markdown",
    ],
    python_requires=">=3.8",
    keywords="markdown lint linter formatter style checker",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/markdown-lint/issues",
        "Source": "https://github.com/yourusername/markdown-lint",
    },
)
