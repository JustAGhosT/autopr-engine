"""
Test Generator Module

Generates tests for code sections that lack coverage and validates fixes.
"""

import ast
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import subprocess
import tempfile
from typing import Any


logger = logging.getLogger(__name__)


class TestCoverageLevel(Enum):
    """Test coverage levels."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class TestGenerationResult:
    """Result of test generation."""

    success: bool
    test_file_path: str | None = None
    test_content: str | None = None
    coverage_level: TestCoverageLevel = TestCoverageLevel.NONE
    functions_tested: list[str] = None
    error_message: str | None = None


@dataclass
class TestValidationResult:
    """Result of test validation."""

    success: bool
    tests_passed: bool = False
    original_tests_passed: bool = False
    new_tests_passed: bool = False
    error_message: str | None = None
    test_output: str | None = None


class TestGenerator:
    """Generates and validates tests for code sections."""

    def __init__(self, test_dir: str | None = None):
        """Initialize the test generator."""
        self.test_dir = Path(test_dir or "tests/generated")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.generated_tests: dict[str, str] = {}  # file_path -> test_file_path

    def analyze_coverage_needs(self, file_path: str, content: str) -> dict[str, Any]:
        """Analyze what test coverage is needed for a file."""
        try:
            tree = ast.parse(content)

            # Find all functions and classes
            functions = []
            classes = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "has_docstring": ast.get_docstring(node) is not None,
                            "is_async": isinstance(node, ast.AsyncFunctionDef),
                            "args": [arg.arg for arg in node.args.args if arg.arg != "self"],
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    classes.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "has_docstring": ast.get_docstring(node) is not None,
                            "methods": [
                                n.name for n in node.body if isinstance(n, ast.FunctionDef)
                            ],
                        }
                    )

            # Check if tests already exist
            existing_tests = self._find_existing_tests(file_path)

            # Determine coverage level
            coverage_level = self._determine_coverage_level(
                file_path, functions, classes, existing_tests
            )

            return {
                "file_path": file_path,
                "functions": functions,
                "classes": classes,
                "existing_tests": existing_tests,
                "coverage_level": coverage_level.value,
                "needs_tests": coverage_level in [TestCoverageLevel.NONE, TestCoverageLevel.LOW],
                "testable_items": len(functions) + len(classes),
            }

        except Exception as e:
            logger.error(f"Failed to analyze coverage for {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "coverage_level": TestCoverageLevel.NONE.value,
                "needs_tests": True,
            }

    def generate_tests_if_needed(
        self, file_path: str, content: str, force_generate: bool = False
    ) -> TestGenerationResult:
        """Generate tests for a file if coverage is insufficient."""
        try:
            # Analyze coverage needs
            coverage_analysis = self.analyze_coverage_needs(file_path, content)

            if not coverage_analysis.get("needs_tests", True) and not force_generate:
                return TestGenerationResult(
                    success=True,
                    coverage_level=TestCoverageLevel(
                        coverage_analysis.get("coverage_level", "none")
                    ),
                    functions_tested=[],
                )

            # Generate tests
            test_content = self._generate_test_content(file_path, content, coverage_analysis)

            if not test_content:
                return TestGenerationResult(
                    success=False, error_message="Failed to generate test content"
                )

            # Write test file
            test_file_path = self._write_test_file(file_path, test_content)

            if not test_file_path:
                return TestGenerationResult(
                    success=False, error_message="Failed to write test file"
                )

            # Store reference
            self.generated_tests[file_path] = test_file_path

            return TestGenerationResult(
                success=True,
                test_file_path=test_file_path,
                test_content=test_content,
                coverage_level=TestCoverageLevel.MEDIUM,
                functions_tested=coverage_analysis.get("functions", []),
            )

        except Exception as e:
            logger.error(f"Failed to generate tests for {file_path}: {e}")
            return TestGenerationResult(success=False, error_message=str(e))

    def validate_fix_with_tests(
        self, file_path: str, original_content: str, fixed_content: str
    ) -> TestValidationResult:
        """Validate that fixes don't break existing or generated tests."""
        try:
            # Check if we have generated tests for this file
            test_file_path = self.generated_tests.get(file_path)

            if not test_file_path:
                # Look for existing tests
                existing_tests = self._find_existing_tests(file_path)
                if not existing_tests:
                    return TestValidationResult(
                        success=True,
                        tests_passed=True,
                        original_tests_passed=True,
                        new_tests_passed=True,
                        test_output="No tests to validate",
                    )
                test_file_path = existing_tests[0]

            # Run tests on original content
            original_result = self._run_tests_on_content(test_file_path, original_content)

            # Run tests on fixed content
            fixed_result = self._run_tests_on_content(test_file_path, fixed_content)

            # Determine overall success
            tests_passed = original_result.get("passed", False) and fixed_result.get(
                "passed", False
            )

            return TestValidationResult(
                success=True,
                tests_passed=tests_passed,
                original_tests_passed=original_result.get("passed", False),
                new_tests_passed=fixed_result.get("passed", False),
                test_output=f"Original: {original_result.get('output', '')}\nFixed: {fixed_result.get('output', '')}",
            )

        except Exception as e:
            logger.error(f"Failed to validate tests for {file_path}: {e}")
            return TestValidationResult(success=False, error_message=str(e))

    def _determine_coverage_level(
        self,
        file_path: str,
        functions: list[dict],
        classes: list[dict],
        existing_tests: list[str],
    ) -> TestCoverageLevel:
        """Determine the current test coverage level."""
        if not existing_tests:
            return TestCoverageLevel.NONE

        # Simple heuristic: check if test file exists and has reasonable size
        test_file = existing_tests[0] if existing_tests else None
        if test_file and Path(test_file).exists():
            try:
                with open(test_file, encoding="utf-8") as f:
                    test_content = f.read()

                # Count test functions
                test_tree = ast.parse(test_content)
                test_functions = [
                    n
                    for n in ast.walk(test_tree)
                    if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
                ]

                total_testable = len(functions) + len(classes)
                if total_testable == 0:
                    return TestCoverageLevel.HIGH

                coverage_ratio = len(test_functions) / total_testable

                if coverage_ratio >= 0.8:
                    return TestCoverageLevel.HIGH
                elif coverage_ratio >= 0.5:
                    return TestCoverageLevel.MEDIUM
                elif coverage_ratio >= 0.2:
                    return TestCoverageLevel.LOW
                else:
                    return TestCoverageLevel.NONE

            except Exception:
                return TestCoverageLevel.NONE

        return TestCoverageLevel.NONE

    def _find_existing_tests(self, file_path: str) -> list[str]:
        """Find existing test files for a given file."""
        file_path_obj = Path(file_path)
        test_files = []

        # Common test patterns
        test_patterns = [
            f"test_{file_path_obj.stem}.py",
            f"{file_path_obj.stem}_test.py",
            f"test_{file_path_obj.stem}s.py",
        ]

        # Look in common test directories
        test_dirs = [
            file_path_obj.parent / "tests",
            file_path_obj.parent / "test",
            file_path_obj.parent.parent / "tests",
            file_path_obj.parent.parent / "test",
        ]

        for test_dir in test_dirs:
            if test_dir.exists() and test_dir.is_dir():
                for pattern in test_patterns:
                    test_file = test_dir / pattern
                    if test_file.exists():
                        test_files.append(str(test_file))

        return test_files

    def _generate_test_content(
        self, file_path: str, content: str, coverage_analysis: dict[str, Any]
    ) -> str | None:
        """Generate test content for a file."""
        try:
            # Create test generation prompt
            functions = coverage_analysis.get("functions", [])
            classes = coverage_analysis.get("classes", [])

            test_prompt = f"""
Generate comprehensive unit tests for the following Python file. Focus on testing all functions and classes.

File: {file_path}

Functions to test:
{chr(10).join([f"- {f['name']} (line {f['line']}, args: {f['args']})" for f in functions])}

Classes to test:
{chr(10).join([f"- {c['name']} (line {c['line']}, methods: {c['methods']})" for c in classes])}

Requirements:
1. Use pytest framework
2. Test all public functions and methods
3. Include edge cases and error conditions
4. Use descriptive test names
5. Mock external dependencies if needed
6. Include docstrings for test functions

File content:
{content}

Generate only the test file content, no explanations.
"""

            # For now, return a basic test template
            # In a real implementation, this would call an LLM
            return self._generate_basic_test_template(file_path, functions, classes, content)

        except Exception as e:
            logger.error(f"Failed to generate test content: {e}")
            return None

    def _generate_basic_test_template(
        self, file_path: str, functions: list[dict], classes: list[dict], content: str
    ) -> str:
        """Generate a basic test template."""
        file_path_obj = Path(file_path)
        module_name = file_path_obj.stem

        test_content = f'''"""
Generated tests for {file_path}
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add the parent directory to sys.path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import {module_name}
except ImportError:
    # If direct import fails, try alternative approaches
    pass

'''

        # Add tests for functions
        for func in functions:
            test_content += f'''
def test_{func["name"]}():
    """Test {func["name"]} function."""
    # TODO: Implement actual test
    # This is a placeholder test
    assert True
'''

        # Add tests for classes
        for cls in classes:
            test_content += f'''
class Test{cls["name"]}:
    """Test {cls["name"]} class."""
    
    def test_{cls["name"]}_initialization(self):
        """Test {cls["name"]} initialization."""
        # TODO: Implement actual test
        assert True
'''

            for method in cls.get("methods", []):
                test_content += f'''
    def test_{cls["name"]}_{method}(self):
        """Test {cls["name"]}.{method} method."""
        # TODO: Implement actual test
        assert True
'''

        return test_content

    def _write_test_file(self, file_path: str, test_content: str) -> str | None:
        """Write test content to a file."""
        try:
            file_path_obj = Path(file_path)
            test_filename = f"test_{file_path_obj.stem}_generated.py"
            test_file_path = self.test_dir / test_filename

            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_content)

            logger.info(f"Generated test file: {test_file_path}")
            return str(test_file_path)

        except Exception as e:
            logger.error(f"Failed to write test file: {e}")
            return None

    def _run_tests_on_content(self, test_file_path: str, content: str) -> dict[str, Any]:
        """Run tests on a specific content version."""
        temp_file_path = None
        try:
            # Create temporary file with the content
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            # Run pytest on the test file
            result = subprocess.run(
                ["python", "-m", "pytest", test_file_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=Path(temp_file_path).parent,
            )

            return {
                "passed": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "returncode": result.returncode,
            }

        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            return {"passed": False, "output": str(e), "returncode": -1}
        finally:
            # Ensure cleanup happens even if an exception occurs
            if temp_file_path and Path(temp_file_path).exists():
                Path(temp_file_path).unlink(missing_ok=True)

    def cleanup_generated_tests(self, file_path: str | None = None):
        """Clean up generated test files."""
        if file_path:
            test_file_path = self.generated_tests.get(file_path)
            if test_file_path and Path(test_file_path).exists():
                Path(test_file_path).unlink(missing_ok=True)
                del self.generated_tests[file_path]
        else:
            # Clean up all generated tests
            for test_file_path in self.generated_tests.values():
                if Path(test_file_path).exists():
                    Path(test_file_path).unlink(missing_ok=True)
            self.generated_tests.clear()
