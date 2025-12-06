"""Dashboard State Storage Backends.

Provides persistent storage for dashboard state with multiple backends:
- InMemoryStorage: Fast, non-persistent (default for development)
- RedisStorage: Persistent, shared across instances (for production)

Configure via AUTOPR_STORAGE_BACKEND environment variable:
- "memory" (default): In-memory storage
- "redis": Redis storage (requires REDIS_URL)
"""

import json
import logging
import os
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for dashboard state storage."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value with optional TTL in seconds."""
        pass

    @abstractmethod
    def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increment a counter and return new value."""
        pass

    @abstractmethod
    def append_to_list(self, key: str, value: Any, max_length: int = 50) -> None:
        """Append to a list, keeping only the last max_length items."""
        pass

    @abstractmethod
    def get_list(self, key: str) -> list[Any]:
        """Get a list by key."""
        pass

    @abstractmethod
    def update_dict(self, key: str, field: str, value: Any) -> None:
        """Update a field in a dictionary."""
        pass

    @abstractmethod
    def get_dict(self, key: str) -> dict[str, Any]:
        """Get a dictionary by key."""
        pass

    @abstractmethod
    def initialize_if_empty(self, key: str, value: Any) -> None:
        """Set a value only if key doesn't exist."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if storage backend is available."""
        pass


class InMemoryStorage(StorageBackend):
    """In-memory storage backend.

    Fast but not persistent. Data is lost on restart.
    Suitable for development and single-instance deployments.
    """

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._lock = threading.Lock()
        logger.info("Using in-memory storage backend")

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        with self._lock:
            self._data[key] = value
        # Note: TTL not implemented for in-memory storage

    def increment(self, key: str, amount: int = 1) -> int:
        with self._lock:
            current = self._data.get(key, 0)
            new_value = current + amount
            self._data[key] = new_value
            return new_value

    def append_to_list(self, key: str, value: Any, max_length: int = 50) -> None:
        with self._lock:
            if key not in self._data:
                self._data[key] = []
            self._data[key].append(value)
            if len(self._data[key]) > max_length:
                self._data[key] = self._data[key][-max_length:]

    def get_list(self, key: str) -> list[Any]:
        with self._lock:
            return list(self._data.get(key, []))

    def update_dict(self, key: str, field: str, value: Any) -> None:
        with self._lock:
            if key not in self._data:
                self._data[key] = {}
            self._data[key][field] = value

    def get_dict(self, key: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._data.get(key, {}))

    def initialize_if_empty(self, key: str, value: Any) -> None:
        with self._lock:
            if key not in self._data:
                self._data[key] = value

    def is_available(self) -> bool:
        return True


class RedisStorage(StorageBackend):
    """Redis storage backend.

    Persistent and shareable across multiple instances.
    Suitable for production deployments.

    Requires REDIS_URL environment variable.
    """

    def __init__(self, redis_url: str | None = None, key_prefix: str = "autopr:dashboard:"):
        self._key_prefix = key_prefix
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None
        self._available = False
        self._connect()

    def _connect(self) -> None:
        """Connect to Redis."""
        try:
            import redis
            self._client = redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self._client.ping()
            self._available = True
            logger.info(f"Connected to Redis at {self._redis_url.split('@')[-1]}")
        except ImportError:
            logger.error("redis package not installed. Install with: pip install redis")
            self._available = False
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory.")
            self._available = False

    def _key(self, key: str) -> str:
        """Get prefixed key."""
        return f"{self._key_prefix}{key}"

    def get(self, key: str, default: Any = None) -> Any:
        if not self._available:
            return default
        try:
            value = self._client.get(self._key(key))
            if value is None:
                return default
            return json.loads(value)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return default

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if not self._available:
            return
        try:
            serialized = json.dumps(value)
            if ttl:
                self._client.setex(self._key(key), ttl, serialized)
            else:
                self._client.set(self._key(key), serialized)
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    def increment(self, key: str, amount: int = 1) -> int:
        if not self._available:
            return 0
        try:
            return self._client.incrby(self._key(key), amount)
        except Exception as e:
            logger.error(f"Redis increment error: {e}")
            return 0

    def append_to_list(self, key: str, value: Any, max_length: int = 50) -> None:
        if not self._available:
            return
        try:
            prefixed_key = self._key(key)
            serialized = json.dumps(value)
            pipe = self._client.pipeline()
            pipe.rpush(prefixed_key, serialized)
            pipe.ltrim(prefixed_key, -max_length, -1)
            pipe.execute()
        except Exception as e:
            logger.error(f"Redis append_to_list error: {e}")

    def get_list(self, key: str) -> list[Any]:
        if not self._available:
            return []
        try:
            items = self._client.lrange(self._key(key), 0, -1)
            return [json.loads(item) for item in items]
        except Exception as e:
            logger.error(f"Redis get_list error: {e}")
            return []

    def update_dict(self, key: str, field: str, value: Any) -> None:
        if not self._available:
            return
        try:
            self._client.hset(self._key(key), field, json.dumps(value))
        except Exception as e:
            logger.error(f"Redis update_dict error: {e}")

    def get_dict(self, key: str) -> dict[str, Any]:
        if not self._available:
            return {}
        try:
            data = self._client.hgetall(self._key(key))
            return {k: json.loads(v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"Redis get_dict error: {e}")
            return {}

    def initialize_if_empty(self, key: str, value: Any) -> None:
        if not self._available:
            return
        try:
            prefixed_key = self._key(key)
            if not self._client.exists(prefixed_key):
                self._client.set(prefixed_key, json.dumps(value))
        except Exception as e:
            logger.error(f"Redis initialize_if_empty error: {e}")

    def is_available(self) -> bool:
        return self._available


def get_storage_backend() -> StorageBackend:
    """Get configured storage backend.

    Configure via environment variables:
    - AUTOPR_STORAGE_BACKEND: "memory" or "redis" (default: "memory")
    - REDIS_URL: Redis connection URL (required if backend is "redis")

    Returns:
        Configured storage backend instance.
    """
    backend_type = os.getenv("AUTOPR_STORAGE_BACKEND", "memory").lower()

    if backend_type == "redis":
        redis_storage = RedisStorage()
        if redis_storage.is_available():
            return redis_storage
        logger.warning("Redis not available, falling back to in-memory storage")

    return InMemoryStorage()


# Singleton storage instance
_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Get or create the singleton storage instance."""
    global _storage
    if _storage is None:
        _storage = get_storage_backend()
    return _storage
