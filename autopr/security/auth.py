from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
import jwt
from passlib.context import CryptContext
import structlog

logger = structlog.get_logger(__name__)


class EnterpriseAuthManager:
    """Enterprise-grade authentication and authorization manager"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.token_blacklist: set[str] = set()

    def create_access_token(
        self, data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """Create JWT access token with enterprise security"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)

        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access_token"})

        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        logger.info("Access token created", user_id=data.get("sub"), expires_at=expire.isoformat())

        return token

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify JWT token with comprehensive validation"""
        try:
            # Check if token is blacklisted
            if token in self.token_blacklist:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked"
                )

            # Decode and validate token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Validate token type
            if payload.get("type") != "access_token":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
                )

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired", token_prefix=token[:10])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        except jwt.JWTError as e:
            logger.error("JWT validation error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
            )

    def revoke_token(self, token: str) -> None:
        """Add token to blacklist"""
        self.token_blacklist.add(token)
        logger.info("Token revoked", token_prefix=token[:10])
