"""
Queue management operations for the AI linting fixer.

Extracted from database module to improve modularity and security.
"""

from __future__ import annotations

from datetime import UTC, datetime
import logging
import sqlite3
from typing import Any


logger = logging.getLogger(__name__)


class IssueQueueManager:
    """Manages the database-first linting issue processing queue."""

    def __init__(self, db: Any):
        # db is expected to have a db_path attribute (e.g., AIInteractionDB)
        self.db = db

    @staticmethod
    def _safe_in_placeholders(count: int) -> str:
        """Return a comma-separated list of '?' placeholders for IN clauses."""
        count = max(0, int(count))
        return ",".join("?" * count)

    def queue_issues(self, session_id: str, issues: list[dict[str, Any]]) -> int:
        """Queue a batch of linting issues for processing."""
        queued_count = 0

        with sqlite3.connect(self.db.db_path) as conn:
            for issue in issues:
                try:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO linting_issues_queue (
                            created_timestamp, session_id, file_path, line_number, column_number,
                            error_code, message, line_content, priority
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            datetime.now(UTC).isoformat(),
                            session_id,
                            issue["file_path"],
                            issue["line_number"],
                            issue["column_number"],
                            issue["error_code"],
                            issue["message"],
                            issue.get("line_content", ""),
                            issue.get("priority", 5),
                        ),
                    )
                    queued_count += 1
                except sqlite3.IntegrityError:
                    # Issue already exists in queue
                    logger.debug(
                        f"Issue already queued: {issue['file_path']}:{issue['line_number']}"
                    )

            conn.commit()

        logger.info(f"Queued {queued_count} new issues for session {session_id}")
        return queued_count

    def get_next_issues(
        self,
        limit: int = 10,
        worker_id: str | None = None,
        filter_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get the next batch of issues to process, ordered by priority."""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Build query with optional filters using parameterization only
            params: list[Any] = ["pending"]
            if filter_types:
                in_ph = self._safe_in_placeholders(len(filter_types))
                query = (
                    "SELECT * FROM linting_issues_queue WHERE status = ? "  # nosec B608
                    f"AND error_code IN ({in_ph}) "
                    "ORDER BY priority DESC, created_timestamp ASC LIMIT ?"
                )
                params.extend(filter_types)
            else:
                query = (
                    "SELECT * FROM linting_issues_queue WHERE status = ? "
                    "ORDER BY priority DESC, created_timestamp ASC LIMIT ?"
                )
            params.append(int(limit))

            cursor = conn.execute(query, params)
            issues = [dict(row) for row in cursor.fetchall()]

            # Mark issues as in_progress and assign worker
            if issues and worker_id:
                issue_ids = [
                    int(issue["id"]) for issue in issues if isinstance(issue.get("id"), int | str)
                ]
                placeholders = self._safe_in_placeholders(len(issue_ids))
                update_query = (
                    "UPDATE linting_issues_queue "  # nosec B608
                    "SET status = 'in_progress', assigned_worker_id = ?, processing_started_at = ? "
                    f"WHERE id IN ({placeholders})"
                )
                conn.execute(update_query, [worker_id, datetime.now(UTC).isoformat(), *issue_ids])
                conn.commit()

            return issues

    def update_issue_status(
        self, issue_id: int, status: str, fix_result: dict[str, Any] | None = None
    ) -> None:
        """Update the status and results of a specific issue."""
        with sqlite3.connect(self.db.db_path) as conn:
            update_fields = ["status = ?"]
            params: list[Any] = [status]

            if status in {"completed", "failed"}:
                update_fields.append("processing_completed_at = ?")
                params.append(datetime.now(UTC).isoformat())

            if fix_result:
                if "fix_successful" in fix_result:
                    update_fields.append("fix_successful = ?")
                    params.append(bool(fix_result["fix_successful"]))

                if "confidence_score" in fix_result:
                    update_fields.append("confidence_score = ?")
                    params.append(float(fix_result["confidence_score"]))

                if "ai_response" in fix_result:
                    update_fields.append("ai_response = ?")
                    params.append(str(fix_result["ai_response"]))

                if "error_message" in fix_result:
                    update_fields.append("error_message = ?")
                    params.append(str(fix_result["error_message"]))

            exec_params: list[Any] = [*params, int(issue_id)]

            # Build update query safely using an allowlist of fields
            allowed_set = {
                "status = ?",
                "processing_completed_at = ?",
                "fix_successful = ?",
                "confidence_score = ?",
                "ai_response = ?",
                "error_message = ?",
            }
            if not set(update_fields).issubset(allowed_set):
                msg = "Invalid update fields detected"
                raise ValueError(msg)
            if update_fields:
                update_query = (
                    "UPDATE linting_issues_queue SET "  # nosec B608
                    + ", ".join(update_fields)
                    + " WHERE id = ?"
                )
                conn.execute(update_query, exec_params)
            conn.commit()

    def retry_failed_issue(self, issue_id: int) -> bool:
        """Retry a failed issue if it hasn't exceeded max retries."""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row

            issue = conn.execute(
                "SELECT retry_count, max_retries FROM linting_issues_queue WHERE id = ?",
                (issue_id,),
            ).fetchone()

            if not issue:
                return False

            if issue["retry_count"] >= issue["max_retries"]:
                # Mark as permanently failed
                conn.execute(
                    "UPDATE linting_issues_queue SET status = 'failed' WHERE id = ?",
                    (issue_id,),
                )
                conn.commit()
                return False

            # Reset to pending with incremented retry count
            conn.execute(
                """
                UPDATE linting_issues_queue
                SET status = 'pending',
                    retry_count = retry_count + 1,
                    assigned_worker_id = NULL,
                    processing_started_at = NULL
                WHERE id = ?
                """,
                (issue_id,),
            )
            conn.commit()
            return True

    def get_queue_statistics(self, session_id: str | None = None) -> dict[str, Any]:
        """Get statistics about the issue queue."""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Base query conditions
            where_conditions = []
            params: list[Any] = []

            if session_id:
                where_conditions.append("session_id = ?")
                params.append(session_id)

            where_clause_prefix = (
                ("WHERE " + " AND ".join(where_conditions)) if where_conditions else ""
            )

            # Overall statistics
            stats_query = (
                "SELECT "  # nosec B608
                "COALESCE(COUNT(*), 0) as total_issues, "
                "COALESCE(SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END), 0) as pending, "
                "COALESCE(SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END), 0) as in_progress, "
                "COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) as completed, "
                "COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) as failed, "
                "COALESCE(SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END), 0) as skipped, "
                "COALESCE(SUM(CASE WHEN fix_successful = 1 THEN 1 ELSE 0 END), 0) as successful_fixes, "
                "COALESCE(AVG(CASE WHEN confidence_score IS NOT NULL THEN confidence_score END), 0) as avg_confidence "
                "FROM linting_issues_queue "
                f"{where_clause_prefix}"
            )

            overall_stats = dict(conn.execute(stats_query, params).fetchone())

            # Issue type breakdown
            type_query = (
                "SELECT "  # nosec B608
                "error_code, "
                "COALESCE(COUNT(*), 0) as count, "
                "COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) as completed, "
                "COALESCE(SUM(CASE WHEN fix_successful = 1 THEN 1 ELSE 0 END), 0) as successful, "
                "COALESCE(AVG(CASE WHEN confidence_score IS NOT NULL THEN confidence_score END), 0) as avg_confidence "
                "FROM linting_issues_queue "
                f"{where_clause_prefix}"
                " GROUP BY error_code ORDER BY count DESC"
            )

            type_stats = [dict(row) for row in conn.execute(type_query, params).fetchall()]

            return {
                "overall": overall_stats,
                "by_type": type_stats,
                "success_rate": (
                    overall_stats["successful_fixes"] / overall_stats["completed"] * 100
                    if overall_stats["completed"] and overall_stats["completed"] > 0
                    else 0
                ),
            }

    def cleanup_old_queue_items(self, days_to_keep: int = 7) -> None:
        """Clean up old completed/failed queue items."""
        with sqlite3.connect(self.db.db_path) as conn:
            cutoff_date = datetime.now(UTC).isoformat()[:10]  # YYYY-MM-DD format

            conn.execute(
                """
                DELETE FROM linting_issues_queue
                WHERE status IN ('completed', 'failed', 'skipped')
                AND DATE(created_timestamp) < DATE(?, ?)
                """,
                (cutoff_date, f"-{days_to_keep} days"),
            )
            conn.commit()

    def reset_stale_issues(self, timeout_minutes: int = 30) -> None:
        """Reset issues that have been in_progress for too long."""
        with sqlite3.connect(self.db.db_path) as conn:
            timeout_time = datetime.now(UTC).replace(microsecond=0)
            timeout_time = timeout_time.replace(minute=timeout_time.minute - timeout_minutes)

            conn.execute(
                """
                UPDATE linting_issues_queue
                SET status = 'pending',
                    assigned_worker_id = NULL,
                    processing_started_at = NULL,
                    retry_count = retry_count + 1
                WHERE status = 'in_progress'
                AND processing_started_at < ?
                AND retry_count < max_retries
                """,
                (timeout_time.isoformat(),),
            )

            # Mark as failed if exceeded retries
            conn.execute(
                """
                UPDATE linting_issues_queue
                SET status = 'failed'
                WHERE status = 'in_progress'
                AND processing_started_at < ?
                AND retry_count >= max_retries
                """,
                (timeout_time.isoformat(),),
            )

            conn.commit()
