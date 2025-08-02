"""Permission caching for improved performance."""

from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class PermissionCache:
    """Cache for permission checks to improve performance."""

    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default TTL
        self.cache = {}
        self.ttl_seconds = ttl_seconds

    def _generate_cache_key(
        self, user_id: str, resource_type: str, resource_id: str, action: str
    ) -> str:
        """Generate cache key for permission check."""
        return f"{user_id}:{resource_type}:{resource_id}:{action}"

    def get(self, user_id: str, resource_type: str, resource_id: str, action: str) -> bool | None:
        """Get cached permission result."""
        cache_key = self._generate_cache_key(user_id, resource_type, resource_id, action)

        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]

            # Check if cache entry is still valid
            if datetime.utcnow().timestamp() - timestamp < self.ttl_seconds:
                logger.debug("Permission cache hit", cache_key=cache_key)
                return result
            else:
                # Remove expired entry
                del self.cache[cache_key]
                logger.debug("Permission cache expired", cache_key=cache_key)

        return None

    def set(self, user_id: str, resource_type: str, resource_id: str, action: str, result: bool):
        """Cache permission result."""
        cache_key = self._generate_cache_key(user_id, resource_type, resource_id, action)
        self.cache[cache_key] = (result, datetime.utcnow().timestamp())
        logger.debug("Permission cached", cache_key=cache_key, result=result)

    def invalidate_user(self, user_id: str):
        """Invalidate all cache entries for a user."""
        keys_to_remove = [key for key in self.cache.keys() if key.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            del self.cache[key]
        logger.debug(
            "User permission cache invalidated", user_id=user_id, count=len(keys_to_remove)
        )

    def invalidate_resource(self, resource_type: str, resource_id: str):
        """Invalidate all cache entries for a resource."""
        pattern = f":{resource_type}:{resource_id}:"
        keys_to_remove = [key for key in self.cache.keys() if pattern in key]
        for key in keys_to_remove:
            del self.cache[key]
        logger.debug(
            "Resource permission cache invalidated",
            resource_type=resource_type,
            resource_id=resource_id,
            count=len(keys_to_remove),
        )

    def clear(self):
        """Clear all cache entries."""
        count = len(self.cache)
        self.cache.clear()
        logger.debug("Permission cache cleared", count=count)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        now = datetime.utcnow().timestamp()
        valid_entries = sum(
            1 for _, timestamp in self.cache.values() if now - timestamp < self.ttl_seconds
        )

        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "ttl_seconds": self.ttl_seconds,
        }
