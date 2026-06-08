"""
app/repositories/analytics_repo.py
------------------------------------
All database queries for analytics and activity logs.
Contains the upsert logic for running accuracy stats.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.analytics import ActivityLog, Analytics

logger = get_logger(__name__)


# ── Analytics queries ──────────────────────────────────────────────────────

async def get_analytics_for_user(
    db: AsyncSession,
    user_id: str,
) -> list[Analytics]:
    """
    Fetch all topic analytics rows for a user.
    Each row = one topic the user has been quizzed on.
    Ordered by accuracy ascending so weakest topics come first.
    """
    result = await db.execute(
        select(Analytics)
        .where(Analytics.user_id == user_id)
        .order_by(Analytics.accuracy_pct.asc())
    )
    return result.scalars().all()


async def get_topic_analytics(
    db: AsyncSession,
    user_id: str,
    topic_tag: str,
) -> Optional[Analytics]:
    """
    Fetch analytics for one specific topic for a user.
    Used by upsert_topic_analytics to check if row exists.
    """
    result = await db.execute(
        select(Analytics).where(
            Analytics.user_id == user_id,
            Analytics.topic_tag == topic_tag,
        )
    )
    return result.scalar_one_or_none()


async def upsert_topic_analytics(
    db: AsyncSession,
    user_id: str,
    topic_tag: str,
    course_id: str,
    new_score: float,
) -> Analytics:
    """
    Insert or update the running accuracy for a user+topic combination.

    UPSERT = UPDATE if exists, INSERT if not.

    HOW THE RUNNING AVERAGE WORKS:
        First attempt:  accuracy = new_score, sessions = 1
        Later attempts: accuracy = (old_accuracy * old_count + new_score)
                                   / (old_count + 1)

        Example:
            After quiz 1: score=60 → accuracy=60.0, sessions=1
            After quiz 2: score=80 → accuracy=(60*1 + 80)/2 = 70.0, sessions=2
            After quiz 3: score=90 → accuracy=(70*2 + 90)/3 = 76.7, sessions=3

    HOW DIFFICULTY IS UPDATED:
        score >= 80 → upgrade to next difficulty
        score >= 50 → stay at current difficulty
        score <  50 → downgrade to easier difficulty
    """
    existing = await get_topic_analytics(db, user_id, topic_tag)

    if existing:
        # Update running average
        old_count = existing.sessions_count
        existing.accuracy_pct = round(
            (existing.accuracy_pct * old_count + new_score) / (old_count + 1),
            2,
        )
        existing.sessions_count = old_count + 1
        existing.last_score = new_score

        # Update adaptive difficulty
        existing.difficulty_level = _calculate_next_difficulty(
            current=existing.difficulty_level,
            score=new_score,
        )
        logger.info(
            "Updated analytics: user=%s topic=%s accuracy=%.1f%% difficulty=%s",
            user_id, topic_tag, existing.accuracy_pct, existing.difficulty_level,
        )
        return existing
    else:
        # First time this user has been quizzed on this topic
        initial_difficulty = _calculate_next_difficulty("easy", new_score)
        row = Analytics(
            user_id=user_id,
            topic_tag=topic_tag,
            course_id=course_id,
            accuracy_pct=round(new_score, 2),
            sessions_count=1,
            difficulty_level=initial_difficulty,
            last_score=new_score,
        )
        db.add(row)
        await db.flush()
        logger.info(
            "Created analytics: user=%s topic=%s score=%.1f%%",
            user_id, topic_tag, new_score,
        )
        return row


def _calculate_next_difficulty(current: str, score: float) -> str:
    """
    Determine next difficulty based on current level and score.

    Rules:
        score >= 80% → move up one level (or stay at hard)
        score >= 50% → stay at current level
        score <  50% → move down one level (or stay at easy)
    """
    levels = ["easy", "medium", "hard"]
    idx = levels.index(current) if current in levels else 0

    if score >= 80.0:
        return levels[min(idx + 1, 2)]   # upgrade, cap at hard
    elif score >= 50.0:
        return current                    # stay same
    else:
        return levels[max(idx - 1, 0)]   # downgrade, floor at easy


# ── Activity log queries ───────────────────────────────────────────────────

async def log_activity(
    db: AsyncSession,
    user_id: str,
    action_type: str,
    metadata: Optional[dict] = None,
) -> ActivityLog:
    """
    Append a new activity log entry.
    Called after any significant user action.

    action_type examples:
        "login", "lesson_complete", "quiz_submit",
        "ai_chat", "face_login", "voice_query"
    """
    log = ActivityLog(
        user_id=user_id,
        action_type=action_type,
        metadata_json=metadata or {},
    )
    db.add(log)
    await db.flush()
    return log


async def get_weekly_trend(
    db: AsyncSession,
    user_id: str,
    weeks: int = 6,
) -> list[dict]:
    """
    Build weekly accuracy trend data for the line chart.
    Returns the last N weeks of quiz activity.

    Algorithm:
        For each of the last N weeks:
            - Count quiz_submit events
            - Average the scores from metadata_json
        Returns list of {week_label, accuracy, sessions}

    We read scores from activity_logs metadata_json because
    it's already stored there during quiz submission — no need
    to re-query the results table.
    """
    trend = []
    now = datetime.now(timezone.utc)

    for i in range(weeks - 1, -1, -1):
        # Calculate week boundaries
        week_start = now - timedelta(weeks=i + 1)
        week_end = now - timedelta(weeks=i)

        # Fetch quiz_submit logs in this week window
        result = await db.execute(
            select(ActivityLog).where(
                and_(
                    ActivityLog.user_id == user_id,
                    ActivityLog.action_type == "quiz_submit",
                    ActivityLog.created_at >= week_start,
                    ActivityLog.created_at < week_end,
                )
            )
        )
        logs = result.scalars().all()

        # Extract scores from metadata_json
        scores = []
        for log in logs:
            score = log.metadata_json.get("score")
            if score is not None:
                scores.append(float(score))

        avg_accuracy = round(sum(scores) / len(scores), 1) if scores else 0.0

        # Human-readable week label
        week_label = week_start.strftime("%d %b").lstrip("0") if i > 0 else "This week"

        trend.append({
            "week_label": week_label,
            "accuracy": avg_accuracy,
            "sessions": len(logs),
        })

    return trend


async def get_activity_streak(
    db: AsyncSession,
    user_id: str,
) -> int:
    """
    Calculate the current consecutive-day activity streak.
    A day counts if the user completed at least one quiz or lesson.

    Returns the streak in days (0 if no activity today or yesterday).
    """
    streak = 0
    today = datetime.now(timezone.utc).date()

    for days_ago in range(30):  # check up to 30 days back
        check_date = today - timedelta(days=days_ago)
        day_start = datetime(check_date.year, check_date.month, check_date.day,
                             tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        result = await db.execute(
            select(func.count(ActivityLog.id)).where(
                and_(
                    ActivityLog.user_id == user_id,
                    ActivityLog.action_type.in_(["quiz_submit", "lesson_complete"]),
                    ActivityLog.created_at >= day_start,
                    ActivityLog.created_at < day_end,
                )
            )
        )
        count = result.scalar() or 0

        if count > 0:
            streak += 1
        else:
            break  # streak broken — stop counting

    return streak