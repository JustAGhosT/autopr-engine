"""
Configuration Generator Module

Handles generation of configuration files for different platforms and frameworks.
"""

from pathlib import Path
from typing import Any

from .base_generator import BaseGenerator


class ConfigGenerator(BaseGenerator):
    """Generates configuration files for different platforms and frameworks."""

    def generate(self, output_dir: str, **kwargs) -> list[str]:
        """Generate configuration files in the specified output directory.

        Args:
            output_dir: The directory to generate files in
            **kwargs: Additional arguments including:
                - framework: The framework to generate configs for
                - language: The programming language
                - app_name: The name of the application
                - version: The version of the application
        Returns:
            List of paths to generated files
        """
        generated_files = []
        framework = kwargs.get("framework", "").lower()
        language = kwargs.get("language", "").lower()
        app_name = kwargs.get("app_name", "myapp")
        version = kwargs.get("version", "1.0.0")

        # Common variables for all templates
        template_vars = {
            "app_name": app_name,
            "version": version,
            "language": language,
            "framework": framework,
            **self._get_platform_variables(),
        }

        # Generate framework-specific configs
        if framework == "react":
            generated_files.extend(self._generate_react_configs(output_dir, template_vars))
        elif framework == "express":
            generated_files.extend(self._generate_express_configs(output_dir, template_vars))
        elif framework == "flask":
            generated_files.extend(self._generate_flask_configs(output_dir, template_vars))

        # Generate language-specific configs
        if language == "typescript":
            generated_files.extend(self._generate_typescript_configs(output_dir, template_vars))
        elif language == "python":
            generated_files.extend(self._generate_python_configs(output_dir, template_vars))

        # Generate common config files
        generated_files.extend(self._generate_common_configs(output_dir, template_vars))

        return generated_files

    def _generate_react_configs(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate React-specific configuration files."""
        generated_files = []
        templates = [
            "package.json",
            "tsconfig.json",
            ".eslintrc.js",
            ".prettierrc",
            "vite.config.ts",
        ]

        for template in templates:
            content = self._render_template(f"react/{template}", variables)
            if content:
                file_path = str(Path(output_dir) / template)
                self._write_file(file_path, content)
                generated_files.append(file_path)

        return generated_files

    def _generate_express_configs(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate Express.js-specific configuration files."""
        generated_files = []
        templates = ["package.json", "tsconfig.json", ".eslintrc.js", ".prettierrc"]

        for template in templates:
            content = self._render_template(f"express/{template}", variables)
            if content:
                file_path = str(Path(output_dir) / template)
                self._write_file(file_path, content)
                generated_files.append(file_path)

        return generated_files

    def _generate_flask_configs(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate Flask-specific configuration files."""
        generated_files = []
        templates = ["requirements.txt", "config.py", ".flaskenv", ".env.example"]

        for template in templates:
            content = self._render_template(f"flask/{template}", variables)
            if content:
                file_path = str(Path(output_dir) / template)
                self._write_file(file_path, content)
                generated_files.append(file_path)

        return generated_files

    def _generate_typescript_configs(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate TypeScript-specific configuration files."""
        generated_files = []
        templates = ["tsconfig.json", ".eslintrc.js", ".prettierrc"]

        for template in templates:
            content = self._render_template(f"typescript/{template}", variables)
            if content:
                file_path = str(Path(output_dir) / template)
                self._write_file(file_path, content)
                generated_files.append(file_path)

        return generated_files

    def _generate_python_configs(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate Python-specific configuration files."""
        generated_files = []
        templates = [
            "requirements.txt",
            "setup.py",
            ".pylintrc",
            ".flake8",
            ".env.example",
        ]

        for template in templates:
            content = self._render_template(f"python/{template}", variables)
            if content:
                file_path = str(Path(output_dir) / template)
                self._write_file(file_path, content)
                generated_files.append(file_path)

        return generated_files

    def _generate_common_configs(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate common configuration files for all projects."""
        generated_files = []
        templates = [".gitignore", "README.md", "LICENSE", ".editorconfig"]

        for template in templates:
            content = self._render_template(f"common/{template}", variables)
            if content:
                file_path = str(Path(output_dir) / template)
                self._write_file(file_path, content)
                generated_files.append(file_path)
        return generated_files
