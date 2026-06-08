"""
app/schemas/assessment.py
--------------------------
Request and response shapes for quizzes and results.

CRITICAL SECURITY NOTE:
  QuestionOut does NOT include correct_answer.
  If we sent correct_answer to the frontend, a user could inspect
  the network response and cheat. correct_answer is only included
  in QuestionResult (returned AFTER submission).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Question schemas ───────────────────────────────────────────────────────

class QuestionOut(BaseModel):
    """
    A question sent to the frontend DURING a quiz.
    correct_answer is intentionally excluded — added only after submission.

    options is a list like:
        ["A) Supervised", "B) Unsupervised", "C) Reinforcement", "D) Semi-supervised"]
    """
    id: str
    question_text: str
    options: list[str]
    topic_tag: str
    difficulty: str

    model_config = {"from_attributes": True}


class QuizOut(BaseModel):
    """
    Full quiz payload returned from GET /assessments/quiz/{course_id}.
    Contains the questions + metadata needed to run the timer.
    """
    course_id: str
    difficulty_level: str           # "easy" | "medium" | "hard" (adaptive)
    questions: list[QuestionOut]
    total_questions: int
    time_limit_mins: int            # 0 = no limit


# ── Submission schemas ─────────────────────────────────────────────────────

class AnswerSubmit(BaseModel):
    """One answer in a quiz submission."""
    question_id: str
    selected_answer: str            # must match one of the option strings exactly


class SubmitQuizRequest(BaseModel):
    """
    Body for POST /assessments/quiz/submit.
    Contains all answers + which course this quiz was for.
    """
    course_id: str
    answers: list[AnswerSubmit] = Field(..., min_length=1)
    time_taken_seconds: Optional[int] = None    # optional, for stats


# ── Result schemas ─────────────────────────────────────────────────────────

class QuestionResult(BaseModel):
    """
    Per-question breakdown in the result report.
    This is where correct_answer is FINALLY revealed.
    """
    question_id: str
    question_text: str
    user_answer: str
    correct_answer: str             # revealed only after submission
    is_correct: bool
    explanation: Optional[str]      # learning note shown to the student


class ResultOut(BaseModel):
    """
    Full result returned after POST /assessments/quiz/submit.
    Frontend uses this to render the ScoreReport page.
    """
    id: str
    course_id: str
    score: float                    # 0.0 to 100.0
    total_questions: int
    correct_count: int
    difficulty_level: str
    taken_at: datetime
    question_results: list[QuestionResult]

    # Adaptive feedback
    next_difficulty: str            # what difficulty will be used next time
    performance_message: str        # e.g. "Great job! Moving to harder questions."

    model_config = {"from_attributes": True}


class ResultHistoryOut(BaseModel):
    """One item in the result history list."""
    id: str
    course_id: str
    score: float
    total_questions: int
    correct_count: int
    difficulty_level: str
    taken_at: datetime

    model_config = {"from_attributes": True}


class ResultHistoryListOut(BaseModel):
    """Returned from GET /assessments/history"""
    results: list[ResultHistoryOut]
    total: int
    average_score: float