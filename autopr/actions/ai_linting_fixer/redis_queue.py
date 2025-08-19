"""
Redis Queue Support Module

Provides Redis-based distributed processing capabilities for AI linting operations.
This enables horizontal scaling across multiple workers and systems.
"""

from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
import json
import logging
import os
from pathlib import Path
import time
from typing import Any, TypedDict
import uuid

logger = logging.getLogger(__name__)

# Optional Redis dependency
try:
    import redis  # type: ignore[import-not-found, import-untyped]
    from redis.exceptions import (
        ConnectionError as RedisConnectionError,  # type: ignore[import-not-found, import-untyped]
    )
    from redis.exceptions import (
        RedisError,  # type: ignore[import-not-found, import-untyped]
    )

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    RedisError = Exception
    RedisConnectionError = Exception
    REDIS_AVAILABLE = False


class QueuePriority(Enum):
    """Priority levels for queue items."""

    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class QueuedIssue:
    """Represents a linting issue queued for distributed processing."""

    id: str
    session_id: str
    file_path: str
    line_number: int
    column_number: int
    error_code: str
    message: str
    line_content: str = ""
    priority: int = 5
    agent_type: str | None = None

    # Processing metadata
    created_at: datetime | None = None
    assigned_worker: str | None = None
    processing_started_at: datetime | None = None
    retry_count: int = 0
    max_retries: int = 3

    # Context information
    function_name: str | None = None
    class_name: str | None = None
    estimated_confidence: float = 0.7

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(UTC)
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO format
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat() if value else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueuedIssue":
        """Create from dictionary (JSON deserialization)."""
        # Convert ISO format back to datetime
        for key in ["created_at", "processing_started_at"]:
            if data.get(key):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)


@dataclass
class ProcessingResult:
    """Result of processing a queued issue."""

    issue_id: str
    success: bool
    fixed_content: str | None = None
    confidence_score: float = 0.0
    processing_time: float = 0.0
    error_message: str | None = None
    worker_id: str | None = None
    processed_at: datetime | None = None

    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if isinstance(data["processed_at"], datetime):
            data["processed_at"] = data["processed_at"].isoformat()
        return data


class RedisQueueManager:
    """Manages Redis-based queues for distributed AI linting processing."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        queue_prefix: str = "ai_linting",
        worker_id: str | None = None,
    ):
        """
        Initialize Redis queue manager.

        Args:
            redis_url: Redis connection URL
            queue_prefix: Prefix for all queue names
            worker_id: Unique identifier for this worker
        """
        if not REDIS_AVAILABLE:
            msg = "Redis is not available. Install with: pip install redis"
            raise ImportError(msg)

        self.redis_url = redis_url
        self.queue_prefix = queue_prefix
        self.worker_id = worker_id or f"worker_{uuid.uuid4().hex[:8]}"

        # Initialize Redis connection
        self.redis_client: Any = None
        self._connect()

        # Queue names
        self.pending_queue = f"{queue_prefix}:pending"
        self.processing_queue = f"{queue_prefix}:processing"
        self.results_queue = f"{queue_prefix}:results"
        self.failed_queue = f"{queue_prefix}:failed"
        self.worker_heartbeat = f"{queue_prefix}:workers:heartbeat"

        # Statistics
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = datetime.now(UTC)

    def _connect(self):
        """Establish Redis connection."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Connected to Redis: %s", self.redis_url)
        except Exception:
            logger.exception("Failed to connect to Redis")
            raise

    def is_connected(self) -> bool:
        """Check if Redis connection is active."""
        try:
            assert self.redis_client is not None
            self.redis_client.ping()
            return True
        except Exception:
            return False

    def _validate_redis_client(self) -> None:
        """Validate that Redis client is available."""
        if self.redis_client is None:
            msg = "Redis client is not initialized"
            raise RuntimeError(msg)

    def enqueue_issue(self, issue: QueuedIssue) -> bool:
        """Add an issue to the pending queue."""
        try:
            self._validate_redis_client()
            issue_data = {
                "id": issue.id,
                "file_path": str(issue.file_path),
                "issue_type": issue.issue_type,
                "message": issue.message,
                "line": issue.line,
                "column": issue.column,
                "severity": issue.severity,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.redis_client.lpush(self.issue_queue_key, json.dumps(issue_data))
            return True
        except Exception as e:
            logger.exception(f"Failed to enqueue issue: {e}")
            return False

    def dequeue_issue(self) -> QueuedIssue | None:
        """Remove and return the next issue from the queue."""
        try:
            self._validate_redis_client()
            result = self.redis_client.rpop(self.issue_queue_key)
            if result:
                data = json.loads(result)
                return QueuedIssue(
                    id=data["id"],
                    file_path=Path(data["file_path"]),
                    issue_type=data["issue_type"],
                    message=data["message"],
                    line=data["line"],
                    column=data["column"],
                    severity=data["severity"],
                )
            return None
        except Exception as e:
            logger.exception(f"Failed to dequeue issue: {e}")
            return None

    def get_queue_length(self) -> int:
        """Get the current number of issues in the queue."""
        try:
            self._validate_redis_client()
            return self.redis_client.llen(self.issue_queue_key)
        except Exception as e:
            logger.exception(f"Failed to get queue length: {e}")
            return 0

    def clear_queue(self) -> bool:
        """Clear all issues from the queue."""
        try:
            self._validate_redis_client()
            self.redis_client.delete(self.issue_queue_key)
            return True
        except Exception as e:
            logger.exception(f"Failed to clear queue: {e}")
            return False

    def get_queue_stats(self) -> dict:
        """Get statistics about the queue."""
        try:
            self._validate_redis_client()
            length = self.redis_client.llen(self.issue_queue_key)
            return {
                "queue_length": length,
                "queue_name": self.issue_queue_key,
                "status": "active" if length > 0 else "empty",
            }
        except Exception as e:
            logger.exception(f"Failed to get queue stats: {e}")
            return {
                "queue_length": 0,
                "queue_name": self.issue_queue_key,
                "status": "error",
            }

    def peek_queue(self, count: int = 5) -> list[QueuedIssue]:
        """Peek at the top issues in the queue without removing them."""
        try:
            self._validate_redis_client()
            results = self.redis_client.lrange(self.issue_queue_key, 0, count - 1)
            issues = []
            for result in results:
                data = json.loads(result)
                issues.append(
                    QueuedIssue(
                        id=data["id"],
                        file_path=Path(data["file_path"]),
                        issue_type=data["issue_type"],
                        message=data["message"],
                        line=data["line"],
                        column=data["column"],
                        severity=data["severity"],
                    )
                )
            return issues
        except Exception as e:
            logger.exception(f"Failed to peek queue: {e}")
            return []

    def remove_issue(self, issue_id: str) -> bool:
        """Remove a specific issue from the queue by ID."""
        try:
            self._validate_redis_client()
            # This is a simplified implementation - in practice you'd need to scan the queue
            # and remove the specific issue by matching its ID
            logger.warning(
                "Remove issue by ID not implemented - would need queue scanning"
            )
            return False
        except Exception as e:
            logger.exception(f"Failed to remove issue: {e}")
            return False

    def get_processing_status(self) -> dict:
        """Get the current processing status."""
        try:
            self._validate_redis_client()
            queue_length = self.redis_client.llen(self.issue_queue_key)
            processing_count = self.redis_client.get(self.processing_count_key) or 0

            return {
                "queue_length": queue_length,
                "processing_count": int(processing_count),
                "status": "processing" if int(processing_count) > 0 else "idle",
            }
        except Exception as e:
            logger.exception(f"Failed to get processing status: {e}")
            return {"queue_length": 0, "processing_count": 0, "status": "error"}

    def increment_processing_count(self) -> bool:
        """Increment the processing count."""
        try:
            self._validate_redis_client()
            self.redis_client.incr(self.processing_count_key)
            return True
        except Exception as e:
            logger.exception(f"Failed to increment processing count: {e}")
            return False

    def decrement_processing_count(self) -> bool:
        """Decrement the processing count."""
        try:
            self._validate_redis_client()
            self.redis_client.decr(self.processing_count_key)
            return True
        except Exception as e:
            logger.exception(f"Failed to decrement processing count: {e}")
            return False

    def reset_processing_count(self) -> bool:
        """Reset the processing count to 0."""
        try:
            self._validate_redis_client()
            self.redis_client.set(self.processing_count_key, 0)
            return True
        except Exception as e:
            logger.exception(f"Failed to reset processing count: {e}")
            return False

    def get_health_status(self) -> dict:
        """Get the health status of the Redis connection."""
        try:
            self._validate_redis_client()
            self.redis_client.ping()
            return {
                "status": "healthy",
                "connection": "active",
                "queue_accessible": True,
            }
        except Exception as e:
            logger.exception(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "connection": "error",
                "queue_accessible": False,
                "error": str(e),
            }

    def enqueue_issues(self, issues: list[QueuedIssue]) -> int:
        """Add multiple issues to the pending queue."""
        enqueued_count = 0

        try:
            # Batch operation for efficiency
            mapping = {}
            for issue in issues:
                issue_data = json.dumps(issue.to_dict())
                score = issue.priority * 1000 + int(time.time())
                mapping[issue_data] = score

            if mapping:
                assert self.redis_client is not None
                self.redis_client.zadd(self.pending_queue, mapping)
                enqueued_count = len(mapping)
                logger.info(f"Enqueued {enqueued_count} issues in batch")

        except Exception as e:
            logger.exception(f"Failed to enqueue issues in batch: {e}")

        return enqueued_count

    def complete_issue(self, issue_id: str, result: ProcessingResult) -> bool:
        """Mark an issue as completed."""
        try:
            # Remove from processing queue
            assert self.redis_client is not None
            self.redis_client.hdel(self.processing_queue, issue_id)

            # Add result
            result_data = json.dumps(result.to_dict())
            assert self.redis_client is not None
            self.redis_client.hset(self.results_queue, issue_id, result_data)

            # Update statistics
            if result.success:
                self.processed_count += 1
            else:
                self.failed_count += 1

            logger.debug("Completed issue %s with success=%s", issue_id, result.success)
            return True

        except Exception as e:
            logger.exception(f"Failed to complete issue {issue_id}: {e}")
            return False

    def fail_issue(self, issue: QueuedIssue, error_message: str) -> bool:
        """Handle a failed issue processing."""
        try:
            # Remove from processing queue
            assert self.redis_client is not None
            self.redis_client.hdel(self.processing_queue, issue.id)

            # Check if we should retry
            if issue.retry_count < issue.max_retries:
                issue.retry_count += 1
                issue.assigned_worker = None
                issue.processing_started_at = None

                # Re-enqueue with lower priority
                issue.priority = max(1, issue.priority - 1)
                return self.enqueue_issue(issue)
            # Move to failed queue
            failed_data = json.dumps(
                {
                    **issue.to_dict(),
                    "final_error": error_message,
                    "failed_at": datetime.now(UTC).isoformat(),
                }
            )
            assert self.redis_client is not None
            self.redis_client.hset(self.failed_queue, issue.id, failed_data)
            self.failed_count += 1

            logger.warning(
                "Issue %s failed permanently after %d retries",
                issue.id,
                issue.retry_count,
            )
            return True

        except Exception as e:
            logger.exception(f"Failed to handle issue failure {issue.id}: {e}")
            return False

    def get_queue_statistics(self) -> dict[str, Any]:
        """Get comprehensive queue statistics."""
        try:
            assert self.redis_client is not None
            return {
                "pending_count": self.redis_client.zcard(self.pending_queue),
                "processing_count": self.redis_client.hlen(self.processing_queue),
                "results_count": self.redis_client.hlen(self.results_queue),
                "failed_count": self.redis_client.hlen(self.failed_queue),
                "worker_stats": {
                    "worker_id": self.worker_id,
                    "processed_count": self.processed_count,
                    "failed_count": self.failed_count,
                    "uptime_seconds": (
                        datetime.now(UTC) - self.start_time
                    ).total_seconds(),
                },
                "active_workers": self._get_active_workers(),
            }

        except Exception as e:
            logger.exception(f"Failed to get queue statistics: {e}")
            return {}

    def _get_active_workers(self) -> list[dict[str, Any]]:
        """Get list of active workers."""
        try:
            cutoff_time = datetime.now(UTC) - timedelta(minutes=5)
            cutoff_timestamp = cutoff_time.timestamp()

            # Get workers that have sent heartbeat in last 5 minutes
            active_workers = []
            assert self.redis_client is not None
            for worker_id, last_seen in self.redis_client.hgetall(
                self.worker_heartbeat
            ).items():
                if float(last_seen) > cutoff_timestamp:
                    active_workers.append(
                        {
                            "worker_id": worker_id,
                            "last_seen": datetime.fromtimestamp(
                                float(last_seen), tz=UTC
                            ).isoformat(),
                        }
                    )

            return active_workers

        except Exception:
            logger.exception("Failed to get active workers")
            return []

    def send_heartbeat(self):
        """Send worker heartbeat."""
        try:
            assert self.redis_client is not None
            self.redis_client.hset(self.worker_heartbeat, self.worker_id, time.time())
        except Exception:
            logger.exception("Failed to send heartbeat")

    def cleanup_stale_processing(self, timeout_minutes: int = 30):
        """Clean up stale processing items."""
        try:
            cutoff_time = datetime.now(UTC) - timedelta(minutes=timeout_minutes)

            stale_count = 0
            assert self.redis_client is not None
            for issue_id, issue_data in self.redis_client.hgetall(
                self.processing_queue
            ).items():
                issue = QueuedIssue.from_dict(json.loads(issue_data))

                if (
                    issue.processing_started_at
                    and issue.processing_started_at < cutoff_time
                ):
                    # Re-enqueue stale issue
                    issue.assigned_worker = None
                    issue.processing_started_at = None
                    issue.retry_count += 1

                    self.redis_client.hdel(self.processing_queue, issue_id)

                    if issue.retry_count <= issue.max_retries:
                        self.enqueue_issue(issue)
                    else:
                        self.fail_issue(issue, "Processing timeout")

                    stale_count += 1

            if stale_count > 0:
                logger.info("Cleaned up %d stale processing items", stale_count)

        except Exception:
            logger.exception("Failed to cleanup stale processing")

    def clear_all_queues(self):
        """Clear all queues (for testing/debugging)."""
        try:
            assert self.redis_client is not None
            self.redis_client.delete(
                self.pending_queue,
                self.processing_queue,
                self.results_queue,
                self.failed_queue,
            )
            logger.info("Cleared all queues")
        except Exception:
            logger.exception("Failed to clear queues")


class DistributedProcessor:
    """Coordinates distributed processing of AI linting tasks."""

    def __init__(
        self,
        queue_manager: RedisQueueManager,
        processor_function: Callable[[QueuedIssue], ProcessingResult],
    ):
        """
        Initialize distributed processor.

        Args:
            queue_manager: Redis queue manager
            processor_function: Function to process individual issues
        """
        self.queue_manager = queue_manager
        self.processor_function = processor_function
        self.running = False
        self.heartbeat_interval = 60  # seconds
        self.last_heartbeat: float = 0.0

    def start_processing(self, max_iterations: int | None = None):
        """Start processing issues from the queue."""
        self.running = True
        iteration_count = 0

        logger.info(
            "Started distributed processing (worker: %s)", self.queue_manager.worker_id
        )

        try:
            while self.running:
                if max_iterations and iteration_count >= max_iterations:
                    break

                # Send periodic heartbeat
                current_time = time.time()
                if current_time - self.last_heartbeat > self.heartbeat_interval:
                    self.queue_manager.send_heartbeat()
                    self.last_heartbeat = current_time

                # Get next issue
                issue = self.queue_manager.dequeue_issue(timeout=10)
                if not issue:
                    continue  # Timeout, try again

                # Process the issue
                try:
                    start_time = time.time()
                    result = self.processor_function(issue)
                    processing_time = time.time() - start_time

                    result.processing_time = processing_time
                    result.worker_id = self.queue_manager.worker_id

                    self.queue_manager.complete_issue(issue.id, result)

                except Exception as e:
                    logger.exception("Error processing issue %s: %s", issue.id, e)
                    self.queue_manager.fail_issue(issue, str(e))

                iteration_count += 1

        except KeyboardInterrupt:
            logger.info("Processing interrupted by user")
        except Exception:
            logger.exception("Unexpected error in processing loop")
        finally:
            self.running = False
            logger.info("Stopped distributed processing")

    def stop_processing(self):
        """Stop processing issues."""
        self.running = False


# Redis configuration helper
class RedisConfig:
    """Helper for Redis configuration."""

    class RedisEnvConfig(TypedDict, total=False):
        redis_url: str
        queue_prefix: str
        worker_id: str

    @staticmethod
    def from_environment() -> "RedisConfig.RedisEnvConfig":
        """Get Redis configuration from environment variables."""

        redis_url_env = os.getenv("REDIS_URL")
        redis_url: str
        redis_url = (
            "redis://localhost:6379/0" if redis_url_env is None else redis_url_env
        )
        queue_prefix_env = os.getenv("AI_LINTING_QUEUE_PREFIX")
        queue_prefix: str
        queue_prefix = "ai_linting" if queue_prefix_env is None else queue_prefix_env
        config: RedisConfig.RedisEnvConfig = {}
        config["redis_url"] = redis_url
        config["queue_prefix"] = queue_prefix
        worker_id: str = os.getenv("AI_LINTING_WORKER_ID") or ""
        config["worker_id"] = worker_id
        return config

    @staticmethod
    def create_queue_manager(**kwargs) -> RedisQueueManager | None:
        """Create a Redis queue manager with environment configuration."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis is not available - distributed processing disabled")
            return None

        try:
            base_config = RedisConfig.from_environment()
            # Merge kwargs skipping None values to satisfy type expectations
            merged: RedisConfig.RedisEnvConfig = {}
            merged.update(base_config)
            redis_url_kw = kwargs.get("redis_url")
            if redis_url_kw is not None:
                merged["redis_url"] = str(redis_url_kw)
            queue_prefix_kw = kwargs.get("queue_prefix")
            if queue_prefix_kw is not None:
                merged["queue_prefix"] = str(queue_prefix_kw)
            worker_id_kw = kwargs.get("worker_id")
            if worker_id_kw is not None:
                merged["worker_id"] = str(worker_id_kw)
            return RedisQueueManager(**merged)

        except Exception:
            logger.exception("Failed to create Redis queue manager")
            return None


# Global instance (optional)
_global_queue_manager = None


def get_global_queue_manager() -> RedisQueueManager | None:
    """Get or create the global queue manager."""
    global _global_queue_manager

    if _global_queue_manager is None:
        _global_queue_manager = RedisConfig.create_queue_manager()

    return _global_queue_manager
