"""
app/api/v1/auth.py
------------------
Auth router — registration, login, face login, token refresh.
No business logic here — all calls go to auth_service.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DB, CurrentUser
from app.core.security import create_access_token
from app.schemas.auth import (
    AccessTokenResponse,
    FaceLoginResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserOut,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    db: DB,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    face_image: UploadFile | None = File(None),
):
    """
    Register a new student account.

    Accepts multipart/form-data so the face image can be
    uploaded alongside the text fields in one request.

    face_image is optional — registration works without it,
    but face login won't be available until an image is added.
    """
    face_bytes = None
    if face_image and face_image.filename:
        face_bytes = await face_image.read()

    return await auth_service.register_user(
        db=db,
        name=name,
        email=email,
        password=password,
        face_image_bytes=face_bytes,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DB):
    """
    Login with email and password.
    Returns access token (short-lived) and refresh token (7 days).
    """
    return await auth_service.login_user(
        db=db,
        email=payload.email,
        password=payload.password,
    )


@router.post("/face-login", response_model=FaceLoginResponse)
async def face_login(
    db: DB,
    image: UploadFile = File(..., description="Webcam frame as JPEG/PNG"),
):
    """
    Login by matching a webcam image against stored face encodings.

    Frontend should:
        1. Capture a frame from the webcam as a Blob
        2. POST it as multipart/form-data with field name "image"
        3. Handle 401 → fall back to password login
    """
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image data received.",
        )
    return await auth_service.face_login(db=db, image_bytes=image_bytes)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(payload: RefreshRequest, db: DB):
    """
    Exchange a valid refresh token for a new access token.
    Call this when the frontend receives a 401 on any protected endpoint.
    """
    new_token = await auth_service.refresh_access_token(
        db=db,
        refresh_token=payload.refresh_token,
    )
    return AccessTokenResponse(access_token=new_token)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUser, db: DB):
    """
    Get the currently authenticated user's profile.
    Used by frontend to restore session after page refresh.
    """
    from app.repositories import user_repo
    face_enc = await user_repo.get_face_encoding_by_user(db, current_user.id)
    return UserOut(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        has_face_encoding=face_enc is not None,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: CurrentUser):
    """
    Logout endpoint.
    JWTs are stateless — we can't truly invalidate them server-side
    without a token blacklist (overkill for academic project).
    The frontend should delete both tokens from storage on logout.
    """
    return {"message": "Logged out successfully. Please delete your tokens."}