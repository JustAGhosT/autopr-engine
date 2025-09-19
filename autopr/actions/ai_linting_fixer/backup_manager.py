"""
Backup Manager Module

Manages file backups and rollback capabilities for the AI linting fixer.
"""

from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from pathlib import Path
import shutil
import tempfile
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class FileBackup:
    """Information about a file backup."""

    file_path: str
    backup_path: str
    original_content: str
    backup_time: datetime
    session_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BackupSession:
    """A backup session with multiple file backups."""

    session_id: str
    start_time: datetime
    backups: dict[str, FileBackup] = field(default_factory=dict)
    is_active: bool = True


class BackupManager:
    """Manages file backups and rollback operations."""

    def __init__(self, backup_dir: str | None = None):
        """Initialize the backup manager."""
        self.backup_dir = Path(
            backup_dir or tempfile.mkdtemp(prefix="ai_fixer_backup_")
        )
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: dict[str, BackupSession] = {}
        self.current_session: str | None = None

        logger.info(f"Backup manager initialized with directory: {self.backup_dir}")

    def start_session(self, session_id: str) -> None:
        """Start a new backup session."""
        self.sessions[session_id] = BackupSession(
            session_id=session_id, start_time=datetime.now()
        )
        self.current_session = session_id
        logger.info(f"Started backup session: {session_id}")

    def backup_file(
        self, file_path: str, session_id: str | None = None
    ) -> FileBackup | None:
        """Create a backup of a file before modification."""
        session_id = session_id or self.current_session
        if not session_id or session_id not in self.sessions:
            logger.error(f"No active session for backup: {session_id}")
            return None

        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"File not found for backup: {file_path}")
                return None

            # Read original content
            with open(file_path_obj, encoding="utf-8") as f:
                original_content = f.read()

            # Create backup file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_filename = f"{file_path_obj.name}_{timestamp}.backup"
            backup_path = self.backup_dir / session_id / backup_filename
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Write backup
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(original_content)

            # Create backup record
            backup = FileBackup(
                file_path=str(file_path_obj.resolve()),
                backup_path=str(backup_path),
                original_content=original_content,
                backup_time=datetime.now(),
                session_id=session_id,
                metadata={"file_size": len(original_content)},
            )

            # Store in session
            self.sessions[session_id].backups[str(file_path_obj.resolve())] = backup
            logger.info(f"Created backup for {file_path} -> {backup_path}")

            return backup

        except Exception as e:
            logger.exception(f"Failed to backup file {file_path}: {e}")
            return None

    def restore_file(self, file_path: str, session_id: str | None = None) -> bool:
        """Restore a file from backup."""
        session_id = session_id or self.current_session
        if not session_id or session_id not in self.sessions:
            logger.error(f"No session found for restore: {session_id}")
            return False

        file_path_resolved = str(Path(file_path).resolve())
        backup = self.sessions[session_id].backups.get(file_path_resolved)

        if not backup:
            logger.error(f"No backup found for {file_path} in session {session_id}")
            return False

        try:
            # Restore from backup content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(backup.original_content)

            logger.info(f"Restored {file_path} from backup")
            return True

        except Exception as e:
            logger.exception(f"Failed to restore {file_path}: {e}")
            return False

    def rollback_session(self, session_id: str | None = None) -> dict[str, bool]:
        """Rollback all files in a session."""
        session_id = session_id or self.current_session
        if not session_id or session_id not in self.sessions:
            logger.error(f"No session found for rollback: {session_id}")
            return {}

        session = self.sessions[session_id]
        results = {}

        for file_path, _backup in session.backups.items():
            try:
                success = self.restore_file(file_path, session_id)
                results[file_path] = success
            except Exception as e:
                logger.exception(f"Failed to rollback {file_path}: {e}")
                results[file_path] = False

        logger.info(
            f"Rollback session {session_id}: {sum(results.values())}/{len(results)} files restored"
        )
        return results

    def validate_file_changes(
        self, file_path: str, session_id: str | None = None
    ) -> dict[str, Any]:
        """Validate changes made to a file since backup."""
        session_id = session_id or self.current_session
        if not session_id or session_id not in self.sessions:
            return {"error": "No active session"}

        file_path_resolved = str(Path(file_path).resolve())
        backup = self.sessions[session_id].backups.get(file_path_resolved)

        if not backup:
            return {"error": "No backup found for file"}

        try:
            # Read current content
            with open(file_path, encoding="utf-8") as f:
                current_content = f.read()

            # Compare with backup
            lines_added = 0
            lines_removed = 0
            lines_modified = 0

            original_lines = backup.original_content.splitlines()
            current_lines = current_content.splitlines()

            # Simple diff calculation
            if len(current_lines) > len(original_lines):
                lines_added = len(current_lines) - len(original_lines)
            elif len(current_lines) < len(original_lines):
                lines_removed = len(original_lines) - len(current_lines)

            # Check for modifications in existing lines
            for _i, (orig, curr) in enumerate(
                zip(original_lines, current_lines, strict=False)
            ):
                if orig != curr:
                    lines_modified += 1

            return {
                "has_changes": current_content != backup.original_content,
                "original_size": len(backup.original_content),
                "current_size": len(current_content),
                "size_change": len(current_content) - len(backup.original_content),
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "lines_modified": lines_modified,
                "backup_time": backup.backup_time.isoformat(),
                "change_ratio": abs(len(current_content) - len(backup.original_content))
                / len(backup.original_content),
            }

        except Exception as e:
            return {"error": str(e)}

    def get_session_stats(self, session_id: str | None = None) -> dict[str, Any]:
        """Get statistics for a backup session."""
        session_id = session_id or self.current_session
        if not session_id or session_id not in self.sessions:
            return {}

        session = self.sessions[session_id]

        total_backups = len(session.backups)
        total_size = sum(
            len(backup.original_content) for backup in session.backups.values()
        )

        return {
            "session_id": session_id,
            "start_time": session.start_time.isoformat(),
            "total_backups": total_backups,
            "total_backup_size": total_size,
            "is_active": session.is_active,
            "files": list(session.backups.keys()),
        }

    def cleanup_session(self, session_id: str, keep_backups: bool = False) -> None:
        """Clean up a backup session."""
        if session_id not in self.sessions:
            return

        try:
            if not keep_backups:
                # Remove backup files
                session_backup_dir = self.backup_dir / session_id
                if session_backup_dir.exists():
                    shutil.rmtree(session_backup_dir)
                    logger.info(f"Removed backup directory for session {session_id}")

            # Mark session as inactive
            self.sessions[session_id].is_active = False

            if self.current_session == session_id:
                self.current_session = None

            logger.info(f"Cleaned up session {session_id}")

        except Exception as e:
            logger.exception(f"Failed to cleanup session {session_id}: {e}")

    def export_session_metadata(self, session_id: str) -> str | None:
        """Export session metadata to JSON file."""
        if session_id not in self.sessions:
            return None

        try:
            session = self.sessions[session_id]
            metadata = {
                "session_id": session_id,
                "start_time": session.start_time.isoformat(),
                "is_active": session.is_active,
                "backups": {
                    file_path: {
                        "backup_path": backup.backup_path,
                        "backup_time": backup.backup_time.isoformat(),
                        "metadata": backup.metadata,
                    }
                    for file_path, backup in session.backups.items()
                },
            }

            export_path = self.backup_dir / f"{session_id}_metadata.json"
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Exported session metadata to {export_path}")
            return str(export_path)

        except Exception as e:
            logger.exception(f"Failed to export session metadata: {e}")
            return None
