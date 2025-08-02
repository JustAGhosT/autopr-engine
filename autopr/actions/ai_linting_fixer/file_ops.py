"""
File Operations Module

Provides safe file manipulation capabilities with backup, restore, validation,
and atomic operations for the AI linting system.
"""

import ast
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
import shutil
import tempfile
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FileBackup:
    """Represents a file backup with metadata."""

    original_path: str
    backup_path: str
    timestamp: datetime
    file_size: int
    checksum: str
    reason: str = "ai_linting_fix"


class FileValidator:
    """Validates Python file syntax and structure."""

    @staticmethod
    def validate_python_syntax(content: str) -> tuple[bool, str | None]:
        """Validate Python syntax using AST parsing."""
        try:
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            return False, error_msg
        except Exception as e:
            return False, f"Parsing error: {e!s}"

    @staticmethod
    def validate_file_syntax(file_path: str) -> tuple[bool, str | None]:
        """Validate syntax of a Python file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            return FileValidator.validate_python_syntax(content)
        except Exception as e:
            return False, f"File read error: {e!s}"

    @staticmethod
    def check_import_usage(file_content: str, import_line: str) -> bool:
        """Check if an import statement is actually used in the file."""
        try:
            # Extract import name from various import formats
            import_name = FileValidator._extract_import_name(import_line)
            if not import_name:
                return False

            # Check for usage in the file
            lines = file_content.split("\n")
            for line in lines:
                # Skip the import line itself
                if line.strip() == import_line.strip():
                    continue

                # Check for direct usage
                if import_name in line:
                    # Simple heuristic - could be improved with AST analysis
                    return True

            return False

        except Exception as e:
            logger.debug(f"Error checking import usage: {e}")
            return True  # Conservative - assume it's used if we can't determine

    @staticmethod
    def _extract_import_name(import_line: str) -> str | None:
        """Extract the import name from an import statement."""
        import_line = import_line.strip()

        if import_line.startswith("import "):
            # "import module" or "import module as alias"
            parts = import_line.replace("import ", "").split(" as ")
            if len(parts) > 1:
                return parts[1].strip()  # Use alias
            return parts[0].split(".")[0].strip()  # Use first part of module

        if import_line.startswith("from "):
            # "from module import name" or "from module import name as alias"
            try:
                parts = import_line.split(" import ")
                if len(parts) == 2:
                    imported_part = parts[1].strip()
                    if " as " in imported_part:
                        return imported_part.split(" as ")[1].strip()
                    return imported_part.split(",")[0].strip()
            except:
                pass

        return None


class BackupManager:
    """Manages file backups with restore capabilities."""

    def __init__(self, backup_dir: str = ".ai_linting_backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.active_backups: dict[str, FileBackup] = {}

    def create_backup(self, file_path: str, reason: str = "ai_linting_fix") -> FileBackup:
        """Create a backup of the specified file."""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                msg = f"Source file not found: {file_path}"
                raise FileNotFoundError(msg)

            # Generate backup filename with timestamp
            timestamp = datetime.now()
            backup_name = f"{source_path.name}.{timestamp.strftime('%Y%m%d_%H%M%S')}.backup"
            backup_path = self.backup_dir / backup_name

            # Copy file
            shutil.copy2(source_path, backup_path)

            # Calculate checksum (simple)
            checksum = self._calculate_checksum(source_path)

            # Create backup record
            backup = FileBackup(
                original_path=str(source_path),
                backup_path=str(backup_path),
                timestamp=timestamp,
                file_size=source_path.stat().st_size,
                checksum=checksum,
                reason=reason,
            )

            self.active_backups[file_path] = backup
            logger.info(f"Created backup: {file_path} -> {backup_path}")

            return backup

        except Exception as e:
            logger.exception(f"Failed to create backup for {file_path}: {e}")
            raise

    def restore_backup(self, file_path: str) -> bool:
        """Restore a file from its backup."""
        try:
            if file_path not in self.active_backups:
                logger.warning(f"No backup found for {file_path}")
                return False

            backup = self.active_backups[file_path]
            backup_path = Path(backup.backup_path)

            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Restore the file
            shutil.copy2(backup_path, file_path)
            logger.info(f"Restored backup: {backup_path} -> {file_path}")

            return True

        except Exception as e:
            logger.exception(f"Failed to restore backup for {file_path}: {e}")
            return False

    def cleanup_backup(self, file_path: str) -> bool:
        """Remove backup after successful operation."""
        try:
            if file_path not in self.active_backups:
                return True  # Nothing to clean up

            backup = self.active_backups[file_path]
            backup_path = Path(backup.backup_path)

            if backup_path.exists():
                backup_path.unlink()
                logger.debug(f"Cleaned up backup: {backup_path}")

            del self.active_backups[file_path]
            return True

        except Exception as e:
            logger.exception(f"Failed to cleanup backup for {file_path}: {e}")
            return False

    def cleanup_all_backups(self) -> int:
        """Clean up all active backups."""
        cleanup_count = 0
        for file_path in list(self.active_backups.keys()):
            if self.cleanup_backup(file_path):
                cleanup_count += 1
        return cleanup_count

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate a simple checksum for the file."""
        try:
            import hashlib

            with open(file_path, "rb") as f:
                content = f.read()
            return hashlib.md5(content, usedforsecurity=False).hexdigest()
        except:
            return ""


class SafeFileOperations:
    """Provides safe file operations with validation and rollback capabilities."""

    def __init__(self, backup_manager: BackupManager = None):
        self.backup_manager = backup_manager or BackupManager()
        self.validator = FileValidator()
        self.temp_files: list[str] = []

    @contextmanager
    def safe_file_operation(self, file_path: str, create_backup: bool = True):
        """Context manager for safe file operations with automatic rollback on failure."""
        backup = None
        original_valid = False

        try:
            # Validate original file
            if Path(file_path).exists():
                original_valid, _ = self.validator.validate_file_syntax(file_path)
                if not original_valid:
                    logger.warning(f"Original file has syntax errors: {file_path}")

            # Create backup if requested
            if create_backup and Path(file_path).exists():
                backup = self.backup_manager.create_backup(file_path)

            # Yield control to the operation
            yield

            # Validate modified file
            if Path(file_path).exists():
                modified_valid, error = self.validator.validate_file_syntax(file_path)
                if not modified_valid:
                    msg = f"Modified file has syntax errors: {error}"
                    raise ValueError(msg)

            # Clean up backup on success
            if backup and create_backup:
                self.backup_manager.cleanup_backup(file_path)

        except Exception as e:
            logger.exception(f"Safe file operation failed for {file_path}: {e}")

            # Restore from backup if available
            if backup and create_backup:
                restore_success = self.backup_manager.restore_backup(file_path)
                if restore_success:
                    logger.info(f"Restored file from backup: {file_path}")
                else:
                    logger.exception(f"Failed to restore backup for {file_path}")

            raise

    def write_file_safely(
        self, file_path: str, content: str, validate_syntax: bool = True, create_backup: bool = True
    ) -> bool:
        """Write content to a file safely with validation and backup."""
        try:
            # Pre-validate content syntax
            if validate_syntax:
                is_valid, error = self.validator.validate_python_syntax(content)
                if not is_valid:
                    logger.error(f"Content has syntax errors: {error}")
                    return False

            with self.safe_file_operation(file_path, create_backup):
                # Write to temporary file first
                temp_file = self._create_temp_file(content)

                # Atomic move to target location
                shutil.move(temp_file, file_path)

                logger.debug(f"Successfully wrote file: {file_path}")

            return True

        except Exception as e:
            logger.exception(f"Failed to write file {file_path}: {e}")
            return False

    def apply_fixes_to_file(
        self, file_path: str, fixes: list[dict[str, Any]], validate_each_fix: bool = True
    ) -> tuple[bool, list[str]]:
        """Apply multiple fixes to a file safely."""
        try:
            # Read original content
            with open(file_path, encoding="utf-8") as f:
                original_content = f.read()

            current_content = original_content
            applied_fixes = []

            with self.safe_file_operation(file_path, create_backup=True):
                for i, fix in enumerate(fixes):
                    try:
                        # Apply the fix
                        new_content = self._apply_single_fix(current_content, fix)

                        # Validate intermediate result if requested
                        if validate_each_fix:
                            is_valid, error = self.validator.validate_python_syntax(new_content)
                            if not is_valid:
                                logger.warning(f"Fix {i + 1} introduces syntax error: {error}")
                                continue  # Skip this fix

                        current_content = new_content
                        applied_fixes.append(f"Fix {i + 1}: {fix.get('description', 'Applied')}")

                    except Exception as e:
                        logger.warning(f"Failed to apply fix {i + 1}: {e}")
                        continue

                # Write final result
                if current_content != original_content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(current_content)

            return True, applied_fixes

        except Exception as e:
            logger.exception(f"Failed to apply fixes to {file_path}: {e}")
            return False, []

    def _apply_single_fix(self, content: str, fix: dict[str, Any]) -> str:
        """Apply a single fix to content."""
        # This is a simplified implementation
        # In practice, this would use more sophisticated logic
        # based on the fix type and target location

        fix_type = fix.get("type", "replace")

        if fix_type == "replace":
            old_text = fix.get("old_text", "")
            new_text = fix.get("new_text", "")
            return content.replace(old_text, new_text, 1)

        if fix_type == "line_replace":
            lines = content.split("\n")
            line_number = fix.get("line_number", 1) - 1  # Convert to 0-based
            if 0 <= line_number < len(lines):
                lines[line_number] = fix.get("new_line", "")
                return "\n".join(lines)

        return content

    def _create_temp_file(self, content: str) -> str:
        """Create a temporary file with the given content."""
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".py", encoding="utf-8"
            ) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            self.temp_files.append(temp_file_path)
            return temp_file_path

        except Exception as e:
            logger.exception(f"Failed to create temporary file: {e}")
            raise

    def cleanup_temp_files(self):
        """Clean up all temporary files."""
        for temp_file in self.temp_files:
            try:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
            except Exception as e:
                logger.debug(f"Failed to cleanup temp file {temp_file}: {e}")

        self.temp_files.clear()

    def get_file_info(self, file_path: str) -> dict[str, Any]:
        """Get comprehensive information about a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"exists": False}

            stat = path.stat()

            # Read content for analysis
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Validate syntax
            is_valid, syntax_error = self.validator.validate_python_syntax(content)

            # Calculate complexity (simple metric)
            complexity = self._calculate_complexity(content)

            return {
                "exists": True,
                "path": str(path.absolute()),
                "size_bytes": stat.st_size,
                "size_lines": len(content.splitlines()),
                "last_modified": datetime.fromtimestamp(stat.st_mtime),
                "is_syntax_valid": is_valid,
                "syntax_error": syntax_error,
                "complexity_score": complexity,
                "encoding": "utf-8",  # Assumed
            }

        except Exception as e:
            logger.exception(f"Failed to get file info for {file_path}: {e}")
            return {"exists": False, "error": str(e)}

    def _calculate_complexity(self, content: str) -> float:
        """Calculate a simple complexity score for the file."""
        try:
            lines = content.splitlines()
            non_empty_lines = [line for line in lines if line.strip()]

            # Simple complexity metrics
            total_lines = len(non_empty_lines)
            function_count = sum(1 for line in lines if line.strip().startswith("def "))
            class_count = sum(1 for line in lines if line.strip().startswith("class "))
            import_count = sum(1 for line in lines if line.strip().startswith(("import ", "from ")))

            # Calculate score (arbitrary formula)
            complexity = (
                total_lines * 0.1 + function_count * 2 + class_count * 3 + import_count * 0.5
            )

            return round(complexity, 2)

        except:
            return 0.0


class DryRunOperations:
    """Provides dry-run capabilities for file operations."""

    def __init__(self):
        self.planned_operations: list[dict[str, Any]] = []
        self.validator = FileValidator()

    def plan_file_write(
        self, file_path: str, content: str, reason: str = "AI fix"
    ) -> dict[str, Any]:
        """Plan a file write operation for dry-run mode."""
        operation = {
            "type": "file_write",
            "file_path": file_path,
            "reason": reason,
            "timestamp": datetime.now(),
            "content_preview": content[:200] + "..." if len(content) > 200 else content,
            "content_size": len(content),
            "content_lines": len(content.splitlines()),
        }

        # Validate syntax
        is_valid, error = self.validator.validate_python_syntax(content)
        operation["syntax_valid"] = is_valid
        operation["syntax_error"] = error

        # Check if file exists
        path = Path(file_path)
        operation["file_exists"] = path.exists()
        if path.exists():
            operation["original_size"] = path.stat().st_size

        self.planned_operations.append(operation)
        return operation

    def plan_backup_creation(self, file_path: str, reason: str = "safety") -> dict[str, Any]:
        """Plan a backup creation for dry-run mode."""
        operation = {
            "type": "backup_creation",
            "file_path": file_path,
            "reason": reason,
            "timestamp": datetime.now(),
        }

        path = Path(file_path)
        if path.exists():
            operation["file_size"] = path.stat().st_size
            operation["backup_name"] = (
                f"{path.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
            )
        else:
            operation["error"] = "File does not exist"

        self.planned_operations.append(operation)
        return operation

    def get_planned_operations(self) -> list[dict[str, Any]]:
        """Get all planned operations."""
        return self.planned_operations.copy()

    def clear_planned_operations(self):
        """Clear all planned operations."""
        self.planned_operations.clear()

    def get_operation_summary(self) -> dict[str, Any]:
        """Get a summary of planned operations."""
        if not self.planned_operations:
            return {"total_operations": 0}

        summary = {
            "total_operations": len(self.planned_operations),
            "file_writes": 0,
            "backup_creations": 0,
            "files_affected": set(),
            "syntax_errors": 0,
            "total_content_size": 0,
        }

        for op in self.planned_operations:
            if op["type"] == "file_write":
                summary["file_writes"] += 1
                summary["total_content_size"] += op.get("content_size", 0)
                if not op.get("syntax_valid", True):
                    summary["syntax_errors"] += 1
            elif op["type"] == "backup_creation":
                summary["backup_creations"] += 1

            summary["files_affected"].add(op["file_path"])

        summary["files_affected"] = len(summary["files_affected"])
        return summary


# Global instances
backup_manager = BackupManager()
safe_file_ops = SafeFileOperations(backup_manager)
dry_run_ops = DryRunOperations()
