"""
Database and Logging Module

Handles AI interaction logging, performance metrics, and full-text search
for the modular AI linting system.
"""

from datetime import datetime
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)


class AIInteractionDB:
    """Database for storing detailed AI interactions with full-text search."""

    def __init__(self, db_path: str = "ai_linting_interactions.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Create main interactions table with enhanced metrics
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    issue_type TEXT NOT NULL,
                    issue_details TEXT NOT NULL,
                    provider_used TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    system_prompt TEXT NOT NULL,
                    user_prompt TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    fix_successful BOOLEAN NOT NULL,
                    confidence_score REAL,
                    fixed_codes TEXT,
                    error_message TEXT,
                    syntax_valid_before BOOLEAN,
                    syntax_valid_after BOOLEAN,
                    file_size_chars INTEGER,
                    prompt_tokens INTEGER,
                    response_tokens INTEGER,

                    -- Performance metrics
                    processing_duration REAL,
                    api_response_time REAL,
                    queue_wait_time REAL,
                    file_complexity_score REAL,
                    parallel_worker_id INTEGER,
                    retry_count INTEGER,
                    memory_usage_mb REAL,
                    tokens_per_second REAL,
                    agent_type TEXT
                )
            """
            )

            # Create FTS virtual table for searching prompts and responses
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS interactions_fts USING fts5(
                    system_prompt,
                    user_prompt,
                    ai_response,
                    issue_type,
                    file_path,
                    content='ai_interactions',
                    content_rowid='id'
                )
            """
            )

            # Create triggers to keep FTS table in sync
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS interactions_ai AFTER INSERT ON ai_interactions BEGIN
                    INSERT INTO interactions_fts(rowid, system_prompt, user_prompt, ai_response, issue_type, file_path)
                    VALUES (new.id, new.system_prompt, new.user_prompt, new.ai_response, new.issue_type, new.file_path);
                END;
            """
            )

            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS interactions_ad AFTER DELETE ON ai_interactions BEGIN
                    INSERT INTO interactions_fts(interactions_fts, rowid, system_prompt, user_prompt, ai_response, issue_type, file_path)
                    VALUES('delete', old.id, old.system_prompt, old.user_prompt, old.ai_response, old.issue_type, old.file_path);
                END;
            """
            )

            # Create performance metrics table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_timestamp TEXT NOT NULL,
                    total_duration REAL,
                    files_processed INTEGER,
                    issues_found INTEGER,
                    issues_fixed INTEGER,
                    success_rate REAL,
                    average_confidence REAL,
                    throughput_files_per_sec REAL,
                    throughput_issues_per_sec REAL,
                    parallel_workers INTEGER,
                    total_tokens INTEGER,
                    total_api_calls INTEGER,
                    average_api_response_time REAL,
                    provider_used TEXT,
                    model_used TEXT
                )
            """
            )

            # Create linting issues queue table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS linting_issues_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    column_number INTEGER NOT NULL,
                    error_code TEXT NOT NULL,
                    message TEXT NOT NULL,
                    line_content TEXT,

                    -- Processing status
                    status TEXT NOT NULL DEFAULT 'pending',  -- pending, in_progress, completed, failed, skipped
                    priority INTEGER DEFAULT 5,  -- 1-10, higher = more priority
                    assigned_worker_id TEXT,
                    assigned_agent_type TEXT,

                    -- Processing metadata
                    processing_started_at TEXT,
                    processing_completed_at TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,

                    -- Fix results
                    fix_successful BOOLEAN,
                    confidence_score REAL,
                    ai_response TEXT,
                    error_message TEXT,

                    -- Constraints
                    UNIQUE(session_id, file_path, line_number, column_number, error_code)
                )
            """
            )

            # Create index for efficient querying
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_issues_status ON linting_issues_queue(status, priority DESC, created_timestamp)"
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_issues_session ON linting_issues_queue(session_id, status)"
            )

            conn.commit()

    def log_interaction(self, interaction_data: dict[str, Any]):
        """Log a complete AI interaction to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO ai_interactions (
                    timestamp, file_path, issue_type, issue_details, provider_used, model_used,
                    system_prompt, user_prompt, ai_response, fix_successful, confidence_score,
                    fixed_codes, error_message, syntax_valid_before, syntax_valid_after,
                    file_size_chars, prompt_tokens, response_tokens,
                    processing_duration, api_response_time, queue_wait_time,
                    file_complexity_score, parallel_worker_id, retry_count,
                    memory_usage_mb, tokens_per_second, agent_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    interaction_data["timestamp"],
                    interaction_data["file_path"],
                    interaction_data["issue_type"],
                    interaction_data["issue_details"],
                    interaction_data["provider_used"],
                    interaction_data["model_used"],
                    interaction_data["system_prompt"],
                    interaction_data["user_prompt"],
                    interaction_data["ai_response"],
                    interaction_data["fix_successful"],
                    interaction_data.get("confidence_score"),
                    json.dumps(interaction_data.get("fixed_codes", [])),
                    interaction_data.get("error_message"),
                    interaction_data.get("syntax_valid_before"),
                    interaction_data.get("syntax_valid_after"),
                    interaction_data.get("file_size_chars"),
                    interaction_data.get("prompt_tokens"),
                    interaction_data.get("response_tokens"),
                    interaction_data.get("processing_duration"),
                    interaction_data.get("api_response_time"),
                    interaction_data.get("queue_wait_time"),
                    interaction_data.get("file_complexity_score"),
                    interaction_data.get("parallel_worker_id"),
                    interaction_data.get("retry_count", 0),
                    interaction_data.get("memory_usage_mb"),
                    interaction_data.get("tokens_per_second"),
                    interaction_data.get("agent_type"),
                ),
            )
            conn.commit()

    def log_performance_session(self, session_data: dict[str, Any]):
        """Log overall session performance metrics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO performance_sessions (
                    session_timestamp, total_duration, files_processed, issues_found,
                    issues_fixed, success_rate, average_confidence, throughput_files_per_sec,
                    throughput_issues_per_sec, parallel_workers, total_tokens, total_api_calls,
                    average_api_response_time, provider_used, model_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_data["session_timestamp"],
                    session_data["total_duration"],
                    session_data["files_processed"],
                    session_data["issues_found"],
                    session_data["issues_fixed"],
                    session_data["success_rate"],
                    session_data["average_confidence"],
                    session_data["throughput_files_per_sec"],
                    session_data["throughput_issues_per_sec"],
                    session_data["parallel_workers"],
                    session_data["total_tokens"],
                    session_data["total_api_calls"],
                    session_data["average_api_response_time"],
                    session_data["provider_used"],
                    session_data["model_used"],
                ),
            )
            conn.commit()

    def search_interactions(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search through AI interactions using full-text search."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT ai.* FROM ai_interactions ai
                JOIN interactions_fts fts ON ai.id = fts.rowid
                WHERE interactions_fts MATCH ?
                ORDER BY ai.timestamp DESC
                LIMIT ?
            """,
                (query, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive statistics from the interaction database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Basic stats
            total_interactions = conn.execute(
                "SELECT COUNT(*) as count FROM ai_interactions"
            ).fetchone()["count"]
            successful_fixes = conn.execute(
                "SELECT COUNT(*) as count FROM ai_interactions WHERE fix_successful = 1"
            ).fetchone()["count"]
            failed_fixes = conn.execute(
                "SELECT COUNT(*) as count FROM ai_interactions WHERE fix_successful = 0"
            ).fetchone()["count"]

            # Confidence statistics
            confidence_stats = conn.execute(
                """
                SELECT
                    AVG(confidence_score) as average_confidence,
                    MIN(confidence_score) as min_confidence,
                    MAX(confidence_score) as max_confidence,
                    COUNT(CASE WHEN confidence_score > 0.8 THEN 1 END) as high_confidence_count,
                    COUNT(CASE WHEN confidence_score < 0.5 THEN 1 END) as low_confidence_count,
                    COUNT(confidence_score) as total_confidence_scores
                FROM ai_interactions
                WHERE confidence_score IS NOT NULL
                """
            ).fetchone()

            # Calculate confidence percentages
            if confidence_stats and confidence_stats["total_confidence_scores"] > 0:
                high_confidence_percentage = (
                    confidence_stats["high_confidence_count"]
                    / confidence_stats["total_confidence_scores"]
                ) * 100
                low_confidence_percentage = (
                    confidence_stats["low_confidence_count"]
                    / confidence_stats["total_confidence_scores"]
                ) * 100
            else:
                high_confidence_percentage = 0.0
                low_confidence_percentage = 0.0

            # Issue type breakdown
            issue_type_breakdown = conn.execute(
                """
                SELECT issue_type, COUNT(*) as count
                FROM ai_interactions
                GROUP BY issue_type
                ORDER BY count DESC
                """
            ).fetchall()

            # Provider performance
            provider_performance = conn.execute(
                """
                SELECT
                    provider_used,
                    COUNT(*) as attempts,
                    SUM(CASE WHEN fix_successful = 1 THEN 1 ELSE 0 END) as successes,
                    AVG(CASE WHEN confidence_score IS NOT NULL THEN confidence_score END) as average_confidence
                FROM ai_interactions
                GROUP BY provider_used
                """
            ).fetchall()

            # Recent activity
            recent_activity = conn.execute(
                """
                SELECT
                    COUNT(CASE WHEN timestamp >= datetime('now', '-1 day') THEN 1 END) as last_24h,
                    COUNT(CASE WHEN timestamp >= datetime('now', '-7 days') THEN 1 END) as last_7d,
                    COUNT(CASE WHEN timestamp >= datetime('now', '-30 days') THEN 1 END) as last_30d
                FROM ai_interactions
                """
            ).fetchone()

            # File statistics
            file_stats = conn.execute(
                """
                SELECT
                    COUNT(DISTINCT file_path) as unique_files,
                    AVG(file_size_chars) as average_file_size
                FROM ai_interactions
                """
            ).fetchone()

            # Most processed file
            most_processed_file = conn.execute(
                """
                SELECT file_path, COUNT(*) as count
                FROM ai_interactions
                GROUP BY file_path
                ORDER BY count DESC
                LIMIT 1
                """
            ).fetchone()

            return {
                "total_interactions": total_interactions,
                "successful_fixes": successful_fixes,
                "failed_fixes": failed_fixes,
                "success_rate": (
                    (successful_fixes / total_interactions * 100) if total_interactions > 0 else 0
                ),
                "confidence_stats": {
                    "average_confidence": (
                        confidence_stats["average_confidence"] if confidence_stats else 0.0
                    ),
                    "median_confidence": 0.0,  # Would need more complex query
                    "min_confidence": (
                        confidence_stats["min_confidence"] if confidence_stats else 0.0
                    ),
                    "max_confidence": (
                        confidence_stats["max_confidence"] if confidence_stats else 0.0
                    ),
                    "high_confidence_count": (
                        confidence_stats["high_confidence_count"] if confidence_stats else 0
                    ),
                    "low_confidence_count": (
                        confidence_stats["low_confidence_count"] if confidence_stats else 0
                    ),
                    "high_confidence_percentage": high_confidence_percentage,
                    "low_confidence_percentage": low_confidence_percentage,
                },
                "issue_type_breakdown": {
                    row["issue_type"]: row["count"] for row in issue_type_breakdown
                },
                "provider_performance": {
                    row["provider_used"]: {
                        "success_rate": (
                            (row["successes"] / row["attempts"] * 100)
                            if row["attempts"] > 0
                            else 0.0
                        ),
                        "average_confidence": row["average_confidence"] or 0.0,
                    }
                    for row in provider_performance
                },
                "recent_activity": {
                    "last_24h": recent_activity["last_24h"] if recent_activity else 0,
                    "last_7d": recent_activity["last_7d"] if recent_activity else 0,
                    "last_30d": recent_activity["last_30d"] if recent_activity else 0,
                },
                "file_stats": {
                    "unique_files": file_stats["unique_files"] if file_stats else 0,
                    "average_file_size": file_stats["average_file_size"] if file_stats else 0,
                    "most_processed_file": (
                        most_processed_file["file_path"] if most_processed_file else "None"
                    ),
                },
            }

    def get_all_interactions(self, limit: int = 1000) -> list[dict[str, Any]]:
        """Get all interactions from the database (for export functionality)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM ai_interactions
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_session_performance(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent session performance data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM performance_sessions
                ORDER BY session_timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def cleanup_old_interactions(self, days_to_keep: int = 30):
        """Clean up old interactions to keep database size manageable."""
        with sqlite3.connect(self.db_path) as conn:
            cutoff_date = datetime.now().isoformat()[:10]  # YYYY-MM-DD format

            # Delete old interactions (keeping last N days)
            conn.execute(
                """
                DELETE FROM ai_interactions
                WHERE DATE(timestamp) < DATE(?, ?)
                """,
                (cutoff_date, f"-{days_to_keep} days"),
            )

            # Delete old performance sessions
            conn.execute(
                """
                DELETE FROM performance_sessions
                WHERE DATE(session_timestamp) < DATE(?, ?)
                """,
                (cutoff_date, f"-{days_to_keep} days"),
            )

            conn.commit()

            # Optimize database after cleanup
            conn.execute("VACUUM")

    def get_database_info(self) -> dict[str, Any]:
        """Get information about the database file and tables."""
        db_path = Path(self.db_path)

        info = {
            "database_path": str(db_path.absolute()),
            "database_exists": db_path.exists(),
            "database_size_mb": 0.0,
            "table_counts": {},
        }

        if db_path.exists():
            info["database_size_mb"] = db_path.stat().st_size / (1024 * 1024)

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Get table counts
                tables = ["ai_interactions", "performance_sessions"]
                for table in tables:
                    try:
                        # Use parameterized query with table name validation
                        if table in tables:  # Validate table name
                            count = conn.execute(
                                "SELECT COUNT(*) as count FROM " + table
                            ).fetchone()["count"]
                            info["table_counts"][table] = count
                    except sqlite3.OperationalError:
                        info["table_counts"][table] = 0

        return info


class IssueQueueManager:
    """Manages the database-first linting issue processing queue."""

    def __init__(self, db: AIInteractionDB):
        self.db = db

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
                            datetime.now().isoformat(),
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
        self, limit: int = 10, worker_id: str | None = None, filter_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Get the next batch of issues to process, ordered by priority."""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Build query with optional filters
            where_conditions = ["status = 'pending'"]
            params = []

            if filter_types:
                placeholders = ",".join("?" * len(filter_types))
                where_conditions.append(f"error_code IN ({placeholders})")
                params.extend(filter_types)

            where_clause = " AND ".join(where_conditions)

            query = f"""
                SELECT * FROM linting_issues_queue
                WHERE {where_clause}
                ORDER BY priority DESC, created_timestamp ASC
                LIMIT ?
            """
            params.append(limit)

            cursor = conn.execute(query, params)
            issues = [dict(row) for row in cursor.fetchall()]

            # Mark issues as in_progress and assign worker
            if issues and worker_id:
                issue_ids = [issue["id"] for issue in issues]
                placeholders = ",".join("?" * len(issue_ids))

                conn.execute(
                    f"""
                    UPDATE linting_issues_queue
                    SET status = 'in_progress',
                        assigned_worker_id = ?,
                        processing_started_at = ?
                    WHERE id IN ({placeholders})
                    """,
                    [worker_id, datetime.now().isoformat(), *issue_ids],
                )
                conn.commit()

            return issues

    def update_issue_status(
        self, issue_id: int, status: str, fix_result: dict[str, Any] | None = None
    ):
        """Update the status and results of a specific issue."""
        with sqlite3.connect(self.db.db_path) as conn:
            update_fields = ["status = ?"]
            params = [status]

            if status in {"completed", "failed"}:
                update_fields.append("processing_completed_at = ?")
                params.append(datetime.now().isoformat())

            if fix_result:
                if "fix_successful" in fix_result:
                    update_fields.append("fix_successful = ?")
                    params.append(fix_result["fix_successful"])

                if "confidence_score" in fix_result:
                    update_fields.append("confidence_score = ?")
                    params.append(fix_result["confidence_score"])

                if "ai_response" in fix_result:
                    update_fields.append("ai_response = ?")
                    params.append(fix_result["ai_response"])

                if "error_message" in fix_result:
                    update_fields.append("error_message = ?")
                    params.append(fix_result["error_message"])

            params.append(issue_id)

            # Build update query safely
            if update_fields:
                update_query = (
                    f"UPDATE linting_issues_queue SET {', '.join(update_fields)} WHERE id = ?"
                )
                conn.execute(update_query, params)
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
            params = []

            if session_id:
                where_conditions.append("session_id = ?")
                params.append(session_id)

            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

            # Overall statistics
            stats_query = f"""
                SELECT
                    COALESCE(COUNT(*), 0) as total_issues,
                    COALESCE(SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END), 0) as pending,
                    COALESCE(SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END), 0) as in_progress,
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) as completed,
                    COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) as failed,
                    COALESCE(SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END), 0) as skipped,
                    COALESCE(SUM(CASE WHEN fix_successful = 1 THEN 1 ELSE 0 END), 0) as successful_fixes,
                    COALESCE(AVG(CASE WHEN confidence_score IS NOT NULL THEN confidence_score END), 0) as avg_confidence
                FROM linting_issues_queue {where_clause}
            """

            overall_stats = dict(conn.execute(stats_query, params).fetchone())

            # Issue type breakdown
            type_stats_query = f"""
                SELECT
                    error_code,
                    COALESCE(COUNT(*), 0) as count,
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) as completed,
                    COALESCE(SUM(CASE WHEN fix_successful = 1 THEN 1 ELSE 0 END), 0) as successful,
                    COALESCE(AVG(CASE WHEN confidence_score IS NOT NULL THEN confidence_score END), 0) as avg_confidence
                FROM linting_issues_queue {where_clause}
                GROUP BY error_code
                ORDER BY count DESC
            """

            type_stats = [dict(row) for row in conn.execute(type_stats_query, params).fetchall()]

            return {
                "overall": overall_stats,
                "by_type": type_stats,
                "success_rate": (
                    overall_stats["successful_fixes"] / overall_stats["completed"] * 100
                    if overall_stats["completed"] and overall_stats["completed"] > 0
                    else 0
                ),
            }

    def cleanup_old_queue_items(self, days_to_keep: int = 7):
        """Clean up old completed/failed queue items."""
        with sqlite3.connect(self.db.db_path) as conn:
            cutoff_date = datetime.now().isoformat()[:10]  # YYYY-MM-DD format

            conn.execute(
                """
                DELETE FROM linting_issues_queue
                WHERE status IN ('completed', 'failed', 'skipped')
                AND DATE(created_timestamp) < DATE(?, ?)
                """,
                (cutoff_date, f"-{days_to_keep} days"),
            )
            conn.commit()

    def reset_stale_issues(self, timeout_minutes: int = 30):
        """Reset issues that have been in_progress for too long."""
        with sqlite3.connect(self.db.db_path) as conn:
            timeout_time = datetime.now().replace(microsecond=0)
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


class DatabaseManager:
    """Higher-level database operations and maintenance."""

    def __init__(self, db_path: str = "ai_linting_interactions.db"):
        self.db = AIInteractionDB(db_path)
        self.queue_manager = IssueQueueManager(self.db)

    def export_to_json(self, filepath: str, include_sessions: bool = True):
        """Export database contents to JSON file."""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "database_info": self.db.get_database_info(),
            "interactions": self.db.get_all_interactions(),
        }

        if include_sessions:
            export_data["performance_sessions"] = self.db.get_session_performance(limit=100)

        # Include queue statistics
        export_data["queue_statistics"] = self.queue_manager.get_queue_statistics()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Database exported to {filepath}")

    def import_from_json(self, filepath: str):
        """Import interactions from JSON file (for data migration)."""
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        interactions = data.get("interactions", [])

        for interaction in interactions:
            try:
                self.db.log_interaction(interaction)
            except Exception as e:
                logger.exception(
                    f"Failed to import interaction {interaction.get('id', 'unknown')}: {e}"
                )

        logger.info(f"Imported {len(interactions)} interactions from {filepath}")

    def get_health_check(self) -> dict[str, Any]:
        """Get database health status."""
        try:
            stats = self.db.get_statistics()
            db_info = self.db.get_database_info()
            queue_stats = self.queue_manager.get_queue_statistics()

            return {
                "status": "healthy",
                "total_interactions": stats["total_interactions"],
                "database_size_mb": db_info["database_size_mb"],
                "success_rate": stats["success_rate"],
                "queue_pending": queue_stats["overall"]["pending"],
                "queue_in_progress": queue_stats["overall"]["in_progress"],
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    def maintenance(self, cleanup_days: int = 30):
        """Perform database maintenance tasks."""
        logger.info("Starting database maintenance...")

        # Clean up old interactions
        self.db.cleanup_old_interactions(cleanup_days)

        # Clean up old queue items
        self.queue_manager.cleanup_old_queue_items(days_to_keep=7)

        # Reset stale issues
        self.queue_manager.reset_stale_issues(timeout_minutes=30)

        logger.info("Database maintenance completed")


# Global database instances for convenience
default_db = AIInteractionDB()
issue_queue = IssueQueueManager(default_db)
db_manager = DatabaseManager()
