"""Base authorization manager definition."""

from abc import ABC, abstractmethod

from .models import AuthorizationContext, Permission, ResourceType


class BaseAuthorizationManager(ABC):
    """Base class for authorization managers"""

    @abstractmethod
    def authorize(self, context: AuthorizationContext) -> bool:
        """Check if the given context is authorized"""

    @abstractmethod
    def grant_resource_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        permissions: set[Permission],
        granted_by: str,
    ) -> bool:
        """Grant permissions to a user for a specific resource"""

    @abstractmethod
    def revoke_resource_permission(
        self, user_id: str, resource_type: ResourceType, resource_id: str
    ) -> bool:
        """Revoke permissions from a user for a specific resource"""
