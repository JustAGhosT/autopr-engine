"""
Authorization managers for different authorization strategies.
"""

# Re-export authorization manager classes for backward compatibility
from autopr.security.authorization.audit_logger import AuthorizationAuditLogger
from autopr.security.authorization.audited_manager import AuditedAuthorizationManager
from autopr.security.authorization.base_manager import BaseAuthorizationManager
from autopr.security.authorization.cached_manager import CachedAuthorizationManager
from autopr.security.authorization.enterprise_manager import (
    EnterpriseAuthorizationManager,
)


__all__ = [
    "AuditedAuthorizationManager",
    "AuthorizationAuditLogger",
    "BaseAuthorizationManager",
    "CachedAuthorizationManager",
    "EnterpriseAuthorizationManager",
]
