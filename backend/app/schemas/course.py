"""
app/schemas/course.py
---------------------
Request and response shapes for courses, lessons, and progress.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Lesson schemas ─────────────────────────────────────────────────────────

class LessonOut(BaseModel):
    """
    A single lesson as returned to the frontend.
    Includes the user's completion status (joined from lesson_progress).
    """
    id: str
    course_id: str
    title: str
    content: str
    order_index: int
    lesson_type: str        # "text" | "video" | "code"
    completed: bool = False # injected by course_repo based on user's progress

    model_config = {"from_attributes": True}


class LessonListOut(BaseModel):
    """Wrapper returned from GET /courses/{id}/lessons"""
    lessons: list[LessonOut]
    total: int
    completed_count: int
    progress_pct: float     # 0.0 to 100.0


# ── Course schemas ─────────────────────────────────────────────────────────

class CourseOut(BaseModel):
    """
    A course card as shown on the dashboard.

    progress_pct is COMPUTED — not stored in DB.
    The repo calculates it: completed_lessons / total_lessons * 100
    """
    id: str
    title: str
    description: str
    subject: str
    difficulty: int         # 1=Beginner, 2=Intermediate, 3=Advanced
    is_active: bool
    created_at: datetime
    total_lessons: int = 0
    completed_lessons: int = 0
    progress_pct: float = 0.0

    model_config = {"from_attributes": True}


class CourseListOut(BaseModel):
    """Wrapper returned from GET /courses"""
    courses: list[CourseOut]
    total: int


# ── Progress schemas ───────────────────────────────────────────────────────

class CompleteLesson(BaseModel):
    """
    Body for POST /courses/{course_id}/lessons/{lesson_id}/complete
    Empty body — the lesson_id comes from the URL path parameter.
    We keep this schema for future extensibility (e.g. time_spent_seconds).
    """
    pass


class LessonProgressOut(BaseModel):
    """Returned after marking a lesson complete."""
    lesson_id: str
    completed: bool
    completed_at: Optional[datetime]
    course_progress_pct: float    # updated progress for the whole course

    model_config = {"from_attributes": True}