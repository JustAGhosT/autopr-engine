"""Tests for dashboard storage backends.

Note: This file uses pytest assertions which are the standard testing pattern.
The B101 warnings about assert are expected and correct for test files.
"""
# ruff: noqa: S101

import time
from autopr.dashboard.storage import (
    InMemoryStorage,
    RedisStorage,
    get_storage,
    get_storage_backend,
)


class TestInMemoryStorage:
    """Test InMemoryStorage backend."""

    def test_get_set_basic(self):
        """Test basic get/set operations."""
        storage = InMemoryStorage()
        storage.set("key1", "value1")
        assert storage.get("key1") == "value1"
        assert storage.get("nonexistent") is None
        assert storage.get("nonexistent", "default") == "default"

    def test_get_set_complex_types(self):
        """Test get/set with complex types."""
        storage = InMemoryStorage()
        data = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        storage.set("complex", data)
        assert storage.get("complex") == data

    def test_ttl_expiration(self):
        """Test TTL expiration for keys."""
        storage = InMemoryStorage()
        storage.set("expires", "soon", ttl=1)
        assert storage.get("expires") == "soon"
        time.sleep(1.1)
        assert storage.get("expires") is None

    def test_ttl_no_expiration(self):
        """Test keys without TTL don't expire."""
        storage = InMemoryStorage()
        storage.set("permanent", "value")
        time.sleep(0.1)
        assert storage.get("permanent") == "value"

    def test_increment(self):
        """Test atomic increment."""
        storage = InMemoryStorage()
        assert storage.increment("counter") == 1
        assert storage.increment("counter") == 2
        assert storage.increment("counter", 5) == 7

    def test_increment_expired_key(self):
        """Test increment on expired key."""
        storage = InMemoryStorage()
        storage.set("counter", 10, ttl=1)
        time.sleep(1.1)
        assert storage.increment("counter") == 1

    def test_append_to_list(self):
        """Test append to list."""
        storage = InMemoryStorage()
        storage.append_to_list("items", "a")
        storage.append_to_list("items", "b")
        assert storage.get_list("items") == ["a", "b"]

    def test_append_to_list_max_length(self):
        """Test list truncation at max length."""
        storage = InMemoryStorage()
        for i in range(10):
            storage.append_to_list("items", i, max_length=5)
        items = storage.get_list("items")
        assert len(items) == 5
        assert items == [5, 6, 7, 8, 9]

    def test_update_dict(self):
        """Test dictionary update."""
        storage = InMemoryStorage()
        storage.update_dict("data", "field1", "value1")
        storage.update_dict("data", "field2", "value2")
        assert storage.get_dict("data") == {"field1": "value1", "field2": "value2"}

    def test_initialize_if_empty(self):
        """Test initialize only when empty."""
        storage = InMemoryStorage()
        storage.initialize_if_empty("key", "initial")
        assert storage.get("key") == "initial"
        storage.initialize_if_empty("key", "new_value")
        assert storage.get("key") == "initial"

    def test_is_available(self):
        """Test availability check."""
        storage = InMemoryStorage()
        assert storage.is_available() is True


class TestRedisStorageFallback:
    """Test RedisStorage fallback behavior when Redis is unavailable."""

    def test_unavailable_redis(self):
        """Test graceful fallback when Redis is unavailable."""
        storage = RedisStorage(redis_url="redis://invalid:6379/0")
        assert storage.is_available() is False
        # Operations should return defaults without raising
        assert storage.get("key") is None
        assert storage.get("key", "default") == "default"
        storage.set("key", "value")  # Should not raise
        assert storage.increment("counter") == 0
        assert storage.get_list("items") == []
        assert storage.get_dict("data") == {}


class TestGetStorageBackend:
    """Test storage backend factory."""

    def test_default_is_memory(self, monkeypatch):
        """Test default backend is in-memory."""
        monkeypatch.delenv("AUTOPR_STORAGE_BACKEND", raising=False)
        # Clear singleton
        import autopr.dashboard.storage as storage_module
        storage_module._storage = None

        storage = get_storage_backend()
        assert isinstance(storage, InMemoryStorage)

    def test_explicit_memory_backend(self, monkeypatch):
        """Test explicit memory backend selection."""
        monkeypatch.setenv("AUTOPR_STORAGE_BACKEND", "memory")
        import autopr.dashboard.storage as storage_module
        storage_module._storage = None

        storage = get_storage_backend()
        assert isinstance(storage, InMemoryStorage)

    def test_redis_fallback_to_memory(self, monkeypatch):
        """Test Redis falls back to memory when unavailable."""
        monkeypatch.setenv("AUTOPR_STORAGE_BACKEND", "redis")
        monkeypatch.setenv("REDIS_URL", "redis://invalid:6379/0")
        import autopr.dashboard.storage as storage_module
        storage_module._storage = None

        storage = get_storage_backend()
        # Should fall back to InMemoryStorage
        assert isinstance(storage, InMemoryStorage)


class TestGetStorageSingleton:
    """Test singleton storage instance."""

    def test_singleton(self, monkeypatch):
        """Test get_storage returns same instance."""
        monkeypatch.delenv("AUTOPR_STORAGE_BACKEND", raising=False)
        import autopr.dashboard.storage as storage_module
        storage_module._storage = None

        storage1 = get_storage()
        storage2 = get_storage()
        assert storage1 is storage2
