"""JWT creation/validation and password hashing utilities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        plain_password: The raw password string supplied by the user.

    Returns:
        str: bcrypt hash suitable for storing in the database.
    """
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its stored bcrypt hash.

    Args:
        plain_password: Password provided at login.
        hashed_password: Stored bcrypt hash from the database.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(
    *,
    subject: int,
    username: str,
    is_admin: bool,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        subject: User primary key to embed as the ``sub`` claim.
        username: Username to embed in the payload.
        is_admin: Admin flag to embed in the payload.
        expires_delta: Custom TTL; defaults to ``access_token_expire_hours`` from settings.

    Returns:
        str: Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=settings.access_token_expire_hours)
    )
    payload = {
        "sub": str(subject),
        "username": username,
        "is_admin": is_admin,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Args:
        token: JWT string to decode.

    Returns:
        dict: Decoded payload dictionary.

    Raises:
        jose.JWTError: If the token is malformed, expired, or has an invalid signature.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
