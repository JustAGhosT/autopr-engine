"""Utility functions for authorization operations."""

from pathlib import Path
from typing import Any, ClassVar, Union, cast

import structlog

from .audit import AuthorizationAuditLogger
from .managers import (
    AuditedAuthorizationManager,
    CachedAuthorizationManager,
    EnterpriseAuthorizationManager,
)
from .models import AuthorizationContext, Permission, ResourceType

logger = structlog.get_logger(__name__)


ManagerType = Union[
    AuditedAuthorizationManager,
    CachedAuthorizationManager,
    EnterpriseAuthorizationManager,
]


class _AuthSingleton:
    """Simple holder to avoid using module-level ``global`` updates."""

    manager: ClassVar[Any | None] = None
    access_logger: ClassVar[AuthorizationAuditLogger | None] = None


def get_authorization_manager(
    *,
    use_cache: bool = True,
    cache_ttl_seconds: int = 300,
    enable_audit: bool = True,
    audit_log_file: str | None = None,
) -> Any:
    """
    Get global authorization manager instance with appropriate capabilities.

    Args:
        use_cache: Whether to use cached authorization (improves performance)
        cache_ttl_seconds: Time-to-live for cache entries in seconds
        enable_audit: Whether to enable audit logging
        audit_log_file: Path to audit log file (if None, logs to structlog only)

    Returns:
        An instance of the appropriate authorization manager
    """
    if _AuthSingleton.manager is None:
        # Determine audit log file if not provided but enabled
        if enable_audit and not audit_log_file:
            log_dir = Path("logs")
            audit_log_file = str(log_dir / "authorization_audit.log")

        # Create the appropriate manager based on requested capabilities
        if enable_audit:
            _AuthSingleton.manager = AuditedAuthorizationManager(
                cache_ttl_seconds=cache_ttl_seconds if use_cache else 0,
                audit_log_file=audit_log_file,
            )
            logger.info(
                "Created AuditedAuthorizationManager",
                cache_enabled=use_cache,
                cache_ttl=cache_ttl_seconds,
                audit_log_file=audit_log_file,
            )
        elif use_cache:
            _AuthSingleton.manager = CachedAuthorizationManager(cache_ttl_seconds=cache_ttl_seconds)
            logger.info("Created CachedAuthorizationManager", cache_ttl=cache_ttl_seconds)
        else:
            _AuthSingleton.manager = EnterpriseAuthorizationManager()
            logger.info("Created basic EnterpriseAuthorizationManager")

    return cast("Any", _AuthSingleton.manager)


def get_access_logger() -> AuthorizationAuditLogger:
    """Get global access logger instance."""
    if _AuthSingleton.access_logger is None:
        _AuthSingleton.access_logger = AuthorizationAuditLogger()
    return _AuthSingleton.access_logger


def create_project_authorization_context(
    user_id: str, roles: list[str], project_id: str, action: str
) -> AuthorizationContext:
    """Create authorization context for project operations."""
    return AuthorizationContext(
        user_id=user_id,
        roles=roles,
        permissions=[],
        resource_type=ResourceType.PROJECT,
        resource_id=project_id,
        action=Permission(action),
    )


def create_repository_authorization_context(
    user_id: str, roles: list[str], repository_id: str, action: str
) -> AuthorizationContext:
    """Create authorization context for repository operations."""
    return AuthorizationContext(
        user_id=user_id,
        roles=roles,
        permissions=[],
        resource_type=ResourceType.REPOSITORY,
        resource_id=repository_id,
        action=Permission(action),
    )


def create_workflow_authorization_context(
    user_id: str, roles: list[str], workflow_id: str, action: str
) -> AuthorizationContext:
    """Create authorization context for workflow operations."""
    return AuthorizationContext(
        user_id=user_id,
        roles=roles,
        permissions=[],
        resource_type=ResourceType.WORKFLOW,
        resource_id=workflow_id,
        action=Permission(action),
    )


def create_template_authorization_context(
    user_id: str, roles: list[str], template_id: str, action: str
) -> AuthorizationContext:
    """Create authorization context for template operations."""
    return AuthorizationContext(
        user_id=user_id,
        roles=roles,
        permissions=[],
        resource_type=ResourceType.TEMPLATE,
        resource_id=template_id,
        action=Permission(action),
    )


def authorize_request(
    user_id: str,
    roles: list[str],
    resource_type: str,
    resource_id: str,
    action: str,
    additional_context: dict[str, Any] | None = None,
) -> bool:
    """Convenience function for authorization checks."""
    auth_manager = get_authorization_manager()
    access_logger = get_access_logger()

    context = AuthorizationContext(
        user_id=user_id,
        roles=roles,
        permissions=[],
        resource_type=ResourceType(resource_type),
        resource_id=resource_id,
        action=Permission(action),
        additional_context=additional_context or {},
    )

    granted = auth_manager.authorize(context)
    access_logger.log_authorization_check(context, granted)

    return bool(granted)


def validate_permission_hierarchy(permissions: list[str]) -> bool:
    """Validate that permission hierarchy is respected."""
    permission_levels = {
        Permission.READ.value: 1,
        Permission.WRITE.value: 2,
        Permission.CREATE.value: 2,
        Permission.UPDATE.value: 3,
        Permission.DELETE.value: 4,
        Permission.ADMIN.value: 5,
        Permission.MANAGE.value: 5,
        Permission.EXECUTE.value: 3,
    }

    READ_REQUIRED_LEVEL = 3
    WRITE_REQUIRED_LEVEL = 4

    max_level = max(permission_levels.get(p, 0) for p in permissions)

    missing_required = (
        max_level >= READ_REQUIRED_LEVEL and Permission.READ.value not in permissions
    ) or (max_level >= WRITE_REQUIRED_LEVEL and Permission.WRITE.value not in permissions)
    return not missing_required


def get_effective_permissions(
    user_roles: list[str],
    explicit_permissions: list[str],
    *,
    resource_owner: bool = False,
) -> list[str]:
    """Calculate effective permissions for a user."""
    effective_permissions = set(explicit_permissions)

    # Add role-based permissions
    role_permissions = {
        "viewer": [Permission.READ.value],
        "contributor": [
            Permission.READ.value,
            Permission.WRITE.value,
            Permission.CREATE.value,
        ],
        "maintainer": [
            Permission.READ.value,
            Permission.WRITE.value,
            Permission.CREATE.value,
            Permission.UPDATE.value,
            Permission.DELETE.value,
        ],
        "admin": [p.value for p in Permission],
    }

    for role in user_roles:
        if role in role_permissions:
            effective_permissions.update(role_permissions[role])

    # Resource owners get all permissions
    if resource_owner:
        effective_permissions.update([p.value for p in Permission])

    return list(effective_permissions)


def check_permission_conflicts(permissions: list[str]) -> list[str]:
    """Check for conflicting permissions."""
    conflicts = []

    # Example: DELETE without UPDATE might be problematic
    if Permission.DELETE.value in permissions and Permission.UPDATE.value not in permissions:
        conflicts.append("DELETE permission without UPDATE permission")

    # ADMIN should include all other permissions
    if Permission.ADMIN.value in permissions:
        missing = [
            p.value for p in Permission if p.value not in permissions and p != Permission.ADMIN
        ]
        if missing:
            conflicts.append(f"ADMIN permission without: {', '.join(missing)}")

    return conflicts


def generate_permission_matrix(
    users: list[str], resources: list[str], auth_manager: Any
) -> dict[str, Any]:
    """Generate a permission matrix for analysis."""
    permissions_map: dict[str, dict[str, list[str]]] = {}
    users_with_access: dict[str, int] = {}
    resources_with_access: dict[str, int] = {}
    summary: dict[str, Any] = {
        "total_grants": 0,
        "users_with_access": users_with_access,
        "resources_with_access": resources_with_access,
    }

    matrix: dict[str, Any] = {
        "users": users,
        "resources": resources,
        "permissions": permissions_map,
        "summary": summary,
    }

    for user_id in users:
        permissions_map[user_id] = {}
        for resource in resources:
            resource_type, resource_id = resource.split(":", 1)
            user_permissions = []

            for permission in Permission:
                context = AuthorizationContext(
                    user_id=user_id,
                    roles=[],
                    permissions=[],
                    resource_type=ResourceType(resource_type),
                    resource_id=resource_id,
                    action=permission,
                )

                if auth_manager.authorize(context):
                    user_permissions.append(permission.value)
                    matrix["summary"]["total_grants"] += 1

            permissions_map[user_id][resource] = user_permissions

            if user_permissions:
                users_with_access[user_id] = users_with_access.get(user_id, 0) + 1

                resources_with_access[resource] = resources_with_access.get(resource, 0) + 1

    return matrix
