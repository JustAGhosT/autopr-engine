"""Audited authorization manager implementation."""

from datetime import datetime

from .audit_logger import AuthorizationAuditLogger
from .cached_manager import CachedAuthorizationManager
from .models import AuthorizationContext, Permission, ResourceType


class AuditedAuthorizationManager(CachedAuthorizationManager):
    """Authorization manager with built-in auditing"""

    def __init__(self, cache_ttl_seconds: int = 300, audit_log_file: str | None = None):
        super().__init__(cache_ttl_seconds)
        self.audit_logger = AuthorizationAuditLogger(audit_log_file)

    def authorize(self, context: AuthorizationContext) -> bool:
        start_time = datetime.utcnow()
        result = super().authorize(context)
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.audit_logger.log_authorization_check(context, result, duration_ms)

        if not result:
            self.audit_logger.log_access_denied(context)

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
            self.audit_logger.log_permission_grant(
                user_id,
                resource_type.value,
                resource_id,
                [p.value for p in permissions],
                granted_by,
            )
        return result

    def revoke_resource_permission(
        self, user_id: str, resource_type: ResourceType, resource_id: str
    ) -> bool:
        result = super().revoke_resource_permission(user_id, resource_type, resource_id)
        if result:
            self.audit_logger.log_permission_revoke(
                user_id, resource_type.value, resource_id, "system"
            )
        return result
