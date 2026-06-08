"""
app/services/auth_service.py
-----------------------------
Business logic for user registration, login, and token management.
Calls user_repo for all DB operations, face_service for face encoding.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories import analytics_repo, user_repo
from app.schemas.auth import FaceLoginResponse, TokenResponse, UserOut
from app.services import face_service

logger = get_logger(__name__)


async def register_user(
    db: AsyncSession,
    name: str,
    email: str,
    password: str,
    face_image_bytes: Optional[bytes] = None,
) -> TokenResponse:
    """
    Register a new student account.

    Steps:
        1. Check email not already taken
        2. Hash the password
        3. Create user row
        4. If face image provided → encode and store it
        5. Log the registration activity
        6. Return JWT tokens + user info

    Args:
        face_image_bytes: optional — if provided, face login will be enabled
                          for this user. Send as multipart file upload.

    Raises:
        HTTPException 400: email already registered
        HTTPException 400: no face detected in provided image
    """
    # Step 1 — check email uniqueness
    if await user_repo.email_exists(db, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    # Step 2 — hash password (never store plain text)
    hashed = hash_password(password)

    # Step 3 — create user in DB
    user = await user_repo.create_user(
        db=db,
        name=name,
        email=email,
        password_hash=hashed,
    )

    # Step 4 — encode and save face if image provided
    has_face = False
    if face_image_bytes:
        encoding = face_service.encode_face(face_image_bytes)
        if encoding is not None:
            await user_repo.save_face_encoding(db, user.id, encoding)
            has_face = True
            logger.info("Face encoding saved for new user: %s", user.id)
        else:
            # Don't block registration if face detection fails
            # Just warn — user can add face later
            logger.warning(
                "No face detected in registration photo for user: %s", user.id
            )

    # Step 5 — log activity
    await analytics_repo.log_activity(
        db=db,
        user_id=user.id,
        action_type="register",
        metadata={"has_face": has_face},
    )

    # Step 6 — generate tokens
    token_data = {"sub": user.id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info("User registered successfully: %s", email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            has_face_encoding=has_face,
        ),
    )


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> TokenResponse:
    """
    Authenticate a user with email + password.

    Steps:
        1. Look up user by email
        2. Verify password against bcrypt hash
        3. Check account is active
        4. Log login activity
        5. Return JWT tokens

    Raises:
        HTTPException 401: invalid email or password
        HTTPException 403: account is deactivated
    """
    # Step 1 — find user (use vague error message to prevent email enumeration)
    user = await user_repo.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Step 2 — verify password
    if not verify_password(password, user.password_hash):
        logger.warning("Failed login attempt for email: %s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Step 3 — check active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    # Step 4 — log activity
    await analytics_repo.log_activity(
        db=db,
        user_id=user.id,
        action_type="login",
        metadata={"method": "password"},
    )

    # Step 5 — generate tokens
    token_data = {"sub": user.id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Check if user has face encoding registered
    face_enc = await user_repo.get_face_encoding_by_user(db, user.id)
    has_face = face_enc is not None

    logger.info("User logged in: %s", email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            has_face_encoding=has_face,
        ),
    )


async def face_login(
    db: AsyncSession,
    image_bytes: bytes,
) -> FaceLoginResponse:
    """
    Authenticate a user by matching their webcam image against
    all stored face encodings.

    Steps:
        1. Fetch all stored face encodings from DB
        2. Compare webcam image against all encodings
        3. Find best match above confidence threshold
        4. Load the matched user
        5. Log activity + return tokens

    Raises:
        HTTPException 503: face recognition not available
        HTTPException 401: no face match found
        HTTPException 401: match confidence too low
    """
    # Step 1 — get all encodings
    all_encodings = await user_repo.get_all_face_encodings(db)

    if not all_encodings:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No face profiles registered. Please use password login.",
        )

    # Step 2+3 — compare and find match
    matched_user_id, confidence = face_service.verify_face(image_bytes, all_encodings)

    if not matched_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Face not recognised. Please try again or use password login.",
        )

    # Minimum confidence threshold — reject weak matches
    if confidence < 0.35:
        logger.warning(
            "Low confidence face match: user=%s confidence=%.3f",
            matched_user_id, confidence,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify identity with sufficient confidence. Please use password login.",
        )

    # Step 4 — load matched user
    user = await user_repo.get_user_by_id(db, matched_user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found or deactivated.",
        )

    # Step 5 — log activity + return tokens
    await analytics_repo.log_activity(
        db=db,
        user_id=user.id,
        action_type="face_login",
        metadata={"confidence": confidence},
    )

    token_data = {"sub": user.id}
    logger.info(
        "Face login successful: user=%s confidence=%.1f%%",
        user.email, confidence * 100,
    )

    return FaceLoginResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=UserOut(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            has_face_encoding=True,
        ),
        confidence=confidence,
    )


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
) -> str:
    """
    Issue a new access token given a valid refresh token.

    Raises:
        HTTPException 401: invalid or expired refresh token
        HTTPException 401: user not found or deactivated
    """
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user_id = payload.get("sub")
    user = await user_repo.get_user_by_id(db, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    new_access_token = create_access_token({"sub": user.id})
    logger.info("Access token refreshed for user: %s", user.id)
    return new_access_token