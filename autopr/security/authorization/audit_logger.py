"""Authorization audit logging functionality."""

from datetime import datetime
import json
import os
from typing import Any

import structlog

from .models import AuthorizationContext

logger = structlog.get_logger(__name__)


class AuthorizationAuditLogger:
    """Logger for authorization-related events with optional file logging"""

    def __init__(self, audit_log_file: str | None = None):
        self.logger = structlog.get_logger("auth_audit")
        self.audit_log_file = audit_log_file

    def log_authorization_check(
        self, context: AuthorizationContext, result: bool, duration_ms: float
    ):
        """Log an authorization check and its result"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "authorization_check",
            "user_id": context.user_id,
            "resource_type": context.resource_type.value,
            "resource_id": context.resource_id,
            "action": context.action.value,
            "result": result,
            "duration_ms": duration_ms,
        }

        if context.ip_address:
            log_data["ip_address"] = context.ip_address

        if context.user_agent:
            log_data["user_agent"] = context.user_agent

        self.logger.info("Authorization check", **log_data)
        self._write_to_file(log_data)

    def log_access_denied(self, context: AuthorizationContext):
        """Log an access denied event"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "access_denied",
            "user_id": context.user_id,
            "resource_type": context.resource_type.value,
            "resource_id": context.resource_id,
            "action": context.action.value,
        }

        if context.ip_address:
            log_data["ip_address"] = context.ip_address

        if context.user_agent:
            log_data["user_agent"] = context.user_agent

        self.logger.warning("Access denied", **log_data)
        self._write_to_file(log_data)

    def log_permission_grant(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permissions: list[str],
        granted_by: str,
    ):
        """Log permission grant event"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "permission_grant",
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "permissions": permissions,
            "granted_by": granted_by,
        }

        self.logger.info("Permission granted", **log_data)
        self._write_to_file(log_data)

    def log_permission_revoke(
        self, user_id: str, resource_type: str, resource_id: str, revoked_by: str
    ):
        """Log permission revocation event"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "permission_revoke",
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "revoked_by": revoked_by,
        }

        self.logger.info("Permission revoked", **log_data)
        self._write_to_file(log_data)

    def _write_to_file(self, log_data: dict[str, Any]):
        """Write log data to file if configured"""
        if not self.audit_log_file:
            return

        try:
            # Create directory if it doesn't exist
            log_dir = os.path.dirname(self.audit_log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # Append to log file
            with open(self.audit_log_file, "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except Exception as e:
            self.logger.error("Failed to write to audit log file", error=str(e))
