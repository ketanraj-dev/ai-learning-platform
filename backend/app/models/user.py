"""
app/models/user.py
------------------
Two tables:
  1. users          — stores all registered students
  2. face_encodings — stores the 128-number face vector per user

WHY TWO TABLES INSTEAD OF ONE?
  - Not every user will register a face (optional feature)
  - Face encoding is large binary data — keeping it separate
    means fetching users is fast (no binary blob loaded every time)
  - Clean 1:1 relationship — easy to add/remove face auth per user
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utc_now() -> datetime:
    """Helper: current UTC time. Used as default for created_at fields."""
    return datetime.now(timezone.utc)


class User(Base):
    """
    Represents a registered student.

    Columns:
        id            — UUID primary key (random, not sequential — harder to guess)
        name          — display name
        email         — unique login identifier
        password_hash — bcrypt hash, NEVER store plain text
        role          — "student" for now, "admin" reserved for future
        is_active     — soft delete: set False instead of deleting the row
        created_at    — registration timestamp
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),   # auto-generate UUID on insert
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,         # no two users with same email
        nullable=False,
        index=True,          # index makes login lookup fast
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20),
        default="student",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────
    # These let you do: user.face_encoding, user.analytics, etc.
    # They don't create extra columns — SQLAlchemy resolves them via FK

    face_encoding: Mapped["FaceEncoding"] = relationship(
        "FaceEncoding",
        back_populates="user",
        uselist=False,           # uselist=False = one-to-one (not a list)
        cascade="all, delete-orphan",  # delete encoding when user deleted
        lazy="select",
    )
    analytics: Mapped[list["Analytics"]] = relationship(  # type: ignore[name-defined]
        "Analytics",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(  # type: ignore[name-defined]
        "ActivityLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class FaceEncoding(Base):
    """
    Stores the 128-dimensional face encoding vector for a user.

    HOW FACE RECOGNITION WORKS:
      1. User uploads a photo during registration
      2. face_recognition.face_encodings(image) returns a numpy array
         of 128 float numbers that uniquely describe the face geometry
      3. We convert that array to bytes and store it here
      4. At login: encode the webcam frame, compare to stored encoding
         using face_recognition.compare_faces() — returns True/False

    WHY BYTES AND NOT JSON?
      - Numpy array as bytes is smaller and faster to load
      - We serialize: encoding.tobytes()
      - We deserialize: np.frombuffer(row.encoding_data, dtype=np.float64)
    """
    __tablename__ = "face_encodings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),  # delete with user
        unique=True,     # one encoding per user (1:1)
        nullable=False,
        index=True,
    )
    encoding_data: Mapped[bytes] = mapped_column(
        LargeBinary,     # stores raw bytes — numpy array serialized
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # ── Relationship back to User ──────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="face_encoding",
    )

    def __repr__(self) -> str:
        return f"<FaceEncoding user_id={self.user_id}>"