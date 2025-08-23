"""
Validation Manager Module

Manages validation phases and rollback decisions for AI fixes.
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


class ValidationResult(Enum):
    """Validation result types."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationCheck:
    """Individual validation check result."""

    check_name: str
    result: ValidationResult
    message: str
    details: dict[str, Any]
    execution_time: float


@dataclass
class ValidationConfig:
    """Configuration for validation phases."""

    max_validation_rounds: int = 3
    enable_syntax_check: bool = True
    enable_linting_check: bool = True
    enable_test_validation: bool = True
    enable_import_validation: bool = True
    rollback_on_syntax_error: bool = True
    rollback_on_test_failure: bool = False
    rollback_on_import_error: bool = True
    rollback_threshold: float = 0.5  # Rollback if validation score < threshold


class ValidationManager:
    """Manages validation phases and rollback decisions."""

    def __init__(self, config: ValidationConfig | None = None):
        """Initialize the validation manager."""
        self.config = config or ValidationConfig()
        self.validation_history: list[dict[str, Any]] = []

    def validate_file_fix(
        self,
        file_path: str,
        original_content: str,
        fixed_content: str,
        issue_codes: list[str],
    ) -> tuple[bool, list[ValidationCheck]]:
        """Validate a file fix and return whether it should be kept."""
        checks = []

        # 1. Syntax validation
        if self.config.enable_syntax_check:
            syntax_check = self._validate_python_syntax(file_path, fixed_content)
            checks.append(syntax_check)

            if (
                syntax_check.result == ValidationResult.FAILED
                and self.config.rollback_on_syntax_error
            ):
                logger.warning(
                    f"Syntax error detected, recommending rollback for {file_path}"
                )
                return False, checks

        # 2. Import validation
        if self.config.enable_import_validation:
            import_check = self._validate_imports(file_path, fixed_content)
            checks.append(import_check)

            if (
                import_check.result == ValidationResult.FAILED
                and self.config.rollback_on_import_error
            ):
                logger.warning(
                    f"Import error detected, recommending rollback for {file_path}"
                )
                return False, checks

        # 3. Linting validation (check if issues were actually fixed)
        if self.config.enable_linting_check:
            linting_check = self._validate_linting_improvements(
                file_path, original_content, fixed_content, issue_codes
            )
            checks.append(linting_check)

        # 4. Test validation (if tests exist)
        if self.config.enable_test_validation:
            test_check = self._validate_tests(file_path)
            checks.append(test_check)

            if (
                test_check.result == ValidationResult.FAILED
                and self.config.rollback_on_test_failure
            ):
                logger.warning(
                    f"Test failure detected, recommending rollback for {file_path}"
                )
                return False, checks

        # Calculate overall validation score
        passed_checks = sum(
            1 for check in checks if check.result == ValidationResult.PASSED
        )
        total_checks = len([c for c in checks if c.result != ValidationResult.SKIPPED])

        if total_checks == 0:
            validation_score = 1.0  # No checks ran, assume success
        else:
            validation_score = passed_checks / total_checks

        # Record validation
        validation_record = {
            "file_path": file_path,
            "validation_score": validation_score,
            "checks": [
                {
                    "name": check.check_name,
                    "result": check.result.value,
                    "message": check.message,
                    "execution_time": check.execution_time,
                }
                for check in checks
            ],
            "recommended_action": (
                "keep"
                if validation_score >= self.config.rollback_threshold
                else "rollback"
            ),
        }
        self.validation_history.append(validation_record)

        # Decision
        should_keep = validation_score >= self.config.rollback_threshold

        logger.info(
            f"Validation for {file_path}: score={validation_score:.2f}, "
            f"action={'keep' if should_keep else 'rollback'}"
        )

        return should_keep, checks

    def _validate_python_syntax(self, file_path: str, content: str) -> ValidationCheck:
        """Validate Python syntax."""
        import time

        start_time = time.time()

        try:
            ast.parse(content)
            return ValidationCheck(
                check_name="syntax_check",
                result=ValidationResult.PASSED,
                message="Python syntax is valid",
                details={"file_path": file_path},
                execution_time=time.time() - start_time,
            )
        except SyntaxError as e:
            return ValidationCheck(
                check_name="syntax_check",
                result=ValidationResult.FAILED,
                message=f"Syntax error: {e.msg} at line {e.lineno}",
                details={
                    "file_path": file_path,
                    "error_line": e.lineno,
                    "error_offset": e.offset,
                    "error_text": e.text,
                },
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            return ValidationCheck(
                check_name="syntax_check",
                result=ValidationResult.FAILED,
                message=f"Unexpected error during syntax check: {e}",
                details={"file_path": file_path, "error": str(e)},
                execution_time=time.time() - start_time,
            )

    def _validate_imports(self, file_path: str, content: str) -> ValidationCheck:
        """Validate that imports work correctly."""
        import time

        start_time = time.time()
        temp_file_path = None

        try:
            # Create a temporary file to test imports
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            # Try to compile the file to check imports
            result = subprocess.run(
                ["python", "-m", "py_compile", temp_file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return ValidationCheck(
                    check_name="import_check",
                    result=ValidationResult.PASSED,
                    message="All imports are valid",
                    details={"file_path": file_path},
                    execution_time=time.time() - start_time,
                )
            else:
                return ValidationCheck(
                    check_name="import_check",
                    result=ValidationResult.FAILED,
                    message=f"Import error: {result.stderr}",
                    details={
                        "file_path": file_path,
                        "stderr": result.stderr,
                        "stdout": result.stdout,
                    },
                    execution_time=time.time() - start_time,
                )

        except subprocess.TimeoutExpired:
            return ValidationCheck(
                check_name="import_check",
                result=ValidationResult.WARNING,
                message="Import check timed out",
                details={"file_path": file_path},
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            return ValidationCheck(
                check_name="import_check",
                result=ValidationResult.WARNING,
                message=f"Import check failed: {e}",
                details={"file_path": file_path, "error": str(e)},
                execution_time=time.time() - start_time,
            )
        finally:
            # Clean up temporary files
            if temp_file_path:
                Path(temp_file_path).unlink(missing_ok=True)
                Path(temp_file_path + "c").unlink(missing_ok=True)  # Remove .pyc file
                # Also clean up __pycache__ directory if created
                pycache_dir = Path(temp_file_path).parent / "__pycache__"
                if pycache_dir.exists():
                    import shutil

                    shutil.rmtree(pycache_dir, ignore_errors=True)

    def _validate_linting_improvements(
        self,
        file_path: str,
        original_content: str,
        fixed_content: str,
        target_issue_codes: list[str],
    ) -> ValidationCheck:
        """Validate that the linting issues were actually improved."""
        import time

        start_time = time.time()

        try:
            # Run ruff on both versions to compare
            original_issues = self._get_ruff_issues(original_content)
            fixed_issues = self._get_ruff_issues(fixed_content)

            # Filter to target issue codes
            original_target_issues = [
                issue
                for issue in original_issues
                if any(issue.startswith(code) for code in target_issue_codes)
            ]
            fixed_target_issues = [
                issue
                for issue in fixed_issues
                if any(issue.startswith(code) for code in target_issue_codes)
            ]

            # Calculate improvement
            issues_fixed = len(original_target_issues) - len(fixed_target_issues)
            new_issues = len(fixed_issues) - len(original_issues)

            if issues_fixed > 0 and new_issues <= 2:  # Allow up to 2 new minor issues
                result = ValidationResult.PASSED
                message = (
                    f"Fixed {issues_fixed} issues, {new_issues} new issues introduced"
                )
            elif issues_fixed == 0 and new_issues == 0:
                result = ValidationResult.WARNING
                message = "No issues fixed, but no new issues introduced"
            else:
                result = ValidationResult.WARNING
                message = f"Fixed {issues_fixed} issues, but {new_issues} new issues introduced"

            return ValidationCheck(
                check_name="linting_improvement",
                result=result,
                message=message,
                details={
                    "file_path": file_path,
                    "original_issues": len(original_issues),
                    "fixed_issues": len(fixed_issues),
                    "target_issues_fixed": issues_fixed,
                    "new_issues": new_issues,
                    "target_codes": target_issue_codes,
                },
                execution_time=time.time() - start_time,
            )

        except Exception as e:
            return ValidationCheck(
                check_name="linting_improvement",
                result=ValidationResult.WARNING,
                message=f"Could not validate linting improvements: {e}",
                details={"file_path": file_path, "error": str(e)},
                execution_time=time.time() - start_time,
            )

    def _get_ruff_issues(self, content: str) -> list[str]:
        """Get ruff issues for content."""
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            result = subprocess.run(
                ["ruff", "check", temp_file_path, "--output-format=text"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Parse ruff output
            issues = []
            for line in result.stdout.splitlines():
                if temp_file_path in line and ":" in line:
                    # Extract error code from line like "temp.py:1:1: E501 Line too long"
                    parts = line.split(":")
                    if len(parts) >= 4:
                        error_part = parts[3].strip()
                        if " " in error_part:
                            error_code = error_part.split()[0]
                            issues.append(error_code)

            return issues

        except Exception as e:
            logger.warning(f"Failed to get ruff issues: {e}")
            return []
        finally:
            # Clean up temporary file
            if temp_file_path:
                Path(temp_file_path).unlink(missing_ok=True)

    def _validate_tests(self, file_path: str) -> ValidationCheck:
        """Validate that tests still pass for the file."""
        import time

        start_time = time.time()

        try:
            # Look for test files
            file_path_obj = Path(file_path)
            test_files = self._find_test_files(file_path_obj)

            if not test_files:
                return ValidationCheck(
                    check_name="test_validation",
                    result=ValidationResult.SKIPPED,
                    message="No test files found",
                    details={"file_path": file_path},
                    execution_time=time.time() - start_time,
                )

            # Run tests
            failed_tests = []
            for test_file in test_files:
                try:
                    result = subprocess.run(
                        ["python", "-m", "pytest", str(test_file), "-v"],
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )
                    if result.returncode != 0:
                        failed_tests.append(str(test_file))
                except subprocess.TimeoutExpired:
                    failed_tests.append(f"{test_file} (timeout)")

            if not failed_tests:
                return ValidationCheck(
                    check_name="test_validation",
                    result=ValidationResult.PASSED,
                    message=f"All {len(test_files)} test files passed",
                    details={
                        "file_path": file_path,
                        "test_files": [str(f) for f in test_files],
                    },
                    execution_time=time.time() - start_time,
                )
            else:
                return ValidationCheck(
                    check_name="test_validation",
                    result=ValidationResult.FAILED,
                    message=f"{len(failed_tests)} test files failed",
                    details={
                        "file_path": file_path,
                        "failed_tests": failed_tests,
                        "total_tests": len(test_files),
                    },
                    execution_time=time.time() - start_time,
                )

        except Exception as e:
            return ValidationCheck(
                check_name="test_validation",
                result=ValidationResult.WARNING,
                message=f"Test validation failed: {e}",
                details={"file_path": file_path, "error": str(e)},
                execution_time=time.time() - start_time,
            )

    def _find_test_files(self, file_path: Path) -> list[Path]:
        """Find test files related to the given file."""
        test_files = []

        # Common test patterns
        test_patterns = [
            f"test_{file_path.stem}.py",
            f"{file_path.stem}_test.py",
            f"test_{file_path.stem}s.py",  # plural
        ]

        # Look in common test directories
        test_dirs = [
            file_path.parent / "tests",
            file_path.parent / "test",
            file_path.parent.parent / "tests",
            file_path.parent.parent / "test",
        ]

        for test_dir in test_dirs:
            if test_dir.exists() and test_dir.is_dir():
                for pattern in test_patterns:
                    test_file = test_dir / pattern
                    if test_file.exists():
                        test_files.append(test_file)

                # Also look for test files that import the module
                for test_file in test_dir.glob("test_*.py"):
                    try:
                        with open(test_file, encoding="utf-8") as f:
                            content = f.read()
                            if file_path.stem in content:
                                test_files.append(test_file)
                    except Exception:
                        continue

        return list(set(test_files))  # Remove duplicates

    def get_validation_stats(self) -> dict[str, Any]:
        """Get validation statistics."""
        if not self.validation_history:
            return {}

        total_validations = len(self.validation_history)
        kept_fixes = sum(
            1 for v in self.validation_history if v["recommended_action"] == "keep"
        )
        avg_score = (
            sum(v["validation_score"] for v in self.validation_history)
            / total_validations
        )

        check_stats = {}
        for validation in self.validation_history:
            for check in validation["checks"]:
                check_name = check["name"]
                if check_name not in check_stats:
                    check_stats[check_name] = {
                        "passed": 0,
                        "failed": 0,
                        "warning": 0,
                        "skipped": 0,
                    }
                check_stats[check_name][check["result"]] += 1

        return {
            "total_validations": total_validations,
            "fixes_kept": kept_fixes,
            "fixes_rolled_back": total_validations - kept_fixes,
            "keep_rate": kept_fixes / total_validations if total_validations > 0 else 0,
            "average_validation_score": avg_score,
            "check_statistics": check_stats,
        }
