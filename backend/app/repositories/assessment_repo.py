"""
app/repositories/assessment_repo.py
-------------------------------------
All database queries for questions, assessments, and results.
Contains the adaptive difficulty query — the heart of the learning engine.
"""

import random
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.assessment import Assessment, Question, Result

logger = get_logger(__name__)


# ── Question queries ───────────────────────────────────────────────────────

async def get_questions_adaptive(
    db: AsyncSession,
    course_id: str,
    difficulty: str,
    limit: int = 10,
) -> list[Question]:
    """
    Fetch questions filtered by course and difficulty level.
    This is the ADAPTIVE part — difficulty is determined by quiz_service
    based on the user's last score for this course.

    Args:
        course_id:  which course to pull questions from
        difficulty: "easy" | "medium" | "hard"
        limit:      how many questions to return (default 10 for a quiz)

    The questions are shuffled randomly so every quiz feels different
    even though the question bank is fixed.
    """
    result = await db.execute(
        select(Question).where(
            Question.course_id == course_id,
            Question.difficulty == difficulty,
        )
    )
    questions = result.scalars().all()

    # Shuffle and limit — random selection keeps quizzes fresh
    shuffled = list(questions)
    random.shuffle(shuffled)
    return shuffled[:limit]


async def get_questions_mixed(
    db: AsyncSession,
    course_id: str,
    limit: int = 30,
) -> list[Question]:
    """
    Fetch a mixed-difficulty set of questions for mock tests.
    Splits limit roughly: 30% easy, 40% medium, 30% hard.

    Args:
        course_id: which course
        limit:     total questions (default 30 for a mock test)
    """
    easy_limit = int(limit * 0.3)     # 9 easy
    medium_limit = int(limit * 0.4)   # 12 medium
    hard_limit = limit - easy_limit - medium_limit  # 9 hard

    all_questions = []
    for diff, lim in [("easy", easy_limit), ("medium", medium_limit), ("hard", hard_limit)]:
        result = await db.execute(
            select(Question).where(
                Question.course_id == course_id,
                Question.difficulty == diff,
            )
        )
        qs = result.scalars().all()
        shuffled = list(qs)
        random.shuffle(shuffled)
        all_questions.extend(shuffled[:lim])

    # Final shuffle to mix difficulties throughout the test
    random.shuffle(all_questions)
    return all_questions


async def get_question_by_id(
    db: AsyncSession,
    question_id: str,
) -> Optional[Question]:
    """Fetch a single question by ID. Used during scoring."""
    result = await db.execute(
        select(Question).where(Question.id == question_id)
    )
    return result.scalar_one_or_none()


async def get_questions_by_ids(
    db: AsyncSession,
    question_ids: list[str],
) -> dict[str, Question]:
    """
    Fetch multiple questions by their IDs in one query.
    Returns a dict keyed by question_id for O(1) lookup during scoring.

    Example:
        questions = await get_questions_by_ids(db, ["id1", "id2", "id3"])
        q = questions["id1"]  # instant lookup
    """
    result = await db.execute(
        select(Question).where(Question.id.in_(question_ids))
    )
    questions = result.scalars().all()
    return {q.id: q for q in questions}


# ── Result queries ─────────────────────────────────────────────────────────

async def save_result(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    score: float,
    total_questions: int,
    correct_count: int,
    difficulty_level: str,
    answers_snapshot: list,
    assessment_id: Optional[str] = None,
) -> Result:
    """
    Save a completed quiz attempt.
    Called immediately after scoring in quiz_service.py.

    answers_snapshot is the full list of QuestionResult dicts —
    stored as JSON so the user can review their quiz later.
    """
    result_obj = Result(
        user_id=user_id,
        course_id=course_id,
        assessment_id=assessment_id,
        score=score,
        total_questions=total_questions,
        correct_count=correct_count,
        difficulty_level=difficulty_level,
        answers_snapshot=answers_snapshot,
    )
    db.add(result_obj)
    await db.flush()
    logger.info(
        "Saved result: user=%s course=%s score=%.1f%%",
        user_id, course_id, score
    )
    return result_obj


async def get_last_result_for_course(
    db: AsyncSession,
    user_id: str,
    course_id: str,
) -> Optional[Result]:
    """
    Get the most recent quiz result for a user in a specific course.
    Used by quiz_service to determine what difficulty to serve next.

    Returns None if user has never taken a quiz for this course
    → quiz_service defaults to "easy" for first-time users.
    """
    result = await db.execute(
        select(Result)
        .where(
            Result.user_id == user_id,
            Result.course_id == course_id,
        )
        .order_by(Result.taken_at.desc())   # most recent first
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_results_for_user(
    db: AsyncSession,
    user_id: str,
    limit: int = 20,
) -> list[Result]:
    """
    Get recent quiz results for a user across all courses.
    Used in the result history page.
    """
    result = await db.execute(
        select(Result)
        .where(Result.user_id == user_id)
        .order_by(Result.taken_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_average_score_for_user(
    db: AsyncSession,
    user_id: str,
) -> float:
    """
    Compute the overall average score across all quiz attempts.
    Used in the analytics dashboard summary card.
    """
    result = await db.execute(
        select(func.avg(Result.score)).where(Result.user_id == user_id)
    )
    avg = result.scalar()
    return round(float(avg), 1) if avg is not None else 0.0


async def get_results_count_for_user(
    db: AsyncSession,
    user_id: str,
) -> int:
    """Total number of quiz attempts by a user."""
    result = await db.execute(
        select(func.count(Result.id)).where(Result.user_id == user_id)
    )
    return result.scalar() or 0