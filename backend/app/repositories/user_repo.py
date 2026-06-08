"""
app/repositories/user_repo.py
------------------------------
All database queries for users and face encodings.
Called only by services — never directly from routers.
"""

from typing import Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.user import FaceEncoding, User

logger = get_logger(__name__)


# ── User queries ───────────────────────────────────────────────────────────

async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> Optional[User]:
    """
    Fetch a user by email address.
    Used during login to find who is trying to authenticate.
    Returns None if email not found — caller decides what to do.
    """
    result = await db.execute(
        select(User).where(User.email == email.lower().strip())
    )
    return result.scalar_one_or_none()


async def get_user_by_id(
    db: AsyncSession,
    user_id: str,
) -> Optional[User]:
    """
    Fetch a user by their UUID primary key.
    Used by get_current_user dependency in api/deps.py after JWT decode.
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    name: str,
    email: str,
    password_hash: str,
    role: str = "student",
) -> User:
    """
    Insert a new user row and return the created object.

    Note: we do NOT commit here — the get_db() dependency in session.py
    commits after the entire endpoint function completes successfully.
    This means if anything fails after create_user(), the whole transaction
    rolls back and no partial data is saved.
    """
    user = User(
        name=name,
        email=email.lower().strip(),   # normalize email to lowercase
        password_hash=password_hash,
        role=role,
    )
    db.add(user)
    await db.flush()    # flush assigns the UUID without committing
                        # so we can use user.id immediately
    logger.info("Created user: %s (id=%s)", email, user.id)
    return user


async def get_user_with_face_encoding(
    db: AsyncSession,
    user_id: str,
) -> Optional[User]:
    """
    Fetch user AND eagerly load their face_encoding in one query.
    Used during face login to check if user has an encoding registered.

    selectinload avoids the N+1 query problem:
    without it, accessing user.face_encoding would fire a second DB query.
    """
    result = await db.execute(
        select(User)
        .options(selectinload(User.face_encoding))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def email_exists(
    db: AsyncSession,
    email: str,
) -> bool:
    """
    Check if an email is already registered.
    Called during registration to prevent duplicates.
    More efficient than get_user_by_email() — no need to load the full row.
    """
    result = await db.execute(
        select(User.id).where(User.email == email.lower().strip())
    )
    return result.scalar_one_or_none() is not None


# ── Face encoding queries ──────────────────────────────────────────────────

async def save_face_encoding(
    db: AsyncSession,
    user_id: str,
    encoding_array: np.ndarray,
) -> FaceEncoding:
    """
    Store a numpy face encoding as bytes in the database.

    HOW NUMPY → BYTES WORKS:
        encoding_array is a shape (128,) float64 numpy array
        .tobytes() converts it to raw binary (1024 bytes = 128 * 8 bytes per float64)
        We reverse this in get_all_face_encodings() with np.frombuffer()

    Args:
        encoding_array: 128-dimensional face encoding from face_recognition lib
    """
    # Check if user already has an encoding — if so, update it
    existing = await db.execute(
        select(FaceEncoding).where(FaceEncoding.user_id == user_id)
    )
    face_enc = existing.scalar_one_or_none()

    if face_enc:
        # Update existing encoding
        face_enc.encoding_data = encoding_array.tobytes()
        logger.info("Updated face encoding for user_id=%s", user_id)
    else:
        # Create new encoding
        face_enc = FaceEncoding(
            user_id=user_id,
            encoding_data=encoding_array.tobytes(),
        )
        db.add(face_enc)
        logger.info("Saved new face encoding for user_id=%s", user_id)

    await db.flush()
    return face_enc


async def get_all_face_encodings(
    db: AsyncSession,
) -> list[tuple[str, np.ndarray]]:
    """
    Fetch ALL face encodings from the database.
    Used during face login to compare the webcam frame against everyone.

    Returns:
        List of (user_id, numpy_array) tuples.
        face_service.py iterates this list to find a match.

    Performance note: for an academic project with <100 users this is fine.
    For production, you'd use a vector similarity search (pgvector, Pinecone).
    """
    result = await db.execute(
        select(FaceEncoding.user_id, FaceEncoding.encoding_data)
    )
    rows = result.all()

    # Convert bytes back to numpy arrays
    encodings = []
    for user_id, encoding_bytes in rows:
        try:
            array = np.frombuffer(encoding_bytes, dtype=np.float64)
            encodings.append((user_id, array))
        except Exception as e:
            logger.warning("Corrupt encoding for user_id=%s: %s", user_id, e)
            continue     # skip corrupt encodings, don't crash

    return encodings


async def get_face_encoding_by_user(
    db: AsyncSession,
    user_id: str,
) -> Optional[np.ndarray]:
    """
    Get the face encoding for a specific user as a numpy array.
    Returns None if user has no face encoding registered.
    """
    result = await db.execute(
        select(FaceEncoding.encoding_data)
        .where(FaceEncoding.user_id == user_id)
    )
    encoding_bytes = result.scalar_one_or_none()

    if encoding_bytes is None:
        return None

    return np.frombuffer(encoding_bytes, dtype=np.float64)