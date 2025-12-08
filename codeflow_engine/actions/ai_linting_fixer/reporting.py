"""
Reporting and statistics helpers for AI linting database.

Extracted from database module.
"""

from __future__ import annotations

import sqlite3
from typing import Any


def get_database_info(db_path: str) -> dict[str, Any]:
    """Get information about the database file and table counts."""
    from pathlib import Path

    db_file = Path(db_path)
    info: dict[str, Any] = {
        "database_path": str(db_file.absolute()),
        "database_exists": db_file.exists(),
        "database_size_mb": 0.0,
        "table_counts": {},
    }

    if not db_file.exists():
        return info

    info["database_size_mb"] = db_file.stat().st_size / (1024 * 1024)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        tables = ["ai_interactions", "performance_sessions"]
        table_counts: dict[str, int] = {}
        allowed_queries: dict[str, str] = {
            "ai_interactions": "SELECT COUNT(*) as count FROM ai_interactions",
            "performance_sessions": "SELECT COUNT(*) as count FROM performance_sessions",
        }

        for table in tables:
            try:
                query = allowed_queries.get(table)
                if not query:
                    continue
                count_row = conn.execute(query).fetchone()
                table_counts[table] = int(count_row["count"]) if count_row else 0
            except sqlite3.OperationalError:
                table_counts[table] = 0

        info["table_counts"] = table_counts

    return info
