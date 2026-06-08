"""
app/models/assessment.py
------------------------
Three tables:
  1. questions    — the question bank (MCQ with 4 options)
  2. assessments  — a named quiz or mock test linked to a course
  3. results      — a user's submitted attempt at an assessment

ADAPTIVE DIFFICULTY DESIGN:
  Each question has a difficulty field: "easy" | "medium" | "hard"
  quiz_service reads the user's last result for this course,
  then fetches questions filtered by the appropriate difficulty.

  Score ≥ 80% → next quiz uses "hard" questions
  Score 50-79% → next quiz uses "medium" questions
  Score < 50%  → next quiz uses "easy" questions
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

# JSON type — works for both SQLite and PostgreSQL
from sqlalchemy import JSON

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Question(Base):
    """
    A single MCQ question in the question bank.

    Columns:
        course_id      — which course this question belongs to
        question_text  — the actual question
        options        — stored as JSON list: ["A) ...", "B) ...", "C) ...", "D) ..."]
        correct_answer — the correct option string (e.g. "A) Linear Regression")
        difficulty     — "easy" | "medium" | "hard"
        topic_tag      — sub-topic label (e.g. "neural_networks", "pandas")
                         used for analytics: which topics is the user weak at?
        explanation    — shown after quiz submission as learning feedback

    IMPORTANT: correct_answer is NEVER sent to the frontend during a quiz.
    Only sent back in the result after submission. See schemas/assessment.py.
    """
    __tablename__ = "questions"

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
    question_text: Mapped[str] = mapped_column(Text, nullable=False)

    # JSON list of 4 options — SQLAlchemy JSON type handles serialization
    # Example: ["A) Supervised", "B) Unsupervised", "C) Reinforcement", "D) None"]
    options: Mapped[list] = mapped_column(JSON, nullable=False)

    correct_answer: Mapped[str] = mapped_column(String(500), nullable=False)

    difficulty: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="medium",
        index=True,      # indexed because we filter by difficulty often
    )
    topic_tag: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,      # indexed for analytics grouping
    )
    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,   # optional — shown after quiz as learning note
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────
    course: Mapped["Course"] = relationship(  # type: ignore[name-defined]
        "Course",
        back_populates="questions",
    )

    def __repr__(self) -> str:
        return (
            f"<Question id={self.id} "
            f"difficulty={self.difficulty} topic={self.topic_tag}>"
        )


class Assessment(Base):
    """
    A named quiz or mock test tied to a course.

    assessment_type values:
        "quiz"      — short topic-specific quiz (10 questions)
        "mock_test" — full-length mixed quiz (30 questions)

    time_limit_mins:
        0 = no time limit
        10 = 10 minute quiz
        60 = 1 hour mock test
    """
    __tablename__ = "assessments"

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
    assessment_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="quiz",
    )
    time_limit_mins: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────
    results: Mapped[list["Result"]] = relationship(
        "Result",
        back_populates="assessment",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Assessment id={self.id} title={self.title}>"


class Result(Base):
    """
    One row = one quiz attempt by one user.

    Columns:
        user_id           — who took it
        assessment_id     — which assessment (nullable for ad-hoc quizzes)
        course_id         — stored directly for easy analytics queries
        score             — percentage: 0.0 to 100.0
        total_questions   — how many questions were in this attempt
        correct_count     — how many they got right
        difficulty_level  — which difficulty band was used ("easy"/"medium"/"hard")
        answers_snapshot  — JSON: stores submitted answers + correct answers
                            for the ScoreReport page (show right/wrong per question)
        taken_at          — when the attempt happened

    WHY answers_snapshot AS JSON?
      We want to show the user exactly what they answered vs what was correct.
      Storing this as a JSON blob is simpler than a separate answer_details table
      for an academic project.

      Structure:
      [
        {
          "question_id": "...",
          "question_text": "...",
          "user_answer": "B) ...",
          "correct_answer": "A) ...",
          "is_correct": false,
          "explanation": "..."
        },
        ...
      ]
    """
    __tablename__ = "results"

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
    assessment_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("assessments.id", ondelete="SET NULL"),
        nullable=True,
    )
    course_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="medium",
    )
    answers_snapshot: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    taken_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    # ── Relationships ──────────────────────────────────────────
    assessment: Mapped["Assessment | None"] = relationship(
        "Assessment",
        back_populates="results",
    )

    def __repr__(self) -> str:
        return (
            f"<Result user={self.user_id} "
            f"score={self.score} taken={self.taken_at}>"
        )