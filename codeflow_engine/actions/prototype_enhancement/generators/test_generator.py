"""
Test Generator Module

Handles generation of test files and configurations for different testing frameworks.
"""

from pathlib import Path
from typing import Any

from codeflow_engine.actions.prototype_enhancement.generators.base_generator import BaseGenerator


class TestGenerator(BaseGenerator):
    """Generates test files and configurations for different testing frameworks."""

    def generate(self, output_dir: str, **kwargs) -> list[str]:
        """Generate test files and configurations.

        Args:
            output_dir: The directory to generate files in
            **kwargs: Additional arguments including:
                - language: The programming language
                - test_framework: The testing framework to use
                - src_dir: The source directory (defaults to 'src')
                - test_dir: The test directory (defaults to 'tests')
        Returns:
            List of paths to generated files
        """
        generated_files = []
        language = kwargs.get("language", "").lower()
        test_framework = kwargs.get("test_framework", "").lower()
        src_dir = kwargs.get("src_dir", "src")
        test_dir = kwargs.get("test_dir", "tests")

        # Common variables for test templates
        template_vars = {
            "language": language,
            "test_framework": test_framework,
            "src_dir": src_dir,
            "test_dir": test_dir,
            **self._get_platform_variables(),
        }

        # Generate test framework configuration
        generated_files.extend(self._generate_test_config(output_dir, template_vars))

        # Generate test examples based on language and framework
        if language == "typescript":
            generated_files.extend(
                self._generate_typescript_tests(output_dir, template_vars)
            )
        elif language == "python":
            generated_files.extend(
                self._generate_python_tests(output_dir, template_vars)
            )

        # Generate CI/CD configuration for tests
        generated_files.extend(self._generate_test_ci_config(output_dir, template_vars))

        return generated_files

    def _generate_test_config(
        self, output_dir: str, variables: dict[str, Any]
    ) -> list[str]:
        """Generate test configuration files."""
        generated_files = []
        language = variables.get("language", "")
        test_framework = variables.get("test_framework", "")

        # Common test configuration files
        config_files = []

        if language == "typescript":
            if test_framework == "jest":
                config_files.extend(
                    ["jest.config.js", "jest.setup.js"]
                )
            elif test_framework == "mocha":
                config_files.extend([".mocharc.json", "test/setup.ts"])
        elif language == "python":
            if test_framework == "pytest":
                config_files.extend(
                    ["pytest.ini", "conftest.py", "requirements-test.txt"]
                )
            elif test_framework == "unittest":
                config_files.append("test_requirements.txt")

        # Generate each config file
        for config_file in config_files:
            content = self._render_template(
                f"test/{language}/{test_framework}/{config_file}", variables
            )
            if content:
                file_path = str(Path(output_dir) / config_file)
                self._write_file(file_path, content)
                generated_files.append(file_path)

        return generated_files

    def _generate_typescript_tests(
        self, output_dir: str, variables: dict[str, Any]
    ) -> list[str]:
        """Generate TypeScript test files."""
        generated_files = []
        test_framework = variables.get("test_framework", "")
        test_dir = variables.get("test_dir", "tests")

        # Create test directory structure
        test_dir_path = Path(output_dir) / test_dir
        test_dir_path.mkdir(parents=True, exist_ok=True)

        # Example test files
        test_files = []

        if test_framework == "jest":
            test_files.extend(
                [
                    "example.test.ts",
                    "utils/__tests__/example-util.test.ts",
                    "setupTests.ts",
                ]
            )
        elif test_framework == "mocha":
            test_files.extend(["example.spec.ts", "test-utils/test-helper.ts"])

        # Generate test files
        for test_file in test_files:
            content = self._render_template(
                f"test/typescript/{test_framework}/{test_file}", variables
            )
            if content:
                file_path = test_dir_path / test_file
                file_path.parent.mkdir(parents=True, exist_ok=True)
                self._write_file(str(file_path), content)
                generated_files.append(str(file_path))

        return generated_files

    def _generate_python_tests(
        self, output_dir: str, variables: dict[str, Any]
    ) -> list[str]:
        """Generate Python test files."""
        generated_files = []
        test_framework = variables.get("test_framework", "pytest")
        test_dir = variables.get("test_dir", "tests")

        # Create test directory structure
        test_dir_path = Path(output_dir) / test_dir
        test_dir_path.mkdir(parents=True, exist_ok=True)

        # Example test files
        test_files = []

        if test_framework == "pytest":
            test_files.extend(
                ["__init__.py", "conftest.py", "test_example.py", "utils/test_utils.py"]
            )
        elif test_framework == "unittest":
            test_files.extend(["__init__.py", "test_example.py", "test_utils.py"])

        # Generate test files
        for test_file in test_files:
            content = self._render_template(
                f"test/python/{test_framework}/{test_file}", variables
            )
            if content:
                file_path = test_dir_path / test_file
                file_path.parent.mkdir(parents=True, exist_ok=True)
                self._write_file(str(file_path), content)
                generated_files.append(str(file_path))

        return generated_files

    def _generate_test_ci_config(
        self, output_dir: str, variables: dict[str, Any]
    ) -> list[str]:
        """Generate CI/CD configuration for running tests."""
        generated_files = []
        ci_provider = variables.get("ci_provider", "github")

        ci_files = []

        if ci_provider == "github":
            ci_files.append(".github/workflows/tests.yml")
        elif ci_provider == "gitlab":
            ci_files.append(".gitlab-ci.yml")

        # Generate CI configuration files
        for ci_file in ci_files:
            content = self._render_template(f"ci/{ci_provider}/{ci_file}", variables)
            if content:
                file_path = Path(output_dir) / ci_file
                file_path.parent.mkdir(parents=True, exist_ok=True)
                self._write_file(str(file_path), content)
                generated_files.append(str(file_path))
        return generated_files
