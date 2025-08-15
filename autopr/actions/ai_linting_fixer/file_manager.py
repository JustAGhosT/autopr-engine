"""
File Manager Module

This module handles file operations, backups, and safe file modifications.
"""

from datetime import UTC, datetime
import logging
import operator
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


class FileManager:
    """Handles file operations and backups."""

    def __init__(self, backup_directory: str | None = None):
        """Initialize the file manager."""
        self.backup_directory = backup_directory or "./backups"
        self._ensure_backup_directory()

    def _ensure_backup_directory(self) -> None:
        """Ensure the backup directory exists."""
        try:
            Path(self.backup_directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning("Failed to create backup directory: %s", e)

    def create_backup(self, file_path: str) -> str | None:
        """Create a backup of a file before modification."""
        try:
            if not Path(self.backup_directory).exists():
                Path(self.backup_directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning("Failed to create backup directory: %s", e)
            return None

        if not Path(file_path).exists():
            logger.warning("File does not exist: %s", file_path)
            return None

        try:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{Path(file_path).stem}.backup_{timestamp}"
            backup_path = Path(self.backup_directory) / backup_filename

            shutil.copy2(file_path, backup_path)
            logger.info("Created backup: %s", backup_path)
            return str(backup_path)

        except Exception as e:
            logger.exception("Failed to create backup for %s: %s", file_path, e)
            return None

    def create_backups(self, file_paths: list) -> int:
        """Create backups for multiple files."""
        successful_backups = 0
        for file_path in file_paths:
            backup_path = self.create_backup(file_path)
            if backup_path:
                successful_backups += 1
        return successful_backups

    def write_file_safely(self, file_path: str, content: str, backup: bool = True) -> bool:
        """Write content to a file with optional backup."""
        backup_path = None
        if backup:
            backup_path = self.create_backup(file_path)

        try:
            with Path(file_path).open("w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Successfully wrote to file: %s", file_path)
            return True

        except Exception as e:
            logger.exception("Failed to write to file %s: %s", file_path, e)

            # Try to restore from backup if available
            if backup_path and Path(backup_path).exists():
                try:
                    shutil.copy2(backup_path, file_path)
                    logger.info("Restored %s from backup after write failure", file_path)
                    return False
                except Exception as restore_error:
                    logger.exception("Failed to restore from backup: %s", restore_error)

            return False

    def restore_from_backup(self, file_path: str, backup_path: str) -> bool:
        """Restore a file from its backup."""
        try:
            if not Path(backup_path).exists():
                logger.error("Backup file does not exist: %s", backup_path)
                return False

            shutil.copy2(backup_path, file_path)
            logger.info("Restored %s from backup: %s", file_path, backup_path)
            return True

        except Exception as e:
            logger.exception("Failed to restore %s from backup %s: %s", file_path, backup_path, e)
            return False

    def read_file_safely(self, file_path: str) -> tuple[bool, str]:
        """Read a file safely and return success status and content."""
        try:
            with Path(file_path).open(encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.exception(f"Failed to read file {file_path}: {e}")
            return False, ""
        else:
            return True, content

    def read_file(self, file_path: str) -> str | None:
        """Read a file and return its content."""
        success, content = self.read_file_safely(file_path)
        return content if success else None

    def write_file(self, file_path: str, content: str) -> bool:
        """Write content to a file."""
        return self.write_file_safely(file_path, content, backup=False)

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        return Path(file_path).exists()

    def get_file_size(self, file_path: str) -> int:
        """Get the size of a file in bytes."""
        try:
            return Path(file_path).stat().st_size
        except Exception as e:
            logger.debug("Failed to get file size for %s: %s", file_path, e)
            return 0

    def get_file_info(self, file_path: str) -> dict:
        """Get comprehensive information about a file."""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {"exists": False}

            stat = file_path_obj.stat()
        except Exception as e:
            logger.debug("Failed to get file info for %s: %s", file_path, e)
            return {"exists": False, "error": str(e)}
        else:
            return {
                "exists": True,
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "modified_time": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                "created_time": datetime.fromtimestamp(stat.st_ctime, tz=UTC).isoformat(),
                "is_file": file_path_obj.is_file(),
                "is_directory": file_path_obj.is_dir(),
                "extension": file_path_obj.suffix,
                "name": file_path_obj.name,
                "stem": file_path_obj.stem,
                "parent": str(file_path_obj.parent),
            }

    def list_backups(self, file_path: str | None = None) -> list:
        """List available backups, optionally filtered by original file."""
        try:
            backup_dir = Path(self.backup_directory)
            if not backup_dir.exists():
                return []

            backups = []
            for backup_file in backup_dir.glob("*.backup_*"):
                backup_info = {
                    "backup_path": str(backup_file),
                    "backup_name": backup_file.name,
                    "size_bytes": backup_file.stat().st_size,
                    "modified_time": datetime.fromtimestamp(
                        backup_file.stat().st_mtime
                    ).isoformat(),
                }

                # Try to extract original filename
                if ".backup_" in backup_file.name:
                    original_name = backup_file.name.split(".backup_")[0]
                    backup_info["original_name"] = original_name

                    # Filter by original file if specified
                    if file_path and not backup_file.name.startswith(Path(file_path).stem):
                        continue

                backups.append(backup_info)

            # Sort by modification time (newest first)
            backups.sort(key=operator.itemgetter("modified_time"), reverse=True)
        except Exception as e:
            logger.exception("Failed to list backups: %s", e)
            return []
        else:
            return backups

    def cleanup_old_backups(self, max_backups: int = 10, older_than_days: int | None = None) -> int:
        """Clean up old backup files."""
        try:
            backups = self.list_backups()
            if len(backups) <= max_backups:
                return 0

            # Remove oldest backups beyond max_backups
            backups_to_remove = backups[max_backups:]

            # Additional filtering by age if specified
            if older_than_days:
                cutoff_time = datetime.now(UTC).timestamp() - (older_than_days * 24 * 60 * 60)
                backups_to_remove = [
                    backup for backup in backups_to_remove
                    if datetime.fromisoformat(backup["modified_time"]).timestamp() < cutoff_time
                ]

            removed_count = 0
            for backup in backups_to_remove:
                try:
                    Path(backup["backup_path"]).unlink()
                    logger.debug("Removed old backup: %s", backup["backup_path"])
                    removed_count += 1
                except Exception as e:
                    logger.warning("Failed to remove backup %s: %s", backup["backup_path"], e)

            logger.info("Cleaned up %d old backup files", removed_count)
            return removed_count

        except Exception as e:
            logger.exception("Failed to cleanup old backups: %s", e)
            return 0

    def validate_file_content(self, content: str) -> dict[str, object]:
        """Validate file content for common issues."""
        validation_result: dict[str, object] = {
            "valid": True,
            "issues": list[str](),
            "warnings": list[str](),
        }

        try:
            # Check for empty content
            if not content.strip():
                warnings_list = validation_result["warnings"]
                self._validate_warnings_list(warnings_list)
                warnings_list.append("File content is empty")

            # Check for encoding issues
            try:
                content.encode("utf-8")
            except UnicodeEncodeError:
                issues_list = validation_result["issues"]
                self._validate_issues_list(issues_list)
                issues_list.append("Content contains invalid UTF-8 characters")
                validation_result["valid"] = False

            # Check for extremely long lines
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if len(line) > 1000:  # Very long lines might indicate issues
                    warnings_list = validation_result["warnings"]
                    self._validate_warnings_list(warnings_list)
                    warnings_list.append(f"Line {i} is very long ({len(line)} characters)")

            # Check for mixed line endings
            if "\r\n" in content and "\n" in content:
                warnings_list = validation_result["warnings"]
                self._validate_warnings_list(warnings_list)
                warnings_list.append("Mixed line endings detected")

            # Check for trailing whitespace
            for i, line in enumerate(lines, 1):
                if line.rstrip() != line:
                    warnings_list = validation_result["warnings"]
                    self._validate_warnings_list(warnings_list)
                    warnings_list.append(f"Line {i} has trailing whitespace")

        except Exception as e:
            issues_list = validation_result["issues"]
            self._validate_issues_list(issues_list)
            issues_list.append(f"Validation error: {e}")
            validation_result["valid"] = False

        return validation_result

    def create_directory_safely(self, directory_path: str) -> bool:
        """Create a directory safely."""
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.exception(f"Failed to create directory {directory_path}: {e}")
            return False

    def copy_file_safely(self, source_path: str, destination_path: str) -> bool:
        """Copy a file safely."""
        try:
            shutil.copy2(source_path, destination_path)
            return True
        except Exception as e:
            logger.exception(f"Failed to copy {source_path} to {destination_path}: {e}")
            return False

    def move_file_safely(self, source_path: str, destination_path: str) -> bool:
        """Move a file safely."""
        try:
            shutil.move(source_path, destination_path)
            return True
        except Exception as e:
            logger.exception(f"Failed to move {source_path} to {destination_path}: {e}")
            return False

    def delete_file(self, file_path: str) -> bool:
        """Delete a file safely."""
        try:
            if not Path(file_path).exists():
                logger.debug("File not found for deletion: %s", file_path)
                return False

            Path(file_path).unlink()
            return True

        except Exception as e:
            logger.exception("Failed to delete file %s: %s", file_path, e)
            return False

    def _validate_warnings_list(self, warnings_list: list) -> None:
        """Validate that warnings_list is a list."""
        if not isinstance(warnings_list, list):
            msg = f"Expected list for warnings_list, got {type(warnings_list).__name__}"
            raise TypeError(msg)

    def _validate_issues_list(self, issues_list: list) -> None:
        """Validate that issues_list is a list."""
        if not isinstance(issues_list, list):
            msg = f"Expected list for issues_list, got {type(issues_list).__name__}"
            raise TypeError(msg)

    def _validate_file_info(self, file_info: dict) -> None:
        """Validate file_info structure."""
        if not isinstance(file_info, dict):
            msg = f"Expected dict for file_info, got {type(file_info).__name__}"
            raise TypeError(msg)

        if "warnings" not in file_info:
            msg = "file_info must contain 'warnings' key"
            raise ValueError(msg)

        if "issues" not in file_info:
            msg = "file_info must contain 'issues' key"
            raise ValueError(msg)

        self._validate_warnings_list(file_info["warnings"])
        self._validate_issues_list(file_info["issues"])

    def _validate_file_info_list(self, file_info_list: list) -> None:
        """Validate that file_info_list is a list of valid file_info dicts."""
        if not isinstance(file_info_list, list):
            msg = f"Expected list for file_info_list, got {type(file_info_list).__name__}"
            raise TypeError(msg)

        for file_info in file_info_list:
            self._validate_file_info(file_info)

    def _validate_file_info_dict(self, file_info_dict: dict) -> None:
        """Validate that file_info_dict is a dict of valid file_info dicts."""
        if not isinstance(file_info_dict, dict):
            msg = f"Expected dict for file_info_dict, got {type(file_info_dict).__name__}"
            raise TypeError(msg)

        for file_info in file_info_dict.values():
            self._validate_file_info(file_info)
