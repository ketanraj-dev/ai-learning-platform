"""
app/services/quiz_service.py
-----------------------------
Adaptive quiz engine — the academic core of the platform.
Handles quiz generation, scoring, and difficulty adjustment.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories import analytics_repo, assessment_repo
from app.schemas.assessment import (
    QuestionOut,
    QuestionResult,
    QuizOut,
    ResultOut,
)

logger = get_logger(__name__)

# ── Difficulty thresholds ──────────────────────────────────────────────────
# Score >= 80% → move up
# Score >= 50% → stay
# Score <  50% → move down
UPGRADE_THRESHOLD = 80.0
MAINTAIN_THRESHOLD = 50.0


# ── Quiz generation ────────────────────────────────────────────────────────

async def get_adaptive_quiz(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    question_count: int = 10,
) -> QuizOut:
    """
    Generate a quiz with adaptive difficulty for a specific user and course.

    ADAPTIVE LOGIC:
        1. Check user's last result for this course
        2. Determine appropriate difficulty based on that score
        3. Fetch questions at that difficulty level
        4. If not enough questions at that level, supplement from adjacent level

    First-time user (no previous results):
        → Start at "easy" to build confidence

    Args:
        user_id:        who is taking the quiz
        course_id:      which course
        question_count: how many questions (default 10)

    Returns:
        QuizOut with questions (correct_answer excluded)
    """
    # Step 1 — check last result for this course
    last_result = await assessment_repo.get_last_result_for_course(
        db, user_id, course_id
    )

    # Step 2 — determine difficulty
    if last_result is None:
        difficulty = "easy"
        logger.info("First quiz for user=%s course=%s → starting at easy", user_id, course_id)
    else:
        difficulty = _determine_difficulty(last_result.score, last_result.difficulty_level)
        logger.info(
            "Adaptive difficulty for user=%s: last_score=%.1f%% → %s",
            user_id, last_result.score, difficulty,
        )

    # Step 3 — fetch questions at target difficulty
    questions = await assessment_repo.get_questions_adaptive(
        db, course_id, difficulty, limit=question_count
    )

    # Step 4 — if not enough questions, supplement from adjacent difficulty
    if len(questions) < question_count:
        fallback_diff = _get_fallback_difficulty(difficulty)
        extra = await assessment_repo.get_questions_adaptive(
            db, course_id, fallback_diff,
            limit=question_count - len(questions),
        )
        questions.extend(extra)
        logger.info(
            "Supplemented %d questions from %s difficulty",
            len(extra), fallback_diff,
        )

    if not questions:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions available for this course yet.",
        )

    # Convert ORM objects to response schema (excludes correct_answer)
    question_out = [
        QuestionOut(
            id=q.id,
            question_text=q.question_text,
            options=q.options,
            topic_tag=q.topic_tag,
            difficulty=q.difficulty,
        )
        for q in questions
    ]

    return QuizOut(
        course_id=course_id,
        difficulty_level=difficulty,
        questions=question_out,
        total_questions=len(question_out),
        time_limit_mins=10,
    )


async def get_mock_test(
    db: AsyncSession,
    course_id: str,
    question_count: int = 30,
) -> QuizOut:
    """
    Generate a full-length mock test with mixed difficulty.
    No adaptive logic — covers all difficulty levels equally.
    """
    questions = await assessment_repo.get_questions_mixed(
        db, course_id, limit=question_count
    )

    if not questions:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions available for this course.",
        )

    question_out = [
        QuestionOut(
            id=q.id,
            question_text=q.question_text,
            options=q.options,
            topic_tag=q.topic_tag,
            difficulty=q.difficulty,
        )
        for q in questions
    ]

    return QuizOut(
        course_id=course_id,
        difficulty_level="mixed",
        questions=question_out,
        total_questions=len(question_out),
        time_limit_mins=45,
    )


# ── Quiz scoring ───────────────────────────────────────────────────────────

async def score_and_save_quiz(
    db: AsyncSession,
    user_id: str,
    course_id: str,
    submitted_answers: list[dict],
    time_taken_seconds: int = 0,
) -> ResultOut:
    """
    Score a submitted quiz, save the result, and update analytics.

    Steps:
        1. Fetch all submitted questions from DB in one query
        2. Compare each answer to correct answer
        3. Calculate score percentage
        4. Build answers_snapshot (full review data)
        5. Save result to DB
        6. Update topic-level analytics (running average)
        7. Log activity
        8. Return ResultOut with feedback

    Args:
        submitted_answers: list of {"question_id": "...", "selected_answer": "..."}

    Returns:
        ResultOut with score, per-question results, and adaptive feedback
    """
    # Step 1 — fetch all questions by ID in one DB query
    question_ids = [a["question_id"] for a in submitted_answers]
    questions_map = await assessment_repo.get_questions_by_ids(db, question_ids)

    # Step 2+3 — score each answer
    correct_count = 0
    answers_snapshot = []
    topic_scores: dict[str, list[float]] = {}  # topic_tag → list of 0/1 scores

    for answer in submitted_answers:
        q_id = answer["question_id"]
        selected = answer["selected_answer"]

        question = questions_map.get(q_id)
        if not question:
            logger.warning("Question not found during scoring: %s", q_id)
            continue

        is_correct = selected.strip() == question.correct_answer.strip()
        if is_correct:
            correct_count += 1

        # Track per-topic accuracy
        topic = question.topic_tag
        if topic not in topic_scores:
            topic_scores[topic] = []
        topic_scores[topic].append(100.0 if is_correct else 0.0)

        # Build snapshot entry
        answers_snapshot.append({
            "question_id": q_id,
            "question_text": question.question_text,
            "user_answer": selected,
            "correct_answer": question.correct_answer,
            "is_correct": is_correct,
            "explanation": question.explanation,
        })

    total = len(answers_snapshot)
    score = round((correct_count / total) * 100, 1) if total > 0 else 0.0

    # Determine difficulty that was used
    last_result = await assessment_repo.get_last_result_for_course(db, user_id, course_id)
    current_difficulty = (
        _determine_difficulty(last_result.score, last_result.difficulty_level)
        if last_result else "easy"
    )

    # Step 5 — save result
    result = await assessment_repo.save_result(
        db=db,
        user_id=user_id,
        course_id=course_id,
        score=score,
        total_questions=total,
        correct_count=correct_count,
        difficulty_level=current_difficulty,
        answers_snapshot=answers_snapshot,
    )

    # Step 6 — update analytics per topic
    for topic, scores in topic_scores.items():
        topic_accuracy = sum(scores) / len(scores)
        await analytics_repo.upsert_topic_analytics(
            db=db,
            user_id=user_id,
            topic_tag=topic,
            course_id=course_id,
            new_score=topic_accuracy,
        )

    # Step 7 — log overall quiz activity
    await analytics_repo.log_activity(
        db=db,
        user_id=user_id,
        action_type="quiz_submit",
        metadata={
            "course_id": course_id,
            "score": score,
            "correct": correct_count,
            "total": total,
            "difficulty": current_difficulty,
            "time_seconds": time_taken_seconds,
        },
    )

    # Step 8 — determine next difficulty and build feedback message
    next_difficulty = _determine_difficulty(score, current_difficulty)
    performance_message = _build_performance_message(score, current_difficulty, next_difficulty)

    logger.info(
        "Quiz scored: user=%s score=%.1f%% (%d/%d) difficulty=%s→%s",
        user_id, score, correct_count, total, current_difficulty, next_difficulty,
    )

    # Build question results for the review page
    question_results = [
        QuestionResult(
            question_id=snap["question_id"],
            question_text=snap["question_text"],
            user_answer=snap["user_answer"],
            correct_answer=snap["correct_answer"],
            is_correct=snap["is_correct"],
            explanation=snap.get("explanation"),
        )
        for snap in answers_snapshot
    ]

    return ResultOut(
        id=result.id,
        course_id=course_id,
        score=score,
        total_questions=total,
        correct_count=correct_count,
        difficulty_level=current_difficulty,
        taken_at=result.taken_at,
        question_results=question_results,
        next_difficulty=next_difficulty,
        performance_message=performance_message,
    )


# ── Private helpers ────────────────────────────────────────────────────────

def _determine_difficulty(score: float, current_difficulty: str) -> str:
    """
    Calculate next difficulty based on score and current level.

    Upgrade:   score >= 80% → move up one level
    Maintain:  50% <= score < 80% → stay
    Downgrade: score < 50% → move down one level
    """
    levels = ["easy", "medium", "hard"]
    idx = levels.index(current_difficulty) if current_difficulty in levels else 0

    if score >= UPGRADE_THRESHOLD:
        return levels[min(idx + 1, 2)]
    elif score >= MAINTAIN_THRESHOLD:
        return current_difficulty
    else:
        return levels[max(idx - 1, 0)]


def _get_fallback_difficulty(difficulty: str) -> str:
    """Return adjacent difficulty for question supplementation."""
    if difficulty == "easy":
        return "medium"
    elif difficulty == "hard":
        return "medium"
    else:
        return "easy"


def _build_performance_message(
    score: float,
    current: str,
    next_diff: str,
) -> str:
    """Generate a human-friendly performance message for the result screen."""
    if score >= 90:
        base = "Excellent work! 🎉"
    elif score >= 80:
        base = "Great job! 👍"
    elif score >= 60:
        base = "Good effort! Keep it up."
    elif score >= 40:
        base = "Nice try. Review the explanations below."
    else:
        base = "Don't worry — every attempt helps you learn."

    if next_diff != current:
        direction = "harder" if next_diff > current else "easier"
        base += f" Your next quiz will use {direction} questions ({next_diff})."
    else:
        base += f" Keep practising at {current} level."

    return base