"""
app/api/deps.py
---------------
FastAPI dependencies — reusable functions injected into endpoints via Depends().

THE SINGLE MOST IMPORTANT FILE IN THE API LAYER:
    Every protected endpoint does:
        current_user: User = Depends(get_current_user)

    This one line:
        1. Extracts the Bearer token from the Authorization header
        2. Decodes and verifies the JWT signature
        3. Loads the user from DB
        4. Injects the User object into your endpoint function
        5. Returns 401 automatically if anything fails

    You never write auth logic in a router — it all happens here.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories import user_repo

# HTTPBearer extracts the token from: Authorization: Bearer <token>
# auto_error=False means we handle the 401 ourselves with a cleaner message
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme)
    ],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Core authentication dependency.

    Usage in any router:
        @router.get("/protected")
        async def my_endpoint(
            current_user: User = Depends(get_current_user)
        ):
            return {"user_id": current_user.id}

    Flow:
        1. Extract Bearer token from Authorization header
        2. Decode JWT → get user_id from "sub" claim
        3. Verify token type is "access" (not refresh)
        4. Load user from DB
        5. Verify user is active
        6. Return User ORM object

    Raises:
        HTTPException 401: missing token, invalid token, user not found
        HTTPException 403: account deactivated
    """
    # Step 1 — check header present
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Step 2+3 — decode and validate JWT
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reject refresh tokens used as access tokens
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload invalid.",
        )

    # Step 4 — load user from DB
    user = await user_repo.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
        )

    # Step 5 — check active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    return user


# ── Type alias for cleaner router signatures ───────────────────────────────
# Instead of: current_user: User = Depends(get_current_user)
# You can write: current_user: CurrentUser
# Both work identically — the alias just reduces repetition

CurrentUser = Annotated[User, Depends(get_current_user)]
DB = Annotated[AsyncSession, Depends(get_db)]