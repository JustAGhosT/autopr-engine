"""Utility functions for authorization operations."""

import os
from typing import Any

import structlog

from .audit import AuthorizationAuditLogger
from .models import AuthorizationContext, Permission, ResourceType

logger = structlog.get_logger(__name__)

# Global instances
_auth_manager = None
_access_logger = None


def get_authorization_manager(
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
    global _auth_manager

    if _auth_manager is None:
        # Determine audit log file if not provided but enabled
        if enable_audit and not audit_log_file:
            log_dir = os.environ.get("AUTOPR_LOG_DIR", "logs")
            audit_log_file = os.path.join(log_dir, "authorization_audit.log")

        # Create the appropriate manager based on requested capabilities
        if enable_audit:
            from .managers import AuditedAuthorizationManager

            _auth_manager = AuditedAuthorizationManager(
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
            from .managers import CachedAuthorizationManager

            _auth_manager = CachedAuthorizationManager(cache_ttl_seconds=cache_ttl_seconds)
            logger.info("Created CachedAuthorizationManager", cache_ttl=cache_ttl_seconds)
        else:
            from .managers import EnterpriseAuthorizationManager

            _auth_manager = EnterpriseAuthorizationManager()
            logger.info("Created basic EnterpriseAuthorizationManager")

    return _auth_manager


def get_access_logger() -> AuthorizationAuditLogger:
    """Get global access logger instance."""
    global _access_logger
    if _access_logger is None:
        _access_logger = AuthorizationAuditLogger()
    return _access_logger


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

    max_level = max(permission_levels.get(p, 0) for p in permissions)

    # If user has high-level permissions, they should have lower-level ones too
    if max_level >= 3 and Permission.READ.value not in permissions:
        return False
    if max_level >= 4 and Permission.WRITE.value not in permissions:
        return False

    return True


def get_effective_permissions(
    user_roles: list[str], explicit_permissions: list[str], resource_owner: bool = False
) -> list[str]:
    """Calculate effective permissions for a user."""
    effective_permissions = set(explicit_permissions)

    # Add role-based permissions
    role_permissions = {
        "viewer": [Permission.READ.value],
        "contributor": [Permission.READ.value, Permission.WRITE.value, Permission.CREATE.value],
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
    matrix = {
        "users": users,
        "resources": resources,
        "permissions": {},
        "summary": {"total_grants": 0, "users_with_access": {}, "resources_with_access": {}},
    }

    for user_id in users:
        matrix["permissions"][user_id] = {}
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

            matrix["permissions"][user_id][resource] = user_permissions

            if user_permissions:
                if user_id not in matrix["summary"]["users_with_access"]:
                    matrix["summary"]["users_with_access"][user_id] = 0
                matrix["summary"]["users_with_access"][user_id] += 1

                if resource not in matrix["summary"]["resources_with_access"]:
                    matrix["summary"]["resources_with_access"][resource] = 0
                matrix["summary"]["resources_with_access"][resource] += 1

    return matrix
