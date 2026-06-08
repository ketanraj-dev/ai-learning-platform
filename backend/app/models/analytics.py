"""
app/models/analytics.py
-----------------------
Two tables:
  1. analytics     — running accuracy stats per user per topic
  2. activity_logs — every meaningful user action logged here

DESIGN — why running stats instead of computing on the fly?
  Option A (compute on the fly):
    Every time user opens dashboard, run:
    SELECT AVG(score) FROM results WHERE user_id=X AND topic=Y
    → Slow if user has 100+ quiz attempts. Dashboard feels sluggish.

  Option B (running stats) ← we use this:
    Keep one row per user per topic in analytics table.
    Update it after every quiz submission.
    Dashboard just reads the analytics table — single fast query.

  Tradeoff: slightly more complex update logic in analytics_service.py,
  but dashboard loads instantly.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Analytics(Base):
    """
    Running performance statistics — one row per user per topic.

    Example rows for one user:
        user_id=abc, topic_tag="numpy",          accuracy=85.0, sessions=4
        user_id=abc, topic_tag="neural_networks", accuracy=42.0, sessions=2
        user_id=abc, topic_tag="pandas",          accuracy=91.0, sessions=6

    This tells us: user is strong at pandas, weak at neural networks.

    Columns:
        user_id        — which student
        topic_tag      — matches Question.topic_tag exactly
                         (e.g. "numpy", "pandas", "neural_networks")
        course_id      — which course this topic belongs to
        accuracy_pct   — running weighted average: 0.0 to 100.0
        sessions_count — how many quizzes included this topic
        difficulty_level — current adaptive difficulty for this user+topic
                           "easy" | "medium" | "hard"
                           updated after each quiz based on score
        last_score     — most recent quiz score for this topic
        updated_at     — when this row was last updated

    HOW accuracy_pct IS UPDATED (in analytics_service.py):
        new_accuracy = (old_accuracy * old_count + new_score) / (old_count + 1)
        This is an incremental weighted average — no need to re-read all results.
    """
    __tablename__ = "analytics"

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
    topic_tag: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    course_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    accuracy_pct: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    sessions_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    difficulty_level: Mapped[str] = mapped_column(
        String(10),
        default="easy",       # everyone starts on easy
        nullable=False,
    )
    last_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,     # auto-update timestamp on every change
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="analytics",
    )

    def __repr__(self) -> str:
        return (
            f"<Analytics user={self.user_id} "
            f"topic={self.topic_tag} accuracy={self.accuracy_pct:.1f}%>"
        )


class ActivityLog(Base):
    """
    Append-only log of every meaningful user action.
    Used to build the learning trend charts.

    action_type values:
        "login"            — user logged in
        "lesson_complete"  — user completed a lesson
        "quiz_submit"      — user submitted a quiz
        "ai_chat"          — user sent a message to AI tutor
        "face_login"       — user logged in via face recognition
        "voice_query"      — user used voice input

    metadata: JSON dict with context.
    Examples:
        quiz_submit: {"course_id": "...", "score": 85.0, "topic": "numpy"}
        lesson_complete: {"lesson_id": "...", "course_id": "..."}
        ai_chat: {"message_length": 42}

    WHY LOG EVERYTHING?
      The trend charts need time-series data:
      "How many sessions per day this week?"
      "Which topics did the user practice?"
      ActivityLog is the source of truth for these queries.
    """
    __tablename__ = "activity_logs"

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
    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,      # indexed for time-range queries
    )

    # ── Relationships ──────────────────────────────────────────
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="activity_logs",
    )

    def __repr__(self) -> str:
        return (
            f"<ActivityLog user={self.user_id} "
            f"action={self.action_type} at={self.created_at}>"
        )