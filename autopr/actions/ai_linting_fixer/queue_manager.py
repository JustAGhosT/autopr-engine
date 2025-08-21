"""
Issue Queue Manager

Manages the queue of linting issues for processing by AI agents.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class IssueQueueManager:
    """Manages the queue of linting issues for AI processing."""

    def __init__(self, db_path: str = "issue_queue.db"):
        """Initialize the issue queue manager."""
        self.db_path = Path(db_path)
        self.init_database()

    def init_database(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS issue_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    error_code TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    column_number INTEGER DEFAULT 0,
                    message TEXT NOT NULL,
                    severity TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    worker_id TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    attempts INTEGER DEFAULT 0,
                    fix_result TEXT DEFAULT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_session_status 
                ON issue_queue(session_id, status)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_file_path 
                ON issue_queue(file_path)
            """
            )

    def queue_issues(self, session_id: str, issues: List[Dict[str, Any]]) -> int:
        """Queue multiple issues for processing."""
        queued_count = 0

        with sqlite3.connect(self.db_path) as conn:
            for issue in issues:
                try:
                    conn.execute(
                        """
                        INSERT INTO issue_queue (
                            session_id, file_path, error_code, line_number, 
                            column_number, message, severity, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            session_id,
                            issue.get("file_path", ""),
                            issue.get("error_code", ""),
                            issue.get("line_number", 0),
                            issue.get("column_number", 0),
                            issue.get("message", ""),
                            issue.get("severity", "medium"),
                            json.dumps(issue.get("metadata", {})),
                        ),
                    )
                    queued_count += 1
                except Exception as e:
                    logger.error(f"Failed to queue issue: {e}")

        return queued_count

    def get_next_issues(
        self,
        limit: int = 50,
        worker_id: Optional[str] = None,
        filter_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get the next batch of issues to process."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            where_conditions = ["status = 'pending'"]
            params = []

            if filter_types:
                placeholders = ",".join("?" for _ in filter_types)
                where_conditions.append(f"error_code IN ({placeholders})")
                params.extend(filter_types)

            query = f"""
                SELECT * FROM issue_queue 
                WHERE {' AND '.join(where_conditions)}
                ORDER BY created_at ASC 
                LIMIT ?
            """
            params.append(limit)

            cursor = conn.execute(query, params)
            issues = [dict(row) for row in cursor.fetchall()]

            # Mark issues as processing
            if issues and worker_id:
                issue_ids = [issue["id"] for issue in issues]
                placeholders = ",".join("?" for _ in issue_ids)
                conn.execute(
                    f"""
                    UPDATE issue_queue 
                    SET status = 'processing', worker_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id IN ({placeholders})
                """,
                    [worker_id] + issue_ids,
                )

        return issues

    def update_issue_status(
        self, issue_id: int, status: str, fix_result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update the status of an issue."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE issue_queue 
                SET status = ?, fix_result = ?, updated_at = CURRENT_TIMESTAMP,
                    attempts = attempts + 1
                WHERE id = ?
            """,
                (status, json.dumps(fix_result) if fix_result else None, issue_id),
            )

    def get_queue_stats(self) -> Dict[str, int]:
        """Get statistics about the issue queue."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM issue_queue
            """
            )
            row = cursor.fetchone()

            return {
                "total": row[0] or 0,
                "pending": row[1] or 0,
                "processing": row[2] or 0,
                "completed": row[3] or 0,
                "failed": row[4] or 0,
                "success_rate": (row[3] / row[0] * 100) if row[0] > 0 else 0.0,
            }
