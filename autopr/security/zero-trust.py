from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


class SecurityLevel(Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    AUTHORIZED = "authorized"
    PRIVILEGED = "privileged"


@dataclass
class SecurityContext:
    user_id: str | None
    roles: list[str]
    permissions: list[str]
    session_id: str
    ip_address: str
    user_agent: str
    security_level: SecurityLevel


class SecurityValidator(ABC):
    """Abstract base class for security validation"""

    @abstractmethod
    async def validate(self, context: SecurityContext, resource: str, action: str) -> bool:
        """Validate security context for resource access"""


class ZeroTrustSecurityManager:
    """Enterprise zero-trust security manager"""

    def __init__(self):
        self.validators: dict[str, SecurityValidator] = {}
        self.audit_logger = structlog.get_logger("security.audit")

    def register_validator(self, name: str, validator: SecurityValidator) -> None:
        """Register a security validator"""
        self.validators[name] = validator
        logger.info("Security validator registered", validator=name)

    async def validate_access(self, context: SecurityContext, resource: str, action: str) -> bool:
        """Validate access using all registered validators"""
        try:
            # Log access attempt
            self.audit_logger.info(
                "Access validation attempt",
                user_id=context.user_id,
                resource=resource,
                action=action,
                ip_address=context.ip_address,
            )

            # Run all validators
            for validator_name, validator in self.validators.items():
                if not await validator.validate(context, resource, action):
                    self.audit_logger.warning(
                        "Access denied by validator",
                        validator=validator_name,
                        user_id=context.user_id,
                        resource=resource,
                        action=action,
                    )
                    return False

            self.audit_logger.info(
                "Access granted", user_id=context.user_id, resource=resource, action=action
            )
            return True

        except Exception as e:
            self.audit_logger.error(
                "Security validation error",
                error=str(e),
                user_id=context.user_id,
                resource=resource,
                action=action,
            )
            return False  # Fail secure
