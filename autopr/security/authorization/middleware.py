"""
Authorization middleware for web framework integration.
"""

from typing import Any

import structlog

from .managers import EnterpriseAuthorizationManager
from .models import AuthorizationContext, Permission, ResourceType

logger = structlog.get_logger(__name__)


class AuthorizationMiddleware:
    """Middleware for web framework integration"""

    def __init__(self, auth_manager: EnterpriseAuthorizationManager):
        self.auth_manager = auth_manager

    def check_authorization(
        self, request: Any, resource_type: str, resource_id: str, action: str
    ) -> bool:
        """Check authorization for web requests"""
        try:
            # Extract user info from request (implementation depends on your auth system)
            user_id = self._extract_user_id(request)
            roles = self._extract_user_roles(request)

            if not user_id:
                logger.warning("Authorization check failed: no user ID found")
                return False

            context = AuthorizationContext(
                user_id=user_id,
                roles=roles,
                permissions=[],
                resource_type=ResourceType(resource_type),
                resource_id=resource_id,
                action=Permission(action),
            )

            return self.auth_manager.authorize(context)

        except Exception as e:
            logger.error("Authorization middleware error", error=str(e))
            return False

    def _extract_user_id(self, request: Any) -> str | None:
        """Extract user ID from request - implement based on your auth system"""
        # Try multiple common patterns for user identification
        if hasattr(request, "user") and hasattr(request.user, "id"):
            return str(request.user.id)

        if hasattr(request, "user_id"):
            return str(request.user_id)

        # Check headers
        if hasattr(request, "headers"):
            user_id = request.headers.get("X-User-ID")
            if user_id:
                return user_id

        # Check session
        if hasattr(request, "session"):
            user_id = request.session.get("user_id")
            if user_id:
                return str(user_id)

        return None

    def _extract_user_roles(self, request: Any) -> list[str]:
        """Extract user roles from request - implement based on your auth system"""
        roles = []

        # Try to get roles from user object
        if hasattr(request, "user") and hasattr(request.user, "roles"):
            if isinstance(request.user.roles, list):
                roles = request.user.roles
            elif hasattr(request.user.roles, "all"):
                roles = [role.name for role in request.user.roles.all()]

        # Check headers
        if hasattr(request, "headers"):
            roles_header = request.headers.get("X-User-Roles", "")
            if roles_header:
                roles.extend(roles_header.split(","))

        # Check session
        if hasattr(request, "session"):
            session_roles = request.session.get("user_roles", [])
            if session_roles:
                roles.extend(session_roles)

        return [role.strip() for role in roles if role.strip()]

    def require_permission(
        self, resource_type: str, action: str, resource_id_param: str = "id"
    ) -> Any:
        """Decorator for route-level authorization"""

        def decorator(func):
            def wrapper(*args, **kwargs):
                # Extract resource_id from kwargs or path parameters
                resource_id = kwargs.get(resource_id_param)
                if not resource_id:
                    raise ValueError(f"Missing {resource_id_param} parameter")

                # Get request object (implementation depends on framework)
                request = kwargs.get("request") or args[0] if args else None
                if not request:
                    raise ValueError("Request object not found")

                if not self.check_authorization(request, resource_type, resource_id, action):
                    raise PermissionError("Access denied")

                return func(*args, **kwargs)

            return wrapper

        return decorator

    def require_any_permission(
        self, permissions: list[dict[str, str]], resource_id_param: str = "id"
    ):
        """Decorator that requires any of the specified permissions"""

        def decorator(func):
            def wrapper(*args, **kwargs):
                resource_id = kwargs.get(resource_id_param)
                if not resource_id:
                    raise ValueError(f"Missing {resource_id_param} parameter")

                request = kwargs.get("request") or args[0] if args else None
                if not request:
                    raise ValueError("Request object not found")

                # Check if user has any of the required permissions
                for perm in permissions:
                    if self.check_authorization(
                        request, perm["resource_type"], resource_id, perm["action"]
                    ):
                        return func(*args, **kwargs)

                raise PermissionError("Access denied - insufficient permissions")

            return wrapper

        return decorator

    def require_all_permissions(
        self, permissions: list[dict[str, str]], resource_id_param: str = "id"
    ):
        """Decorator that requires all of the specified permissions"""

        def decorator(func):
            def wrapper(*args, **kwargs):
                resource_id = kwargs.get(resource_id_param)
                if not resource_id:
                    raise ValueError(f"Missing {resource_id_param} parameter")

                request = kwargs.get("request") or args[0] if args else None
                if not request:
                    raise ValueError("Request object not found")

                # Check if user has all required permissions
                for perm in permissions:
                    if not self.check_authorization(
                        request, perm["resource_type"], resource_id, perm["action"]
                    ):
                        raise PermissionError(
                            f"Access denied - missing {perm['action']} permission on {perm['resource_type']}"
                        )

                return func(*args, **kwargs)

            return wrapper

        return decorator

    def create_context_middleware(self):
        """Create middleware that adds authorization context to requests"""

        def middleware(request, response, next_handler):
            # Add authorization context to request
            request.auth_context = {
                "user_id": self._extract_user_id(request),
                "roles": self._extract_user_roles(request),
                "auth_manager": self.auth_manager,
            }

            return next_handler(request, response)

        return middleware
