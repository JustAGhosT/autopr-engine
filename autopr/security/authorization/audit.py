"""Audit logging for authorization events."""

from datetime import datetime
from typing import Any

import structlog

from .models import AuthorizationContext

logger = structlog.get_logger(__name__)


class AuthorizationAuditLogger:
    """Audit logger for authorization events."""

    def __init__(self, log_file: str | None = None):
        self.audit_logger = structlog.get_logger("authorization_audit")
        self.log_file = log_file

        if log_file:
            import logging

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            self.audit_logger.addHandler(file_handler)

    def log_authorization_check(
        self, context: AuthorizationContext, result: bool, duration_ms: float | None = None
    ):
        """Log authorization check."""
        self.audit_logger.info(
            "authorization_check",
            user_id=context.user_id,
            roles=context.roles,
            resource_type=context.resource_type.value,
            resource_id=context.resource_id,
            action=context.action.value,
            result=result,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow().isoformat(),
        )

    def log_permission_grant(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permissions: list[str],
        granted_by: str,
    ):
        """Log permission grant."""
        self.audit_logger.info(
            "permission_granted",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permissions=permissions,
            granted_by=granted_by,
            timestamp=datetime.utcnow().isoformat(),
        )

    def log_permission_revoke(
        self, user_id: str, resource_type: str, resource_id: str, revoked_by: str
    ):
        """Log permission revocation."""
        self.audit_logger.info(
            "permission_revoked",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            revoked_by=revoked_by,
            timestamp=datetime.utcnow().isoformat(),
        )

    def log_access_denied(
        self, context: AuthorizationContext, reason: str = "insufficient_permissions"
    ):
        """Log access denied events."""
        self.audit_logger.warning(
            "access_denied",
            user_id=context.user_id,
            roles=context.roles,
            resource_type=context.resource_type.value,
            resource_id=context.resource_id,
            action=context.action.value,
            reason=reason,
            timestamp=datetime.utcnow().isoformat(),
        )

    def log_security_event(self, event_type: str, user_id: str, details: dict[str, Any]):
        """Log security events."""
        self.audit_logger.warning(
            "security_event",
            event_type=event_type,
            user_id=user_id,
            details=details,
            timestamp=datetime.utcnow().isoformat(),
        )
