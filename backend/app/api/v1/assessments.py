"""
app/api/v1/assessments.py
--------------------------
Quiz and assessment router.
Adaptive quiz, mock test, submit answers, view history.
"""

from fastapi import APIRouter, Query

from app.api.deps import DB, CurrentUser
from app.repositories.assessment_repo import get_results_for_user
from app.schemas.assessment import (
    QuizOut,
    ResultHistoryListOut,
    ResultHistoryOut,
    ResultOut,
    SubmitQuizRequest,
)
from app.services import quiz_service
from app.repositories.assessment_repo import get_average_score_for_user

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.get("/quiz/{course_id}", response_model=QuizOut)
async def get_adaptive_quiz(
    course_id: str,
    current_user: CurrentUser,
    db: DB,
    count: int = Query(default=10, ge=5, le=30),
):
    """
    Get an adaptive quiz for a course.

    Difficulty is automatically determined based on user's
    previous performance on this course:
        - No history    → easy (first time)
        - Score < 50%   → easy
        - Score 50-79%  → medium
        - Score >= 80%  → hard

    Query param:
        count: number of questions (5-30, default 10)

    Response includes questions WITHOUT correct answers.
    Submit answers to /quiz/submit to get the scored result.
    """
    return await quiz_service.get_adaptive_quiz(
        db=db,
        user_id=current_user.id,
        course_id=course_id,
        question_count=count,
    )


@router.get("/mock-test/{course_id}", response_model=QuizOut)
async def get_mock_test(
    course_id: str,
    current_user: CurrentUser,
    db: DB,
):
    """
    Get a full-length mock test with mixed difficulty (30 questions).
    Questions are shuffled — 30% easy, 40% medium, 30% hard.
    Time limit: 45 minutes.
    """
    return await quiz_service.get_mock_test(db=db, course_id=course_id)


@router.post("/quiz/submit", response_model=ResultOut)
async def submit_quiz(
    payload: SubmitQuizRequest,
    current_user: CurrentUser,
    db: DB,
):
    """
    Submit quiz answers and get scored result.

    Request body:
        {
            "course_id": "...",
            "answers": [
                {"question_id": "...", "selected_answer": "A) ..."},
                ...
            ],
            "time_taken_seconds": 420
        }

    Response includes:
        - Score percentage
        - Per-question breakdown with correct answers revealed
        - Next difficulty recommendation
        - Performance message
    """
    answers_dicts = [
        {"question_id": a.question_id, "selected_answer": a.selected_answer}
        for a in payload.answers
    ]
    return await quiz_service.score_and_save_quiz(
        db=db,
        user_id=current_user.id,
        course_id=payload.course_id,
        submitted_answers=answers_dicts,
        time_taken_seconds=payload.time_taken_seconds or 0,
    )


@router.get("/history", response_model=ResultHistoryListOut)
async def get_result_history(
    current_user: CurrentUser,
    db: DB,
    limit: int = Query(default=20, ge=1, le=50),
):
    """
    Get recent quiz results for the current user.
    Ordered by most recent first.
    """
    results = await get_results_for_user(db, current_user.id, limit=limit)
    avg = await get_average_score_for_user(db, current_user.id)

    history = [
        ResultHistoryOut(
            id=r.id,
            course_id=r.course_id,
            score=r.score,
            total_questions=r.total_questions,
            correct_count=r.correct_count,
            difficulty_level=r.difficulty_level,
            taken_at=r.taken_at,
        )
        for r in results
    ]

    return ResultHistoryListOut(
        results=history,
        total=len(history),
        average_score=avg,
    )