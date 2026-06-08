"""
app/core/security.py
--------------------
All security utilities in one place:
  - Password hashing (bcrypt)
  - JWT token creation (access + refresh)
  - JWT token decoding and verification

RULE: This file has NO database access, NO HTTP logic.
Pure functions only. Easy to test independently.

HOW TOKENS WORK IN THIS APP:
  1. User logs in → we call create_access_token() + create_refresh_token()
  2. Frontend stores both tokens
  3. Every API request sends: Authorization: Bearer <access_token>
  4. api/deps.py calls decode_token() to verify it
  5. When access token expires (60 min), frontend sends refresh token
     to /auth/refresh → we issue a new access token
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# bcrypt context — industry standard for password hashing
# "deprecated=auto" means old hash formats are auto-upgraded on next login
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password utilities ─────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """
    Convert a plain text password into a bcrypt hash.
    The hash is different every time (random salt) but always verifiable.

    Example:
        hash_password("mypassword123")
        → "$2b$12$randomsalt...hashedvalue"
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain text password matches a stored bcrypt hash.
    Returns True if match, False otherwise.

    Example:
        verify_password("mypassword123", stored_hash) → True
        verify_password("wrongpassword", stored_hash) → False
    """
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT utilities ──────────────────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        data: dict containing at minimum {"sub": user_id}
              "sub" (subject) is the standard JWT field for user identity
        expires_delta: optional custom expiry, defaults to settings value

    Returns:
        Signed JWT string — send this to the frontend
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.access_token_expire_minutes)
    )
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "type": "access",   # custom claim so we can reject refresh tokens
    })
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )


def create_refresh_token(data: dict) -> str:
    """
    Create a long-lived JWT refresh token (7 days).
    Used ONLY to get a new access token — not for API calls.

    Args:
        data: dict containing {"sub": user_id}
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    to_encode.update({
        "exp": expire,
        "type": "refresh",  # different type — routers check this
    })
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.

    Returns:
        dict payload if token is valid and not expired
        None if token is invalid, expired, or tampered with

    The calling code (api/deps.py) decides what to do with None.
    This function never raises — always returns dict or None.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        # Covers: expired, invalid signature, malformed token
        return None