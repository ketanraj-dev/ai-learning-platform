"""
app/repositories/course_repo.py
--------------------------------
All database queries for courses, lessons, and lesson progress.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.course import Course, Lesson, LessonProgress

logger = get_logger(__name__)


# ── Course queries ─────────────────────────────────────────────────────────

async def get_all_courses(
    db: AsyncSession,
    user_id: str,
) -> list[dict]:
    """
    Fetch all active courses with the user's progress percentage.

    Returns a list of dicts (not ORM objects) because we're combining
    data from multiple tables (courses + lesson_progress) into one shape.

    Each dict has:
        id, title, description, subject, difficulty, is_active,
        created_at, total_lessons, completed_lessons, progress_pct
    """
    # Step 1: get all active courses
    courses_result = await db.execute(
        select(Course).where(Course.is_active == True).order_by(Course.created_at)
    )
    courses = courses_result.scalars().all()

    enriched = []
    for course in courses:
        # Step 2: count total lessons for this course
        total_result = await db.execute(
            select(func.count(Lesson.id))
            .where(Lesson.course_id == course.id)
        )
        total_lessons = total_result.scalar() or 0

        # Step 3: count completed lessons for this user in this course
        completed_result = await db.execute(
            select(func.count(LessonProgress.id))
            .join(Lesson, LessonProgress.lesson_id == Lesson.id)
            .where(
                Lesson.course_id == course.id,
                LessonProgress.user_id == user_id,
                LessonProgress.completed == True,
            )
        )
        completed_lessons = completed_result.scalar() or 0

        # Step 4: compute progress percentage
        progress_pct = (
            round((completed_lessons / total_lessons) * 100, 1)
            if total_lessons > 0
            else 0.0
        )

        enriched.append({
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "subject": course.subject,
            "difficulty": course.difficulty,
            "is_active": course.is_active,
            "created_at": course.created_at,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "progress_pct": progress_pct,
        })

    return enriched


async def get_course_by_id(
    db: AsyncSession,
    course_id: str,
) -> Optional[Course]:
    """Fetch a single course by ID. Returns None if not found."""
    result = await db.execute(
        select(Course).where(Course.id == course_id, Course.is_active == True)
    )
    return result.scalar_one_or_none()


# ── Lesson queries ─────────────────────────────────────────────────────────

async def get_lessons_for_course(
    db: AsyncSession,
    course_id: str,
    user_id: str,
) -> list[dict]:
    """
    Fetch all lessons for a course, with each lesson's completion
    status for the requesting user.

    Returns list of dicts with 'completed' field injected.
    Lessons are ordered by order_index (1, 2, 3...).
    """
    # Fetch all lessons ordered by index
    lessons_result = await db.execute(
        select(Lesson)
        .where(Lesson.course_id == course_id)
        .order_by(Lesson.order_index)
    )
    lessons = lessons_result.scalars().all()

    # Fetch all progress records for this user in this course in one query
    # (avoid N+1 — one query for all lessons, not one per lesson)
    progress_result = await db.execute(
        select(LessonProgress.lesson_id)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .where(
            Lesson.course_id == course_id,
            LessonProgress.user_id == user_id,
            LessonProgress.completed == True,
        )
    )
    # Set of completed lesson IDs for O(1) lookup
    completed_ids = set(progress_result.scalars().all())

    return [
        {
            "id": lesson.id,
            "course_id": lesson.course_id,
            "title": lesson.title,
            "content": lesson.content,
            "order_index": lesson.order_index,
            "lesson_type": lesson.lesson_type,
            "completed": lesson.id in completed_ids,
        }
        for lesson in lessons
    ]


async def get_lesson_by_id(
    db: AsyncSession,
    lesson_id: str,
) -> Optional[Lesson]:
    """Fetch a single lesson by ID."""
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    return result.scalar_one_or_none()


# ── Progress queries ───────────────────────────────────────────────────────

async def mark_lesson_complete(
    db: AsyncSession,
    user_id: str,
    lesson_id: str,
) -> LessonProgress:
    """
    Mark a lesson as completed for a user.
    Uses upsert logic: creates a new record or updates existing one.

    Returns the LessonProgress record.
    """
    # Check if progress record already exists
    existing_result = await db.execute(
        select(LessonProgress).where(
            LessonProgress.user_id == user_id,
            LessonProgress.lesson_id == lesson_id,
        )
    )
    progress = existing_result.scalar_one_or_none()

    if progress:
        # Already exists — just mark completed if not already
        if not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.now(timezone.utc)
            logger.info("Lesson %s marked complete for user %s", lesson_id, user_id)
    else:
        # First time visiting this lesson — create record
        progress = LessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            completed=True,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(progress)
        logger.info("New progress record: lesson %s for user %s", lesson_id, user_id)

    await db.flush()
    return progress


async def get_course_progress_pct(
    db: AsyncSession,
    course_id: str,
    user_id: str,
) -> float:
    """
    Calculate the completion percentage for one user in one course.
    Called after marking a lesson complete to return updated progress.
    """
    total_result = await db.execute(
        select(func.count(Lesson.id)).where(Lesson.course_id == course_id)
    )
    total = total_result.scalar() or 0
    if total == 0:
        return 0.0

    completed_result = await db.execute(
        select(func.count(LessonProgress.id))
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .where(
            Lesson.course_id == course_id,
            LessonProgress.user_id == user_id,
            LessonProgress.completed == True,
        )
    )
    completed = completed_result.scalar() or 0
    return round((completed / total) * 100, 1)


async def get_total_completed_lessons(
    db: AsyncSession,
    user_id: str,
) -> int:
    """
    Total lessons completed by a user across ALL courses.
    Used in the analytics dashboard.
    """
    result = await db.execute(
        select(func.count(LessonProgress.id)).where(
            LessonProgress.user_id == user_id,
            LessonProgress.completed == True,
        )
    )
    return result.scalar() or 0