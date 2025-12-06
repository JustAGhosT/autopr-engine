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
import time
from abc import ABC, abstractmethod
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
    Supports TTL (time-to-live) for automatic key expiration.
    """

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}  # key -> expiry timestamp
        self._lock = threading.Lock()
        logger.info("Using in-memory storage backend")

    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired."""
        if key not in self._expiry:
            return False
        return time.time() > self._expiry[key]

    def _cleanup_expired(self, key: str) -> None:
        """Remove key if expired."""
        if self._is_expired(key):
            self._data.pop(key, None)
            self._expiry.pop(key, None)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            self._cleanup_expired(key)
            return self._data.get(key, default)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        with self._lock:
            self._data[key] = value
            if ttl is not None:
                self._expiry[key] = time.time() + ttl
            elif key in self._expiry:
                del self._expiry[key]

    def increment(self, key: str, amount: int = 1) -> int:
        with self._lock:
            self._cleanup_expired(key)
            current = self._data.get(key, 0)
            new_value = current + amount
            self._data[key] = new_value
            return new_value

    def append_to_list(self, key: str, value: Any, max_length: int = 50) -> None:
        with self._lock:
            self._cleanup_expired(key)
            if key not in self._data:
                self._data[key] = []
            self._data[key].append(value)
            if len(self._data[key]) > max_length:
                self._data[key] = self._data[key][-max_length:]

    def get_list(self, key: str) -> list[Any]:
        with self._lock:
            self._cleanup_expired(key)
            return list(self._data.get(key, []))

    def update_dict(self, key: str, field: str, value: Any) -> None:
        with self._lock:
            self._cleanup_expired(key)
            if key not in self._data:
                self._data[key] = {}
            self._data[key][field] = value

    def get_dict(self, key: str) -> dict[str, Any]:
        with self._lock:
            self._cleanup_expired(key)
            return dict(self._data.get(key, {}))

    def initialize_if_empty(self, key: str, value: Any) -> None:
        with self._lock:
            self._cleanup_expired(key)
            if key not in self._data:
                self._data[key] = value

    def is_available(self) -> bool:
        return True


class RedisStorage(StorageBackend):
    """Redis storage backend.

    Persistent and shareable across multiple instances.
    Suitable for production deployments.
    Includes automatic reconnection on connection failures.

    Requires REDIS_URL environment variable.
    """

    # Minimum seconds between reconnection attempts
    RECONNECT_COOLDOWN = 5.0

    def __init__(self, redis_url: str | None = None, key_prefix: str = "autopr:dashboard:"):
        self._key_prefix = key_prefix
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None
        self._available = False
        self._last_reconnect_attempt = 0.0
        self._lock = threading.Lock()
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

    def _try_reconnect(self) -> bool:
        """Attempt to reconnect to Redis with cooldown.

        Returns:
            True if reconnection succeeded, False otherwise.
        """
        now = time.time()
        with self._lock:
            if now - self._last_reconnect_attempt < self.RECONNECT_COOLDOWN:
                return False
            self._last_reconnect_attempt = now

        logger.info("Attempting to reconnect to Redis...")
        self._connect()
        return self._available

    def _execute_with_retry(self, operation: str, func, default: Any = None):
        """Execute a Redis operation with automatic retry on connection failure.

        Args:
            operation: Name of the operation for logging.
            func: Callable that performs the Redis operation.
            default: Default value to return on failure.

        Returns:
            Result of func() on success, default on failure.
        """
        if not self._available:
            # Try to reconnect if not available
            if not self._try_reconnect():
                return default

        try:
            return func()
        except Exception as e:
            # Check if it's a connection error
            error_str = str(e).lower()
            is_connection_error = any(
                term in error_str
                for term in ["connection", "timeout", "refused", "reset", "broken pipe"]
            )

            if is_connection_error:
                logger.warning(f"Redis connection error in {operation}: {e}")
                self._available = False
                # Try one reconnection
                if self._try_reconnect():
                    try:
                        return func()
                    except Exception as retry_error:
                        logger.error(f"Redis {operation} failed after reconnect: {retry_error}")
            else:
                logger.error(f"Redis {operation} error: {e}")

            return default

    def _key(self, key: str) -> str:
        """Get prefixed key."""
        return f"{self._key_prefix}{key}"

    def get(self, key: str, default: Any = None) -> Any:
        def _get():
            value = self._client.get(self._key(key))
            if value is None:
                return default
            return json.loads(value)
        return self._execute_with_retry("get", _get, default)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        def _set():
            serialized = json.dumps(value)
            if ttl:
                self._client.setex(self._key(key), ttl, serialized)
            else:
                self._client.set(self._key(key), serialized)
            return True
        self._execute_with_retry("set", _set, None)

    def increment(self, key: str, amount: int = 1) -> int:
        def _increment():
            return self._client.incrby(self._key(key), amount)
        result = self._execute_with_retry("increment", _increment, 0)
        return result if isinstance(result, int) else 0

    def append_to_list(self, key: str, value: Any, max_length: int = 50) -> None:
        def _append():
            prefixed_key = self._key(key)
            serialized = json.dumps(value)
            pipe = self._client.pipeline()
            pipe.rpush(prefixed_key, serialized)
            pipe.ltrim(prefixed_key, -max_length, -1)
            pipe.execute()
            return True
        self._execute_with_retry("append_to_list", _append, None)

    def get_list(self, key: str) -> list[Any]:
        def _get_list():
            items = self._client.lrange(self._key(key), 0, -1)
            return [json.loads(item) for item in items]
        result = self._execute_with_retry("get_list", _get_list, [])
        return result if isinstance(result, list) else []

    def update_dict(self, key: str, field: str, value: Any) -> None:
        def _update():
            self._client.hset(self._key(key), field, json.dumps(value))
            return True
        self._execute_with_retry("update_dict", _update, None)

    def get_dict(self, key: str) -> dict[str, Any]:
        def _get_dict():
            data = self._client.hgetall(self._key(key))
            return {k: json.loads(v) for k, v in data.items()}
        result = self._execute_with_retry("get_dict", _get_dict, {})
        return result if isinstance(result, dict) else {}

    def initialize_if_empty(self, key: str, value: Any) -> None:
        def _initialize():
            prefixed_key = self._key(key)
            # Use atomic SET NX to avoid race condition
            self._client.set(prefixed_key, json.dumps(value), nx=True)
            return True
        self._execute_with_retry("initialize_if_empty", _initialize, None)

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
