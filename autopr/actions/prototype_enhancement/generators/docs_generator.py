"""
Documentation Generator Module

Handles generation of project documentation including README, API docs, and contribution guidelines.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from .base_generator import BaseGenerator


class DocsGenerator(BaseGenerator):
    """Generates project documentation and related files."""

    def generate(self, output_dir: str, **kwargs) -> list[str]:
        """Generate documentation files.

        Args:
            output_dir: The directory to generate files in
            **kwargs: Additional arguments including:
                - project_name: The name of the project
                - description: Project description
                - author: Project author
                - version: Project version (default: 0.1.0)
                - license: Project license (default: MIT)
                - language: The programming language
                - framework: The web framework being used
                - repo_url: URL of the repository
                - docs_dir: Directory for documentation (default: 'docs')
                - include_api_docs: Whether to include API documentation (default: True)
                - include_contributing: Whether to include CONTRIBUTING.md (default: True)
                - include_changelog: Whether to include CHANGELOG.md (default: True)
                - include_code_of_conduct: Whether to include CODE_OF_CONDUCT.md (default: True)
                - include_license: Whether to include LICENSE (default: True)
                - include_github_actions: Whether to include GitHub Actions workflows (default: True)
        Returns:
            List of paths to generated files
        """
        generated_files = []
        project_name = kwargs.get("project_name", "my-project")

        # Common variables for documentation templates
        template_vars = {
            "project_name": project_name,
            "description": kwargs.get("description", "A new project"),
            "author": kwargs.get("author", "Your Name"),
            "version": kwargs.get("version", "0.1.0"),
            "license": kwargs.get("license", "MIT"),
            "language": kwargs.get("language", "").lower(),
            "framework": kwargs.get("framework", "").lower(),
            "repo_url": kwargs.get("repo_url", ""),
            "year": datetime.now().year,
            **self._get_platform_variables(),
        }

        # Create docs directory
        docs_dir = Path(output_dir) / kwargs.get("docs_dir", "docs")
        docs_dir.mkdir(exist_ok=True)

        # Generate README.md
        generated_files.extend(self._generate_readme(output_dir, template_vars))

        # Generate CONTRIBUTING.md
        if kwargs.get("include_contributing", True):
            generated_files.extend(self._generate_contributing(output_dir, template_vars))

        # Generate CHANGELOG.md
        if kwargs.get("include_changelog", True):
            generated_files.extend(self._generate_changelog(output_dir, template_vars))

        # Generate CODE_OF_CONDUCT.md
        if kwargs.get("include_code_of_conduct", True):
            generated_files.extend(self._generate_code_of_conduct(output_dir, template_vars))

        # Generate LICENSE
        if kwargs.get("include_license", True):
            generated_files.extend(self._generate_license(output_dir, template_vars))

        # Generate API documentation
        if kwargs.get("include_api_docs", True):
            generated_files.extend(self._generate_api_docs(docs_dir, template_vars))

        # Generate GitHub Actions workflows
        if kwargs.get("include_github_actions", True):
            generated_files.extend(self._generate_github_actions(output_dir, template_vars))

        return generated_files

    def _generate_readme(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate README.md file."""
        content = self._render_template("docs/README.md", variables)
        if not content:
            # Fallback to a basic README
            content = f"""# {variables['project_name']}

{variables['description']}

## Getting Started

### Prerequisites

- Node.js 16+ (for JavaScript/TypeScript projects)
- Python 3.8+ (for Python projects)
- Docker (optional)

### Installation

```bash
# Clone the repository
git clone {variables['repo_url']}
cd {variables['project_name']}

# Install dependencies
npm install  # for Node.js projects
# or
pip install -r requirements.txt  # for Python projects
```

### Usage

```bash
# Start development server
npm run dev  # for Node.js projects
# or
python app.py  # for Python projects
```

## Documentation

For more detailed documentation, see the [docs](docs/) directory.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the {variables['license']} License - see the [LICENSE](LICENSE) file for details.
"""

        file_path = str(Path(output_dir) / "README.md")
        self._write_file(file_path, content)
        return [file_path]

    def _generate_contributing(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate CONTRIBUTING.md file."""
        content = self._render_template("docs/CONTRIBUTING.md", variables)
        if not content:
            content = f"""# Contributing to {variables['project_name']}

Thank you for your interest in contributing! Here are some guidelines to help you get started.

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

1. **Fork** the repository on GitHub
2. **Clone** the project to your own machine
3. **Commit** changes to your own branch
4. **Push** your work back up to your fork
5. Submit a **Pull Request** so we can review your changes

## Development Setup

### Prerequisites

- Node.js 16+ (for JavaScript/TypeScript projects)
- Python 3.8+ (for Python projects)
- Docker (optional)

### Installation

```bash
# Clone your fork
git clone git@github.com:YOUR_USERNAME/{variables['project_name']}.git
cd {variables['project_name']}

# Set up the upstream remote
git remote add upstream {variables['repo_url']}

# Install dependencies
npm install  # for Node.js projects
# or
pip install -r requirements.txt  # for Python projects
```

### Testing

```bash
npm test  # for Node.js projects
# or
pytest  # for Python projects
```

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build.
2. Update the README.md with details of changes to the interface, this includes new environment variables, exposed ports, useful file locations and container parameters.
3. Increase the version numbers in any examples files and the README.md to the new version that this Pull Request would represent.
4. The PR will be reviewed by maintainers who may suggest changes.

## Reporting Issues

Please use the [GitHub issue tracker]({variables['repo_url']}/issues) to report any issues or submit feature requests.
"""

        file_path = str(Path(output_dir) / "CONTRIBUTING.md")
        self._write_file(file_path, content)
        return [file_path]

    def _generate_changelog(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate CHANGELOG.md file."""
        content = self._render_template("docs/CHANGELOG.md", variables)
        if not content:
            content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup

## [0.1.0] - {datetime.now().strftime('%Y-%m-%d')}

### Added
- Initial release
"""

        file_path = str(Path(output_dir) / "CHANGELOG.md")
        self._write_file(file_path, content)
        return [file_path]

    def _generate_code_of_conduct(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate CODE_OF_CONDUCT.md file."""
        content = self._render_template("docs/CODE_OF_CONDUCT.md", variables)
        if not content:
            content = """# Contributor Covenant Code of Conduct

## Our Pledge

In the interest of fostering an open and welcoming environment, we as contributors and maintainers pledge to make participation in our project and our community a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

## Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

Examples of unacceptable behavior by participants include:

- The use of sexualized language or imagery and unwelcome sexual attention or advances
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information, such as a physical or electronic address, without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

## Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable behavior and are expected to take appropriate and fair corrective action in response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or reject comments, commits, code, wiki edits, issues, and other contributions that are not aligned to this Code of Conduct, or to ban temporarily or permanently any contributor for other behaviors that they deem inappropriate, threatening, offensive, or harmful.

## Scope

This Code of Conduct applies both within project spaces and in public spaces when an individual is representing the project or its community. Examples of representing a project or community include using an official project e-mail address, posting via an official social media account, or acting as an appointed representative at an online or offline event.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team at [INSERT EMAIL ADDRESS]. All complaints will be reviewed and investigated and will result in a response that is deemed necessary and appropriate to the circumstances. The project team is obligated to maintain confidentiality with regard to the reporter of an incident. Further details of specific enforcement policies may be posted separately.

Project maintainers who do not follow or enforce the Code of Conduct in good faith may face temporary or permanent repercussions as determined by other members of the project's leadership.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage], version 1.4, available at [http://contributor-covenant.org/version/1/4][version]

[homepage]: http://contributor-covenant.org
[version]: http://contributor-covenant.org/version/1/4/
"""

        file_path = str(Path(output_dir) / "CODE_OF_CONDUCT.md")
        self._write_file(file_path, content)
        return [file_path]

    def _generate_license(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate LICENSE file."""
        license_type = variables.get("license", "MIT").lower()
        content = self._render_template(f"docs/licenses/{license_type}.txt", variables)

        if not content and license_type == "mit":
            content = f"""MIT License

Copyright (c) {datetime.now().year} {variables.get('author', '')}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

        if content:
            file_path = str(Path(output_dir) / "LICENSE")
            self._write_file(file_path, content)
            return [file_path]

        return []

    def _generate_api_docs(self, docs_dir: Path, variables: dict[str, Any]) -> list[str]:
        """Generate API documentation."""
        generated_files = []
        language = variables.get("language", "")

        # Create API documentation directory
        api_dir = docs_dir / "api"
        api_dir.mkdir(exist_ok=True)

        # Generate API documentation based on language/framework
        if language == "typescript":
            # Generate TypeScript API docs with TypeDoc
            content = """# API Reference

This documentation was generated with [TypeDoc](https://typedoc.org/).

## Installation

```bash
# Install TypeDoc
npm install --save-dev typedoc

# Generate documentation
npm run docs
```

## Viewing Documentation

Open `docs/api/index.html` in your browser to view the API documentation.
"""
            readme_path = api_dir / "README.md"
            self._write_file(str(readme_path), content)
            generated_files.append(str(readme_path))

            # Add docs script to package.json if it exists
            package_json_path = Path(docs_dir).parent / "package.json"
            if package_json_path.exists():
                package_json = self._read_json_file(str(package_json_path))
                if package_json:
                    package_json.setdefault("scripts", {})
                    if "docs" not in package_json["scripts"]:
                        package_json["scripts"]["docs"] = "typedoc --out docs/api src/"
                        self._write_json_file(str(package_json_path), package_json)
                        generated_files.append(str(package_json_path))

        elif language == "python":
            # Generate Python API docs with Sphinx
            content = """# API Reference

This documentation was generated with [Sphinx](https://www.sphinx-doc.org/).

## Installation

```bash
# Install Sphinx and theme
pip install sphinx sphinx-rtd-theme

# Generate documentation
cd docs
make html
```

## Viewing Documentation

Open `docs/_build/html/index.html` in your browser to view the API documentation.
"""
            readme_path = api_dir / "README.md"
            self._write_file(str(readme_path), content)
            generated_files.append(str(readme_path))

            # Create Sphinx configuration if it doesn't exist
            conf_py = docs_dir / "conf.py"
            if not conf_py.exists():
                sphinx_quickstart = f"""# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = '{variables['project_name']}'
copyright = '{datetime.now().year}, {variables.get('author', '')}'
author = '{variables.get('author', '')}'
release = '{variables.get('version', '0.1.0')}'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}
"""
                self._write_file(str(conf_py), sphinx_quickstart)
                generated_files.append(str(conf_py))
                # Create index.rst
                index_rst = f""".. {variables['project_name']} documentation master file, created by
   sphinx-quickstart on {datetime.now().strftime('%Y-%m-%d')}.

Welcome to {variables['project_name']}'s documentation!
=========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
"""
                index_path = docs_dir / "index.rst"
                self._write_file(str(index_path), index_rst)
                generated_files.append(str(index_path))

                # Create modules.rst
                modules_rst = f"""{variables['project_name']}
{'=' * len(variables['project_name'])}

.. automodule:: {variables['project_name'].lower().replace('-', '_')}
   :members:
   :undoc-members:
   :show-inheritance:
"""
                modules_path = docs_dir / "modules.rst"
                self._write_file(str(modules_path), modules_rst)
                generated_files.append(str(modules_path))

        return generated_files

    def _generate_github_actions(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate GitHub Actions workflows."""
        generated_files = []
        workflows_dir = Path(output_dir) / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        # CI workflow
        ci_workflow = """name: CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [16.x, 18.x]
        # Add more versions as needed

    steps:
    - uses: actions/checkout@v3

    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Run tests
      run: npm test

    - name: Build
      run: npm run build --if-present

    - name: Lint
      run: npm run lint --if-present
"""
        ci_path = workflows_dir / "ci.yml"
        self._write_file(str(ci_path), ci_workflow)
        generated_files.append(str(ci_path))

        # CodeQL analysis
        codeql_workflow = """name: "CodeQL"

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  schedule:
    - cron: '0 0 * * 0'

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [ 'javascript' ]
        # Add more languages as needed

    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v2
      with:
        languages: ${{ matrix.language }}
        # Add any additional queries or configurations

    - name: Autobuild
      uses: github/codeql-action/autobuild@v2

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2
"""
        codeql_path = workflows_dir / "codeql-analysis.yml"
        self._write_file(str(codeql_path), codeql_workflow)
        generated_files.append(str(codeql_path))

        return generated_files
