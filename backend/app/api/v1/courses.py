"""
app/api/v1/courses.py
---------------------
Courses and lessons router.
All endpoints are protected — must be logged in to access content.
"""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DB, CurrentUser
from app.repositories import course_repo
from app.schemas.course import (
    CourseListOut,
    CourseOut,
    LessonListOut,
    LessonProgressOut,
)

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=CourseListOut)
async def list_courses(current_user: CurrentUser, db: DB):
    """
    Get all active courses with the current user's progress.

    Each course includes:
        - progress_pct: how much of the course is completed
        - total_lessons / completed_lessons counts
    """
    courses_data = await course_repo.get_all_courses(db, current_user.id)
    course_list = [CourseOut(**c) for c in courses_data]
    return CourseListOut(courses=course_list, total=len(course_list))


@router.get("/{course_id}", response_model=CourseOut)
async def get_course(course_id: str, current_user: CurrentUser, db: DB):
    """Get a single course by ID."""
    course = await course_repo.get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )
    # Get progress for this course
    courses_data = await course_repo.get_all_courses(db, current_user.id)
    course_dict = next((c for c in courses_data if c["id"] == course_id), None)
    if not course_dict:
        raise HTTPException(status_code=404, detail="Course not found.")
    return CourseOut(**course_dict)


@router.get("/{course_id}/lessons", response_model=LessonListOut)
async def get_lessons(course_id: str, current_user: CurrentUser, db: DB):
    """
    Get all lessons for a course with completion status.

    Lessons are ordered by order_index (1, 2, 3...).
    Each lesson has a 'completed' flag showing if this user finished it.
    """
    # Verify course exists
    course = await course_repo.get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    lessons_data = await course_repo.get_lessons_for_course(
        db, course_id, current_user.id
    )

    completed_count = sum(1 for l in lessons_data if l["completed"])
    total = len(lessons_data)
    progress_pct = round((completed_count / total) * 100, 1) if total > 0 else 0.0

    from app.schemas.course import LessonOut
    lessons = [LessonOut(**l) for l in lessons_data]

    return LessonListOut(
        lessons=lessons,
        total=total,
        completed_count=completed_count,
        progress_pct=progress_pct,
    )


@router.post(
    "/{course_id}/lessons/{lesson_id}/complete",
    response_model=LessonProgressOut,
)
async def complete_lesson(
    course_id: str,
    lesson_id: str,
    current_user: CurrentUser,
    db: DB,
):
    """
    Mark a lesson as completed for the current user.

    Safe to call multiple times — idempotent (won't create duplicates).
    Returns updated course progress percentage.
    """
    # Verify lesson belongs to this course
    lesson = await course_repo.get_lesson_by_id(db, lesson_id)
    if not lesson or lesson.course_id != course_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found in this course.",
        )

    progress = await course_repo.mark_lesson_complete(db, current_user.id, lesson_id)
    updated_pct = await course_repo.get_course_progress_pct(db, course_id, current_user.id)

    # Log activity
    from app.repositories import analytics_repo
    await analytics_repo.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="lesson_complete",
        metadata={"lesson_id": lesson_id, "course_id": course_id},
    )

    return LessonProgressOut(
        lesson_id=lesson_id,
        completed=progress.completed,
        completed_at=progress.completed_at,
        course_progress_pct=updated_pct,
    )