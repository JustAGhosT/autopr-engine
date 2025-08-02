"""Cached authorization manager implementation."""

from .cache import PermissionCache
from .enterprise_manager import EnterpriseAuthorizationManager
from .models import AuthorizationContext, Permission, ResourceType


class CachedAuthorizationManager(EnterpriseAuthorizationManager):
    """Authorization manager with caching for improved performance"""

    def __init__(self, cache_ttl_seconds: int = 300):
        super().__init__()
        self.cache = PermissionCache(cache_ttl_seconds)

    def authorize(self, context: AuthorizationContext) -> bool:
        cached_result = self.cache.get(
            context.user_id, context.resource_type.value, context.resource_id, context.action.value
        )

        if cached_result is not None:
            return cached_result

        result = super().authorize(context)
        self.cache.set(
            context.user_id,
            context.resource_type.value,
            context.resource_id,
            context.action.value,
            result,
        )

        return result

    def grant_resource_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        permissions: set[Permission],
        granted_by: str,
    ) -> bool:
        result = super().grant_resource_permission(
            user_id, resource_type, resource_id, permissions, granted_by
        )
        if result:
            self.cache.invalidate_user(user_id)
            self.cache.invalidate_resource(resource_type.value, resource_id)
        return result

    def revoke_resource_permission(
        self, user_id: str, resource_type: ResourceType, resource_id: str
    ) -> bool:
        result = super().revoke_resource_permission(user_id, resource_type, resource_id)
        if result:
            self.cache.invalidate_user(user_id)
            self.cache.invalidate_resource(resource_type.value, resource_id)
        return result
