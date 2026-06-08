"""
app/schemas/auth.py
-------------------
Request and response shapes for all auth endpoints.

NAMING CONVENTION USED THROUGHOUT:
  *Request  — data coming IN  from frontend (POST body)
  *Out      — data going  OUT to frontend (response)
  *Response — full response wrapper (contains tokens + user info)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Registration ───────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """
    Body for POST /auth/register (JSON part — face image sent separately).

    Validations:
      - name: 2-100 chars
      - email: must be valid email format (pydantic EmailStr handles this)
      - password: minimum 6 characters
    """
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr                                       # auto-validates format
    password: str = Field(..., min_length=6)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        """Strip whitespace and ensure name isn't just spaces."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Name cannot be blank")
        return stripped


# ── Login ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Body for POST /auth/login"""
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    """Body for POST /auth/refresh"""
    refresh_token: str


# ── User output shape ──────────────────────────────────────────────────────

class UserOut(BaseModel):
    """
    Safe user representation — NEVER includes password_hash.
    Returned inside TokenResponse and also from GET /users/me.
    """
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    has_face_encoding: bool = False    # frontend uses this to show face login option

    model_config = {"from_attributes": True}  # allows .model_validate(orm_object)


# ── Token response ─────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """
    Returned after successful login or registration.
    Frontend stores both tokens — access for API calls, refresh to get new access.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class AccessTokenResponse(BaseModel):
    """Returned from POST /auth/refresh — new access token only."""
    access_token: str
    token_type: str = "bearer"


# ── Face login ─────────────────────────────────────────────────────────────

class FaceLoginResponse(BaseModel):
    """
    Returned from POST /auth/face-login.
    Same as TokenResponse but includes a confidence score.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut
    confidence: float = Field(..., description="Match confidence 0.0-1.0")