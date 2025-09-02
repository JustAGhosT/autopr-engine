"""
File Persistence Module

Handles atomic file operations and persistence following the Single Responsibility Principle.
"""

from contextlib import suppress
import logging
import os
from pathlib import Path
from typing import Any

from autopr.actions.ai_linting_fixer.backup_manager import BackupManager


logger = logging.getLogger(__name__)


class FilePersistenceManager:
    """Manages file persistence with atomic operations and backup support."""

    def __init__(self, backup_manager: BackupManager | None = None):
        """Initialize the file persistence manager.

        Args:
            backup_manager: Optional backup manager for file operations
        """
        self.backup_manager = backup_manager or BackupManager()

    async def persist_fix(
        self,
        file_path: str,
        content: str,
        session_id: str | None = None,
        create_backup: bool = True,
    ) -> dict[str, Any]:
        """Persist a fix to disk with atomic operations.

        Args:
            file_path: Path to the file to update
            content: Content to write
            session_id: Session ID for backup management
            create_backup: Whether to create a backup before writing

        Returns:
            Result dictionary with success status and details
        """
        backup = None
        write_success = True
        rollback_performed = False

        try:
            # Create backup if requested
            if create_backup:
                current_session_id = session_id or "default"
                if current_session_id not in self.backup_manager.sessions:
                    self.backup_manager.start_session(current_session_id)

                backup = self.backup_manager.backup_file(file_path, current_session_id)
                if not backup:
                    logger.error("Failed to create backup for %s", file_path)
                    return {
                        "write_success": False,
                        "backup_created": False,
                        "rollback_performed": False,
                        "error": "Backup creation failed",
                    }

            # Perform atomic write
            write_success = await self._atomic_write(file_path, content)

            if not write_success and backup:
                # Rollback on write failure
                logger.info("Write failed, rolling back %s", file_path)
                rollback_success = self.backup_manager.restore_file(
                    file_path, session_id or "default"
                )
                rollback_performed = rollback_success

                if not rollback_success:
                    logger.error("Rollback failed for %s", file_path)

        except Exception as e:
            logger.exception("Error during file persistence for %s", file_path)
            return {
                "write_success": False,
                "backup_created": backup is not None,
                "rollback_performed": False,
                "error": str(e),
            }
        else:
            return {
                "write_success": write_success,
                "backup_created": backup is not None,
                "rollback_performed": rollback_performed,
            }

    async def _atomic_write(self, file_path: str, content: str) -> bool:
        """Perform atomic file write using temp file + rename with proper fsync.

        Args:
            file_path: Target file path
            content: Content to write

        Returns:
            True if write successful, False otherwise
        """
        temp_file_path = f"{file_path}.tmp"
        parent_dir_fd = None

        try:
            # Write to temporary file with context manager
            with Path(temp_file_path).open('w', encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_file.flush()  # Ensure data is written to disk

                # Call fsync to ensure data is persisted to disk
                os.fsync(temp_file.fileno())

            # Atomic rename to target file with platform-specific handling
            if os.name == 'nt':  # Windows
                # On Windows, prefer Path.replace for atomic replacement
                try:
                    Path(temp_file_path).replace(file_path)
                except OSError:
                    # Fallback to rename if replace fails
                    if Path(file_path).exists():
                        Path(temp_file_path).replace(file_path)
                    else:
                        Path(temp_file_path).rename(file_path)
            else:  # Unix-like systems
                Path(temp_file_path).rename(file_path)

            # Ensure directory entry is persisted by fsyncing the parent directory
            try:
                parent_dir = str(Path(file_path).parent)
                parent_dir_fd = os.open(parent_dir, os.O_RDONLY)
                os.fsync(parent_dir_fd)
            except OSError as e:
                logger.warning("Failed to fsync parent directory %s: %s", parent_dir, e)
            finally:
                if parent_dir_fd is not None:
                    with suppress(OSError):
                        os.close(parent_dir_fd)
                    parent_dir_fd = None

            logger.info("Successfully persisted file %s", file_path)

        except Exception:
            logger.exception("Failed to write file %s", file_path)
        else:
            return True
        finally:
            # Clean up resources
            if parent_dir_fd is not None:
                with suppress(OSError):
                    os.close(parent_dir_fd)

            # Clean up temp file if it exists
            with suppress(Exception):
                if Path(temp_file_path).exists():
                    Path(temp_file_path).unlink()

        return False

    def rollback_if_needed(
        self,
        file_path: str,
        should_rollback: bool,
        session_id: str | None = None,
    ) -> bool:
        """Rollback a file if needed.

        Args:
            file_path: Path to the file to rollback
            should_rollback: Whether rollback should be performed
            session_id: Session ID for backup management

        Returns:
            True if rollback was successful or not needed, False otherwise
        """
        if not should_rollback:
            return True

        try:
            logger.info("Rolling back %s", file_path)
            rollback_success = self.backup_manager.restore_file(
                file_path, session_id or "default"
            )

            if not rollback_success:
                logger.error("Rollback failed for %s", file_path)

        except Exception:
            logger.exception("Error during rollback for %s", file_path)
            return False
        else:
            return rollback_success
