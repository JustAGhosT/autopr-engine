# autopr/security/authorization/decorators.py

from functools import wraps
from typing import Any

from .models import AuthorizationContext, Permission, ResourceType
from .utils import get_authorization_manager


class AuthorizationDecorator:
    """Class-based decorator for authorization checks"""

    def __init__(
        self,
        resource_type: ResourceType,
        action: Permission,
        resource_id_param: str = "resource_id",
    ):
        """
        Initialize the authorization decorator

        Args:
            resource_type: Type of resource to check permission for
            action: Permission action to check
            resource_id_param: Name of the parameter that contains the resource ID
        """
        self.resource_type = resource_type
        self.action = action
        self.resource_id_param = resource_id_param

    def __call__(self, func: Any) -> Any:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user info - try different sources
            user_id = kwargs.get("user_id")
            if user_id is None and args and hasattr(args[0], "current_user_id"):
                user_id = args[0].current_user_id

            # Extract user roles (plural)
            user_roles = []
            if "user_roles" in kwargs:
                user_roles = kwargs["user_roles"]
            elif args and hasattr(args[0], "current_user_roles"):
                user_roles = args[0].current_user_roles

            # Get resource ID from parameters
            resource_id = kwargs.get(self.resource_id_param)

            if not user_id or not resource_id:
                raise ValueError(
                    f"Missing required authorization parameters: user_id={user_id}, {self.resource_id_param}={resource_id}"
                )

            # Create authorization context
            context = AuthorizationContext(
                user_id=user_id,
                resource_type=self.resource_type,
                resource_id=resource_id,
                action=self.action,
                roles=user_roles,  # Pass the roles list directly
            )

            # Get auth manager from instance or create a new one
            auth_manager = None
            if args and hasattr(args[0], "auth_manager"):
                auth_manager = args[0].auth_manager
            else:
                auth_manager = get_authorization_manager()

            if not auth_manager.authorize(context):
                raise PermissionError(
                    f"Access denied for user {user_id} performing {self.action.value} "
                    f"on {self.resource_type.value}:{resource_id}"
                )

            return func(*args, **kwargs)

        return wrapper


def require_permission(
    resource_type: ResourceType, action: Permission, resource_id_param: str = "resource_id"
) -> Any:
    """
    Function decorator to require permission for a specific resource action

    Args:
        resource_type: Type of resource to check permission for
        action: Permission action to check
        resource_id_param: Name of the parameter that contains the resource ID
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user info
            user_id = kwargs.get("user_id")
            if user_id is None and len(args) > 0 and hasattr(args[0], "current_user_id"):
                user_id = args[0].current_user_id

            # Get user roles (list)
            user_roles = []  # Initialize as empty list
            if "user_roles" in kwargs:
                user_roles = kwargs["user_roles"]
            elif len(args) > 0 and hasattr(args[0], "current_user_roles"):
                user_roles = args[0].current_user_roles

            # Get resource ID
            resource_id = kwargs.get(resource_id_param)

            if not user_id or not resource_id:
                raise ValueError(
                    f"Missing required authorization parameters: user_id={user_id}, "
                    f"{resource_id_param}={resource_id}"
                )

            # Create authorization context with proper parameters
            context = AuthorizationContext(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                roles=user_roles,  # Pass roles directly
            )

            # Get authorization manager
            auth_manager = kwargs.get("auth_manager")
            if auth_manager is None and len(args) > 0 and hasattr(args[0], "auth_manager"):
                auth_manager = args[0].auth_manager
            if auth_manager is None:
                auth_manager = get_authorization_manager()

            # Check authorization
            if not auth_manager.authorize(context):
                raise PermissionError(
                    f"Access denied for user {user_id} performing {action.value} "
                    f"on {resource_type.value}:{resource_id}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator
