"""Enterprise-grade authorization manager implementation."""

from datetime import datetime

import structlog

from .base_manager import BaseAuthorizationManager
from .models import AuthorizationContext, Permission, ResourcePermission, ResourceType

logger = structlog.get_logger(__name__)


class EnterpriseAuthorizationManager(BaseAuthorizationManager):
    """Enterprise-grade authorization manager with comprehensive features"""

    def __init__(self):
        # Role-based permissions: role -> resource_type -> permissions
        self.role_permissions: dict[str, dict[ResourceType, set[Permission]]] = {}

        # User-specific resource permissions
        self.user_resource_permissions: dict[str, list[ResourcePermission]] = {}

        # Resource ownership mapping
        self.resource_owners: dict[str, str] = {}

        # Initialize default roles
        self._initialize_default_roles()

    def _initialize_default_roles(self):
        """Initialize default role permissions"""
        # Admin role - full access to everything
        self.role_permissions["admin"] = {
            ResourceType.PROJECT: {
                Permission.READ,
                Permission.WRITE,
                Permission.DELETE,
                Permission.CREATE,
                Permission.UPDATE,
                Permission.EXECUTE,
                Permission.ADMIN,
            },
            ResourceType.REPOSITORY: {
                Permission.READ,
                Permission.WRITE,
                Permission.DELETE,
                Permission.CREATE,
                Permission.UPDATE,
                Permission.EXECUTE,
                Permission.ADMIN,
            },
            ResourceType.WORKFLOW: {
                Permission.READ,
                Permission.WRITE,
                Permission.DELETE,
                Permission.CREATE,
                Permission.UPDATE,
                Permission.EXECUTE,
                Permission.ADMIN,
            },
            ResourceType.TEMPLATE: {
                Permission.READ,
                Permission.WRITE,
                Permission.DELETE,
                Permission.CREATE,
                Permission.UPDATE,
                Permission.EXECUTE,
                Permission.ADMIN,
            },
            ResourceType.INTEGRATION: {
                Permission.READ,
                Permission.WRITE,
                Permission.DELETE,
                Permission.CREATE,
                Permission.UPDATE,
                Permission.EXECUTE,
                Permission.ADMIN,
            },
        }

        # Developer role - read/write access to most resources
        self.role_permissions["developer"] = {
            ResourceType.PROJECT: {
                Permission.READ,
                Permission.WRITE,
                Permission.CREATE,
                Permission.UPDATE,
            },
            ResourceType.REPOSITORY: {
                Permission.READ,
                Permission.WRITE,
                Permission.CREATE,
                Permission.UPDATE,
            },
            ResourceType.WORKFLOW: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
            ResourceType.TEMPLATE: {
                Permission.READ,
                Permission.WRITE,
                Permission.CREATE,
                Permission.UPDATE,
            },
            ResourceType.INTEGRATION: {Permission.READ},
        }

        # Viewer role - read-only access
        self.role_permissions["viewer"] = {
            ResourceType.PROJECT: {Permission.READ},
            ResourceType.REPOSITORY: {Permission.READ},
            ResourceType.WORKFLOW: {Permission.READ},
            ResourceType.TEMPLATE: {Permission.READ},
            ResourceType.INTEGRATION: {Permission.READ},
        }

        # Maintainer role - elevated permissions but not full admin
        self.role_permissions["maintainer"] = {
            ResourceType.PROJECT: {
                Permission.READ,
                Permission.WRITE,
                Permission.CREATE,
                Permission.UPDATE,
                Permission.DELETE,
            },
            ResourceType.REPOSITORY: {
                Permission.READ,
                Permission.WRITE,
                Permission.CREATE,
                Permission.UPDATE,
                Permission.DELETE,
            },
            ResourceType.WORKFLOW: {
                Permission.READ,
                Permission.WRITE,
                Permission.CREATE,
                Permission.UPDATE,
                Permission.EXECUTE,
            },
            ResourceType.TEMPLATE: {
                Permission.READ,
                Permission.WRITE,
                Permission.CREATE,
                Permission.UPDATE,
                Permission.DELETE,
            },
            ResourceType.INTEGRATION: {Permission.READ, Permission.WRITE},
        }

    def authorize(self, context: AuthorizationContext) -> bool:
        try:
            if self._is_resource_owner(context.user_id, context.resource_type, context.resource_id):
                return True

            if self._check_role_permissions(context):
                return True

            if self._check_user_resource_permissions(context):
                return True

            if self._check_explicit_permissions(context):
                return True

            return False
        except Exception as e:
            logger.error("Authorization check failed", error=str(e))
            return False

    def grant_resource_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        permissions: set[Permission],
        granted_by: str,
    ) -> bool:
        """Grant specific permissions to a user for a resource"""
        try:
            if user_id not in self.user_resource_permissions:
                self.user_resource_permissions[user_id] = []

            # Remove any existing permissions for this resource
            self.user_resource_permissions[user_id] = [
                perm
                for perm in self.user_resource_permissions[user_id]
                if not (perm.resource_type == resource_type and perm.resource_id == resource_id)
            ]

            # Create new permission
            resource_permission = ResourcePermission(
                resource_type=resource_type,
                resource_id=resource_id,
                permissions=permissions,
                granted_by=granted_by,
                granted_at=datetime.utcnow().isoformat(),
            )

            # Add new permission
            self.user_resource_permissions[user_id].append(resource_permission)
            logger.info(
                "Granted permissions to user",
                user_id=user_id,
                resource_type=resource_type.value,
                resource_id=resource_id,
                permissions=[p.value for p in permissions],
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to grant permissions",
                error=str(e),
                user_id=user_id,
                resource_type=resource_type.value,
                resource_id=resource_id,
            )
            return False

    def revoke_resource_permission(
        self, user_id: str, resource_type: ResourceType, resource_id: str
    ) -> bool:
        """Revoke all permissions from a user for a specific resource"""
        try:
            if user_id not in self.user_resource_permissions:
                # User has no permissions to revoke
                return True

            # Filter out permissions for the specified resource
            original_count = len(self.user_resource_permissions[user_id])
            self.user_resource_permissions[user_id] = [
                perm
                for perm in self.user_resource_permissions[user_id]
                if not (perm.resource_type == resource_type and perm.resource_id == resource_id)
            ]

            # Check if any permissions were removed
            revoked = original_count > len(self.user_resource_permissions[user_id])

            if revoked:
                logger.info(
                    "Revoked permissions from user",
                    user_id=user_id,
                    resource_type=resource_type.value,
                    resource_id=resource_id,
                )

            return True
        except Exception as e:
            logger.error(
                "Failed to revoke permissions",
                error=str(e),
                user_id=user_id,
                resource_type=resource_type.value,
                resource_id=resource_id,
            )
            return False

    def _is_resource_owner(
        self, user_id: str, resource_type: ResourceType, resource_id: str
    ) -> bool:
        """Check if the user is the owner of the resource"""
        resource_key = f"{resource_type.value}:{resource_id}"
        return self.resource_owners.get(resource_key) == user_id

    def _check_role_permissions(self, context: AuthorizationContext) -> bool:
        """Check if the user has role-based permissions for the requested action"""
        # Get the user's role from the context
        user_role = context.user_role

        if not user_role or user_role not in self.role_permissions:
            return False

        # Check if the role has the necessary permissions for this resource type
        role_perms = self.role_permissions.get(user_role, {})
        if context.resource_type not in role_perms:
            return False

        # Check if the required permission is in the role's permissions for this resource type
        return context.action in role_perms[context.resource_type]

    def _check_user_resource_permissions(self, context: AuthorizationContext) -> bool:
        """Check user-specific resource permissions"""
        if context.user_id not in self.user_resource_permissions:
            return False

        # Find matching resource permission
        for perm in self.user_resource_permissions[context.user_id]:
            if (
                perm.resource_type == context.resource_type
                and perm.resource_id == context.resource_id
                and context.action in perm.permissions
            ):
                return True

        return False

    def _check_explicit_permissions(self, context: AuthorizationContext) -> bool:
        """Check for explicit permissions granted for specific actions"""
        # Check the explicit_permissions attribute in the context
        if context.explicit_permissions and context.action in context.explicit_permissions:
            return True

        return False
