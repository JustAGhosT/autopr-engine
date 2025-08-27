"""
Setup script for AutoPR Engine

Installs the AutoPR CLI and makes it available system-wide.
"""

import os

from setuptools import find_packages, setup


# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, encoding="utf-8") as f:
            return f.read()
    return "AutoPR Engine - AI-Powered Code Quality and Automation"


# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, encoding="utf-8") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    return []


setup(
    name="autopr-engine",
    version="1.0.0",
    author="AutoPR Team",
    author_email="team@autopr.dev",
    description="AI-Powered Code Quality and Automation Engine",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/autopr/autopr-engine",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
            "pre-commit>=3.0.0",
        ],
        "dashboard": [
            "flask>=2.3.0",
            "flask-cors>=4.0.0",
        ],
        "full": [
            "flask>=2.3.0",
            "flask-cors>=4.0.0",
            "click>=8.1.0",
            "openai>=1.0.0",
            "anthropic>=0.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "autopr=autopr.cli.main:cli",
            "autopr-dashboard=autopr.dashboard.server:run_dashboard",
        ],
    },
    include_package_data=True,
    package_data={
        "autopr": [
            "dashboard/templates/*.html",
            "dashboard/static/*",
        ],
    },
    keywords=[
        "ai",
        "code-quality",
        "automation",
        "linting",
        "testing",
        "code-review",
        "git-hooks",
        "ci-cd",
        "development-tools",
    ],
    project_urls={
        "Bug Reports": "https://github.com/autopr/autopr-engine/issues",
        "Source": "https://github.com/autopr/autopr-engine",
        "Documentation": "https://autopr.dev/docs",
    },
)
