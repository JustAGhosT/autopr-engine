"""
File Manager Module

This module handles file operations, backups, and safe file modifications.
"""

from datetime import datetime
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
            logger.warning(f"Failed to create backup directory: {e}")

    def create_backup(self, file_path: str) -> str:
        """Create a backup of the file before modification."""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.warning(f"File does not exist: {file_path}")
                return ""

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path_obj.stem}.backup_{timestamp}{file_path_obj.suffix}"
            backup_path = Path(self.backup_directory) / backup_name

            # Copy the file
            shutil.copy2(file_path, backup_path)

            logger.info(f"Created backup: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.exception(f"Failed to create backup for {file_path}: {e}")
            return ""

    def create_backups(self, file_paths: list) -> int:
        """Create backups for multiple files."""
        successful_backups = 0
        for file_path in file_paths:
            backup_path = self.create_backup(file_path)
            if backup_path:
                successful_backups += 1
        return successful_backups

    def write_file_safely(self, file_path: str, content: str, backup: bool = True) -> bool:
        """Write content to a file safely with optional backup."""
        try:
            file_path_obj = Path(file_path)

            # Create backup if requested
            backup_path = ""
            if backup and file_path_obj.exists():
                backup_path = self.create_backup(file_path)

            # Write the new content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Successfully wrote to file: {file_path}")
            return True

        except Exception as e:
            logger.exception(f"Failed to write to file {file_path}: {e}")

            # Try to restore from backup if available
            if backup_path and Path(backup_path).exists():
                try:
                    self.restore_from_backup(file_path, backup_path)
                    logger.info(f"Restored {file_path} from backup after write failure")
                except Exception as restore_error:
                    logger.exception(f"Failed to restore from backup: {restore_error}")

            return False

    def restore_from_backup(self, file_path: str, backup_path: str) -> bool:
        """Restore a file from its backup."""
        try:
            if not Path(backup_path).exists():
                logger.error(f"Backup file does not exist: {backup_path}")
                return False

            shutil.copy2(backup_path, file_path)
            logger.info(f"Restored {file_path} from backup: {backup_path}")
            return True

        except Exception as e:
            logger.exception(f"Failed to restore {file_path} from backup {backup_path}: {e}")
            return False

    def read_file_safely(self, file_path: str) -> tuple[bool, str]:
        """Read a file safely and return success status and content."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            return True, content
        except Exception as e:
            logger.exception(f"Failed to read file {file_path}: {e}")
            return False, ""

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
            logger.debug(f"Failed to get file size for {file_path}: {e}")
            return 0

    def get_file_info(self, file_path: str) -> dict:
        """Get comprehensive information about a file."""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {"exists": False}

            stat = file_path_obj.stat()
            return {
                "exists": True,
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "is_file": file_path_obj.is_file(),
                "is_directory": file_path_obj.is_dir(),
                "extension": file_path_obj.suffix,
                "name": file_path_obj.name,
                "stem": file_path_obj.stem,
                "parent": str(file_path_obj.parent),
            }
        except Exception as e:
            logger.debug(f"Failed to get file info for {file_path}: {e}")
            return {"exists": False, "error": str(e)}

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
            return backups

        except Exception as e:
            logger.exception(f"Failed to list backups: {e}")
            return []

    def cleanup_old_backups(self, max_backups: int = 10, older_than_days: int | None = None) -> int:
        """Clean up old backup files."""
        try:
            backups = self.list_backups()
            if len(backups) <= max_backups:
                return 0

            # Remove oldest backups beyond the limit
            backups_to_remove = backups[max_backups:]

            # Additional filtering by age if specified
            if older_than_days:
                cutoff_time = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
                backups_to_remove = [
                    b
                    for b in backups_to_remove
                    if datetime.fromisoformat(b["modified_time"]).timestamp() < cutoff_time
                ]

            removed_count = 0
            for backup in backups_to_remove:
                try:
                    Path(backup["backup_path"]).unlink()
                    removed_count += 1
                    logger.debug(f"Removed old backup: {backup['backup_path']}")
                except Exception as e:
                    logger.warning(f"Failed to remove backup {backup['backup_path']}: {e}")

            logger.info(f"Cleaned up {removed_count} old backup files")
            return removed_count

        except Exception as e:
            logger.exception(f"Failed to cleanup old backups: {e}")
            return 0

    def validate_file_content(self, content: str) -> dict:
        """Validate file content for common issues."""
        validation_result = {"valid": True, "issues": [], "warnings": []}

        try:
            # Check for empty content
            if not content.strip():
                validation_result["warnings"].append("File content is empty")

            # Check for encoding issues
            try:
                content.encode("utf-8")
            except UnicodeEncodeError:
                validation_result["issues"].append("Content contains invalid UTF-8 characters")
                validation_result["valid"] = False

            # Check for extremely long lines
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if len(line) > 1000:  # Very long lines might indicate issues
                    validation_result["warnings"].append(
                        f"Line {i} is very long ({len(line)} characters)"
                    )

            # Check for mixed line endings
            if "\r\n" in content and "\n" in content:
                validation_result["warnings"].append("Mixed line endings detected")

            # Check for trailing whitespace
            for i, line in enumerate(lines, 1):
                if line.rstrip() != line:
                    validation_result["warnings"].append(f"Line {i} has trailing whitespace")

        except Exception as e:
            validation_result["issues"].append(f"Validation error: {e}")
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

    def delete_file_safely(self, file_path: str) -> bool:
        """Delete a file safely."""
        try:
            Path(file_path).unlink()
            return True
        except FileNotFoundError:
            logger.debug(f"File not found for deletion: {file_path}")
            return True  # File doesn't exist, so deletion is successful
        except Exception as e:
            logger.exception(f"Failed to delete {file_path}: {e}")
            return False
