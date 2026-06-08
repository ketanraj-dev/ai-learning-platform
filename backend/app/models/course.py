"""
app/models/course.py
--------------------
Three tables:
  1. courses         — the 5 DS/AI-ML courses
  2. lessons         — individual lessons inside each course
  3. lesson_progress — tracks which lessons each user has completed

DESIGN DECISION — why lesson_progress is its own table:
  Many-to-many: one user completes many lessons, one lesson completed
  by many users. We can't put this in users or lessons directly.
  A junction table (lesson_progress) is the standard SQL solution.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Course(Base):
    """
    A top-level learning course (e.g. 'Python for Data Science').

    Columns:
        title       — display name
        description — shown on the course card
        subject     — category tag (e.g. "Machine Learning")
        difficulty  — 1=Beginner, 2=Intermediate, 3=Advanced
                      used to suggest courses to new vs experienced users
        is_active   — hide course without deleting it
    """
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,      # we query by subject often
    )
    difficulty: Mapped[int] = mapped_column(
        Integer,
        default=1,
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
    lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Lesson.order_index",  # always return lessons in order
        lazy="select",
    )
    questions: Mapped[list["Question"]] = relationship(  # type: ignore[name-defined]
        "Question",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Course id={self.id} title={self.title}>"


class Lesson(Base):
    """
    A single lesson inside a course.

    Columns:
        course_id   — which course this belongs to
        title       — lesson title shown in the sidebar
        content     — full lesson text (markdown supported)
        order_index — 1, 2, 3... controls display order
        lesson_type — "text" | "video" | "code"
                      frontend renders differently based on type
    """
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    course_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    lesson_type: Mapped[str] = mapped_column(
        String(20),
        default="text",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="lessons",
    )
    progress_records: Mapped[list["LessonProgress"]] = relationship(
        "LessonProgress",
        back_populates="lesson",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Lesson id={self.id} title={self.title} order={self.order_index}>"


class LessonProgress(Base):
    """
    Tracks whether a specific user has completed a specific lesson.

    This is the junction table for User <-> Lesson many-to-many.

    Example rows:
        user_id=abc, lesson_id=123, completed=True   ← user finished
        user_id=abc, lesson_id=124, completed=False  ← user started
        user_id=xyz, lesson_id=123, completed=True   ← different user

    UniqueConstraint ensures one row per user+lesson combo.
    """
    __tablename__ = "lesson_progress"

    # Composite uniqueness: one record per user per lesson
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,   # null until actually completed
    )

    # ── Relationships ──────────────────────────────────────────
    lesson: Mapped["Lesson"] = relationship(
        "Lesson",
        back_populates="progress_records",
    )

    def __repr__(self) -> str:
        return (
            f"<LessonProgress user={self.user_id} "
            f"lesson={self.lesson_id} done={self.completed}>"
        )