"""
Authorization module for AutoPR Engine.

This module provides comprehensive authorization and access control functionality
including role-based access control (RBAC), resource-based permissions, audit logging,
and caching for performance optimization.
"""

from autopr.security.authorization.audit import AuthorizationAuditLogger
from autopr.security.authorization.cache import PermissionCache
from autopr.security.authorization.decorators import (AuthorizationDecorator,
                                                      require_permission)
from autopr.security.authorization.managers import (
    AuditedAuthorizationManager, BaseAuthorizationManager,
    CachedAuthorizationManager, EnterpriseAuthorizationManager)
from autopr.security.authorization.middleware import AuthorizationMiddleware
from autopr.security.authorization.models import (AuthorizationContext,
                                                  Permission,
                                                  ResourcePermission,
                                                  ResourceType)
from autopr.security.authorization.utils import (
    authorize_request, create_project_authorization_context,
    create_repository_authorization_context,
    create_template_authorization_context,
    create_workflow_authorization_context, get_access_logger,
    get_authorization_manager)

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
