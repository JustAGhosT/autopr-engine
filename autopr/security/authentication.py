from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import secrets
from typing import Any

import bcrypt
import jwt
import structlog

from .encryption import EnterpriseEncryptionManager

logger = structlog.get_logger(__name__)


class AuthenticationMethod(Enum):
    PASSWORD = "password"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    MULTI_FACTOR = "multi_factor"


class UserRole(Enum):
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    SERVICE_ACCOUNT = "service_account"


@dataclass
class AuthenticationResult:
    success: bool
    user_id: str | None = None
    roles: list[str] = None
    permissions: list[str] = None
    token: str | None = None
    expires_at: datetime | None = None
    error_message: str | None = None
    requires_mfa: bool = False


@dataclass
class UserCredentials:
    username: str
    password_hash: str
    salt: str
    roles: list[str]
    permissions: list[str]
    is_active: bool = True
    created_at: datetime = None
    last_login: datetime | None = None
    failed_login_attempts: int = 0
    locked_until: datetime | None = None


class EnterpriseAuthenticationManager:
    "Enterprise-grade authentication and authorization"

    def __init__(self, secret_key: str, encryption_manager: EnterpriseEncryptionManager):
        self.secret_key = secret_key
        self.encryption_manager = encryption_manager
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.token_expiry = timedelta(hours=24)
        self.refresh_token_expiry = timedelta(days=30)

        # In-memory storage for demo - replace with database in production
        self.users: dict[str, UserCredentials] = {}
        self.api_keys: dict[str, dict[str, Any]] = {}
        self.active_sessions: dict[str, dict[str, Any]] = {}

        logger.info("Authentication manager initialized")

    def create_user(
        self, username: str, password: str, roles: list[str], permissions: list[str]
    ) -> bool:
        """Create a new user with secure password hashing"""
        try:
            if username in self.users:
                logger.warning("User creation failed - username exists", username=username)
                return False

            # Generate salt and hash password
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)

            # Create user credentials
            user_creds = UserCredentials(
                username=username,
                password_hash=password_hash.decode("utf-8"),
                salt=salt.decode("utf-8"),
                roles=roles,
                permissions=permissions,
                created_at=datetime.utcnow(),
            )

            self.users[username] = user_creds

            logger.info("User created successfully", username=username, roles=roles)
            return True

        except Exception as e:
            logger.error("User creation failed", username=username, error=str(e))
            return False

    def authenticate_user(self, username: str, password: str) -> AuthenticationResult:
        """Authenticate user with password"""
        try:
            user = self.users.get(username)
            if not user:
                logger.warning("Authentication failed - user not found", username=username)
                return AuthenticationResult(success=False, error_message="Invalid credentials")

            # Check if account is locked
            if user.locked_until and datetime.utcnow() < user.locked_until:
                logger.warning(
                    "Authentication failed - account locked",
                    username=username,
                    locked_until=user.locked_until,
                )
                return AuthenticationResult(
                    success=False, error_message="Account temporarily locked"
                )

            # Check if account is active
            if not user.is_active:
                logger.warning("Authentication failed - account inactive", username=username)
                return AuthenticationResult(success=False, error_message="Account inactive")

            # Verify password
            if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
                # Increment failed attempts
                user.failed_login_attempts += 1

                # Lock account if too many failed attempts
                if user.failed_login_attempts >= self.max_failed_attempts:
                    user.locked_until = datetime.utcnow() + self.lockout_duration
                    logger.warning(
                        "Account locked due to failed attempts",
                        username=username,
                        attempts=user.failed_login_attempts,
                    )

                logger.warning(
                    "Authentication failed - invalid password",
                    username=username,
                    failed_attempts=user.failed_login_attempts,
                )
                return AuthenticationResult(success=False, error_message="Invalid credentials")

            # Reset failed login attempts on successful login
            user.failed_login_attempts = 0
            user.last_login = datetime.utcnow()
            user.locked_until = None

            # Generate JWT token
            payload = {
                "sub": user.username,
                "roles": user.roles,
                "permissions": user.permissions,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + self.token_expiry,
            }
            token = jwt.encode(payload, self.secret_key, algorithm="HS256")

            # Store active session
            session_id = secrets.token_urlsafe(32)
            self.active_sessions[session_id] = {
                "username": user.username,
                "token": token,
                "created_at": datetime.utcnow(),
                "expires_at": payload["exp"],
            }

            logger.info("User authenticated successfully", username=username)
            return AuthenticationResult(
                success=True,
                user_id=user.username,
                roles=user.roles,
                permissions=user.permissions,
                token=token,
                expires_at=payload["exp"],
            )

        except Exception as e:
            logger.error("Authentication failed", username=username, error=str(e))
            return AuthenticationResult(success=False, error_message="An unexpected error occurred")

    def validate_token(self, token: str) -> AuthenticationResult:
        "Validate JWT token"
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            username = payload.get("sub")

            if not username:
                return AuthenticationResult(success=False, error_message="Invalid token format")

            user = self.users.get(username)
            if not user or not user.is_active:
                return AuthenticationResult(
                    success=False, error_message="User not found or inactive"
                )

            return AuthenticationResult(
                success=True,
                user_id=username,
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                token=token,
                expires_at=datetime.fromtimestamp(payload["exp"]),
            )

        except jwt.ExpiredSignatureError:
            logger.warning("Token validation failed - expired token")
            return AuthenticationResult(success=False, error_message="Token expired")
        except jwt.InvalidTokenError:
            logger.warning("Token validation failed - invalid token")
            return AuthenticationResult(success=False, error_message="Invalid token")
        except Exception as e:
            logger.error("Token validation error", error=str(e))
            return AuthenticationResult(success=False, error_message="Token validation failed")

    def create_api_key(
        self, username: str, name: str, permissions: list[str], expires_in_days: int = 365
    ) -> str | None:
        "Create API key for user"
        try:
            user = self.users.get(username)
            if not user:
                logger.warning("API key creation failed - user not found", username=username)
                return None

            api_key = f"ak_{secrets.token_urlsafe(32)}"

            self.api_keys[api_key] = {
                "username": username,
                "name": name,
                "permissions": permissions,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=expires_in_days),
                "is_active": True,
                "last_used": None,
            }

            logger.info(
                "API key created", username=username, key_name=name, permissions=permissions
            )
            return api_key

        except Exception as e:
            logger.error("API key creation failed", username=username, error=str(e))
            return None

    def validate_api_key(self, api_key: str) -> AuthenticationResult:
        "Validate API key"
        try:
            key_data = self.api_keys.get(api_key)
            if not key_data:
                return AuthenticationResult(success=False, error_message="Invalid API key")

            # Check if key is active
            if not key_data["is_active"]:
                return AuthenticationResult(success=False, error_message="API key inactive")

            # Check if key is expired
            if datetime.utcnow() > key_data["expires_at"]:
                return AuthenticationResult(success=False, error_message="API key expired")

            # Update last used timestamp
            key_data["last_used"] = datetime.utcnow()

            username = key_data["username"]
            user = self.users.get(username)
            if not user or not user.is_active:
                return AuthenticationResult(
                    success=False, error_message="Associated user not found or inactive"
                )

            return AuthenticationResult(
                success=True,
                user_id=username,
                roles=user.roles,
                permissions=key_data["permissions"],
                token=api_key,
                expires_at=key_data["expires_at"],
            )

        except Exception as e:
            logger.error("API key validation failed", error=str(e))
            return AuthenticationResult(success=False, error_message="API key validation failed")

    def revoke_api_key(self, api_key: str) -> bool:
        "Revoke API key"
        try:
            if api_key in self.api_keys:
                self.api_keys[api_key]["is_active"] = False
                logger.info("API key revoked", api_key=api_key[:10] + "...")
                return True
            return False
        except Exception as e:
            logger.error("API key revocation failed", error=str(e))
            return False

    def check_permission(self, user_permissions: list[str], required_permission: str) -> bool:
        "Check if user has required permission"
        return required_permission in user_permissions or "admin" in user_permissions

    def check_role(self, user_roles: list[str], required_role: str) -> bool:
        "Check if user has required role"
        role_hierarchy = {"guest": 0, "user": 1, "admin": 2, "super_admin": 3, "service_account": 1}

        user_level = max([role_hierarchy.get(role, 0) for role in user_roles])
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level

    def logout_user(self, token: str) -> bool:
        "Logout user by invalidating session"
        try:
            # Remove from active sessions
            sessions_to_remove = []
            for session_id, session_data in self.active_sessions.items():
                if session_data["token"] == token:
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]

            logger.info("User logged out successfully")
            return True

        except Exception as e:
            logger.error("Logout failed", error=str(e))
            return False

    def cleanup_expired_sessions(self) -> int:
        "Clean up expired sessions"
        try:
            current_time = datetime.utcnow()
            expired_sessions = []

            for session_id, session_data in self.active_sessions.items():
                if current_time > session_data["expires_at"]:
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self.active_sessions[session_id]

            logger.info("Cleaned up expired sessions", count=len(expired_sessions))
            return len(expired_sessions)

        except Exception as e:
            logger.error("Session cleanup failed", error=str(e))
            return 0

    def get_user_sessions(self, username: str) -> list[dict[str, Any]]:
        "Get active sessions for user"
        sessions = []
        for session_id, session_data in self.active_sessions.items():
            if session_data["username"] == username:
                sessions.append(
                    {
                        "session_id": session_id,
                        "created_at": session_data["created_at"],
                        "expires_at": session_data["expires_at"],
                    }
                )
        return sessions

    def revoke_all_user_sessions(self, username: str) -> int:
        "Revoke all sessions for a user"
        try:
            sessions_to_remove = []
            for session_id, session_data in self.active_sessions.items():
                if session_data["username"] == username:
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]

            logger.info(
                "Revoked all user sessions", username=username, count=len(sessions_to_remove)
            )
            return len(sessions_to_remove)

        except Exception as e:
            logger.error("Session revocation failed", username=username, error=str(e))
            return 0
