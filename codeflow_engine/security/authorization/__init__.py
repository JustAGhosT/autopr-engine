"""
Authorization module for AutoPR Engine.

This module provides comprehensive authorization and access control functionality
including role-based access control (RBAC), resource-based permissions, audit logging,
and caching for performance optimization.
"""

from codeflow_engine.security.authorization.audit import AuthorizationAuditLogger
from codeflow_engine.security.authorization.cache import PermissionCache
from codeflow_engine.security.authorization.decorators import (
    AuthorizationDecorator,
    require_permission,
)
from codeflow_engine.security.authorization.managers import (
    AuditedAuthorizationManager,
    BaseAuthorizationManager,
    CachedAuthorizationManager,
    EnterpriseAuthorizationManager,
)
from codeflow_engine.security.authorization.middleware import AuthorizationMiddleware
from codeflow_engine.security.authorization.models import (
    AuthorizationContext,
    Permission,
    ResourcePermission,
    ResourceType,
)
from codeflow_engine.security.authorization.utils import (
    authorize_request,
    create_project_authorization_context,
    create_repository_authorization_context,
    create_template_authorization_context,
    create_workflow_authorization_context,
    get_access_logger,
    get_authorization_manager,
)


__all__ = [
    "AuditedAuthorizationManager",
    # Audit
    "AuthorizationAuditLogger",
    "AuthorizationContext",
    # Decorators
    "AuthorizationDecorator",
    # Middleware
    "AuthorizationMiddleware",
    # Managers
    "BaseAuthorizationManager",
    "CachedAuthorizationManager",
    "EnterpriseAuthorizationManager",
    # Models
    "Permission",
    # Cache
    "PermissionCache",
    "ResourcePermission",
    "ResourceType",
    "authorize_request",
    # Utils
    "create_project_authorization_context",
    "create_repository_authorization_context",
    "create_template_authorization_context",
    "create_workflow_authorization_context",
    "get_access_logger",
    "get_authorization_manager",
    "require_permission",
]
