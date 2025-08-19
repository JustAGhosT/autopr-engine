"""
AutoPR Action: Learning & Memory System
Tracks patterns, user preferences, and project context to improve decision-making over time.
"""

from datetime import datetime
import hashlib
import os
import pathlib
import sqlite3
from typing import Any

from pydantic import BaseModel


class MemoryInputs(BaseModel):
    action_type: str  # "record_fix", "record_preference", "get_patterns", "get_recommendations"
    user_id: str | None = None
    file_path: str | None = None
    comment_type: str | None = None
    fix_applied: str | None = None
    success: bool | None = None
    context: dict[str, Any] = {}


class MemoryOutputs(BaseModel):
    success: bool
    patterns: list[dict[str, Any]] = []
    recommendations: list[str] = []
    confidence_scores: dict[str, float] = {}
    learned_preferences: dict[str, Any] = {}


class LearningMemorySystem:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path: str = db_path or "autopr_memory.db"
        self.init_database()

    def init_database(self) -> None:
        """Initialize the memory database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables for different types of memory
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fix_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_type TEXT,
                file_extension TEXT,
                fix_type TEXT,
                fix_code TEXT,
                success_rate REAL,
                usage_count INTEGER,
                last_used TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                preference_type TEXT,
                preference_value TEXT,
                confidence REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS project_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_hash TEXT,
                context_type TEXT,
                pattern TEXT,
                frequency INTEGER,
                effectiveness REAL,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fix_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT,
                user_id TEXT,
                file_path TEXT,
                original_comment TEXT,
                fix_applied TEXT,
                success BOOLEAN,
                feedback_score INTEGER,
                execution_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def record_fix_pattern(self, inputs: MemoryInputs) -> bool:
        """Record a successful fix pattern for future learning."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            file_ext = os.path.splitext(inputs.file_path or "")[1] if inputs.file_path else ""

            # Check if pattern exists
            cursor.execute(
                """
                SELECT id, usage_count, success_rate FROM fix_patterns
                WHERE comment_type = ? AND file_extension = ? AND fix_type = ?
            """,
                (inputs.comment_type, file_ext, inputs.fix_applied),
            )

            existing = cursor.fetchone()

            if existing:
                # Update existing pattern
                pattern_id, usage_count, success_rate = existing
                new_usage_count = usage_count + 1
                new_success_rate = (
                    (success_rate * usage_count) + (1 if inputs.success else 0)
                ) / new_usage_count

                cursor.execute(
                    """
                    UPDATE fix_patterns
                    SET usage_count = ?, success_rate = ?, last_used = ?
                    WHERE id = ?
                """,
                    (new_usage_count, new_success_rate, datetime.now(), pattern_id),
                )
            else:
                # Create new pattern
                cursor.execute(
                    """
                    INSERT INTO fix_patterns
                    (comment_type, file_extension, fix_type, fix_code, success_rate, usage_count, last_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        inputs.comment_type,
                        file_ext,
                        inputs.fix_applied,
                        inputs.context.get("fix_code", ""),
                        1.0 if inputs.success else 0.0,
                        1,
                        datetime.now(),
                    ),
                )

            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def record_user_preference(
        self,
        user_id: str | None = None,
        preference_type: str | None = None,
        preference_value: str | None = None,
        confidence: float = 1.0,
    ) -> bool:
        """Record user preferences for personalized responses."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Upsert user preference
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_preferences
                (user_id, preference_type, preference_value, confidence, last_updated)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    preference_type,
                    preference_value,
                    confidence,
                    datetime.now(),
                ),
            )

            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def get_fix_recommendations(
        self, comment_type: str | None = None, file_path: str | None = None
    ) -> list[dict[str, Any]]:
        """Get fix recommendations based on learned patterns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            file_ext = os.path.splitext(file_path or "")[1] if file_path else ""

            # Get patterns ordered by success rate and usage
            cursor.execute(
                """
                SELECT fix_type, fix_code, success_rate, usage_count,
                       (success_rate * 0.7 + (usage_count / 100.0) * 0.3) as score
                FROM fix_patterns
                WHERE comment_type = ? AND (file_extension = ? OR file_extension = '')
                ORDER BY score DESC
                LIMIT 5
            """,
                (comment_type, file_ext),
            )

            recommendations = []
            for row in cursor.fetchall():
                fix_type, fix_code, success_rate, usage_count, score = row
                recommendations.append(
                    {
                        "fix_type": fix_type,
                        "fix_code": fix_code,
                        "confidence": min(score, 1.0),
                        "usage_count": usage_count,
                        "success_rate": success_rate,
                    }
                )

            return recommendations
        except Exception:
            return []
        finally:
            conn.close()

    def get_user_preferences(self, user_id: str | None = None) -> dict[str, Any]:
        """Get learned preferences for a specific user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT preference_type, preference_value, confidence
                FROM user_preferences
                WHERE user_id = ?
                ORDER BY confidence DESC
            """,
                (user_id,),
            )

            preferences = {}
            for pref_type, pref_value, confidence in cursor.fetchall():
                preferences[pref_type] = {"value": pref_value, "confidence": confidence}

            return preferences
        except Exception:
            return {}
        finally:
            conn.close()

    def analyze_project_patterns(self, project_files: list[str]) -> dict[str, Any]:
        """Analyze project-specific patterns and conventions."""
        project_hash = hashlib.md5(
            str(sorted(project_files)).encode(), usedforsecurity=False
        ).hexdigest()[:8]

        patterns = {
            "coding_style": self._detect_coding_style(project_files),
            "naming_conventions": self._detect_naming_conventions(project_files),
            "file_structure": self._analyze_file_structure(project_files),
            "common_patterns": self._find_common_patterns(project_files),
        }

        # Store project context
        self._store_project_context(project_hash, patterns)

        return patterns

    def _detect_coding_style(self, files: list[str]) -> dict[str, Any]:
        """Detect coding style preferences from project files."""
        style_indicators = {
            "semicolons": 0,
            "no_semicolons": 0,
            "single_quotes": 0,
            "double_quotes": 0,
            "spaces": 0,
            "tabs": 0,
        }

        # Sample a few files to analyze style
        for file_path in files[:10]:
            if file_path.endswith((".js", ".ts", ".tsx", ".jsx")):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    # Count style indicators
                    style_indicators["semicolons"] += content.count(";\n")
                    style_indicators["single_quotes"] += content.count("'")
                    style_indicators["double_quotes"] += content.count('"')

                    lines = content.split("\n")
                    for line in lines[:50]:  # Sample first 50 lines
                        if line.startswith("  "):
                            style_indicators["spaces"] += 1
                        elif line.startswith("\t"):
                            style_indicators["tabs"] += 1
                except (OSError, UnicodeDecodeError):
                    continue

        return {
            "prefers_semicolons": style_indicators["semicolons"]
            > style_indicators["no_semicolons"],
            "quote_style": (
                "single"
                if style_indicators["single_quotes"] > style_indicators["double_quotes"]
                else "double"
            ),
            "indentation": (
                "spaces" if style_indicators["spaces"] > style_indicators["tabs"] else "tabs"
            ),
        }

    def _detect_naming_conventions(self, files: list[str]) -> dict[str, str]:
        """Detect naming conventions used in the project."""
        conventions = {
            "files": "kebab-case",  # Default assumption
            "components": "PascalCase",
            "functions": "camelCase",
        }

        # Analyze file names
        kebab_count = sum(1 for f in files if "-" in pathlib.Path(f).name)
        snake_count = sum(1 for f in files if "_" in pathlib.Path(f).name)

        if snake_count > kebab_count:
            conventions["files"] = "snake_case"

        return conventions

    def _analyze_file_structure(self, files: list[str]) -> dict[str, Any]:
        """Analyze project file structure patterns."""
        return {
            "has_components_dir": any("components" in f for f in files),
            "has_utils_dir": any("utils" in f for f in files),
            "has_types_dir": any("types" in f for f in files),
            "has_tests_colocated": any(".test." in f or ".spec." in f for f in files),
        }

    def _find_common_patterns(self, files: list[str]) -> list[str]:
        """Find common code patterns in the project."""
        patterns = []

        # Check for common frameworks/libraries
        if any("react" in f.lower() for f in files):
            patterns.append("React project")
        if any("next" in f.lower() for f in files):
            patterns.append("Next.js project")
        if any("tailwind" in f.lower() for f in files):
            patterns.append("Tailwind CSS")

        return patterns

    def _store_project_context(self, project_hash: str, patterns: dict[str, Any]) -> None:
        """Store project context in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for context_type, pattern_data in patterns.items():
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO project_context
                    (project_hash, context_type, pattern, frequency, effectiveness, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        project_hash,
                        context_type,
                        str(pattern_data),
                        1,
                        1.0,
                        datetime.now(),
                    ),
                )

            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()


def learning_memory_action(inputs: MemoryInputs) -> MemoryOutputs:
    """Main action interface for the learning memory system."""
    memory_system = LearningMemorySystem()

    if inputs.action_type == "record_fix":
        success = memory_system.record_fix_pattern(inputs)
        return MemoryOutputs(success=success)

    if inputs.action_type == "record_preference":
        success = memory_system.record_user_preference(
            inputs.user_id,
            inputs.context.get("preference_type", ""),
            inputs.context.get("preference_value", ""),
        )
        return MemoryOutputs(success=success)

    if inputs.action_type == "get_patterns":
        recommendations = memory_system.get_fix_recommendations(
            inputs.comment_type, inputs.file_path
        )
        confidence_scores = {rec["fix_type"]: rec["confidence"] for rec in recommendations}
        return MemoryOutputs(
            success=True,
            recommendations=[rec["fix_type"] for rec in recommendations],
            confidence_scores=confidence_scores,
        )

    if inputs.action_type == "get_preferences":
        preferences = memory_system.get_user_preferences(inputs.user_id)
        return MemoryOutputs(success=True, learned_preferences=preferences)

    return MemoryOutputs(success=False)
