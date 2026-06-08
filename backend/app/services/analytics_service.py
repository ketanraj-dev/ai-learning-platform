"""
app/services/analytics_service.py
-----------------------------------
Aggregates raw analytics data into dashboard-ready objects.
Calls analytics_repo for data and ai_service for recommendations.
"""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories import analytics_repo, assessment_repo, course_repo
from app.schemas.analytics import (
    AnalyticsDashboard,
    RecommendationOut,
    TopicStat,
    TrendPoint,
)
from app.services import ai_service

logger = get_logger(__name__)

# Topic tag → human readable display name mapping
TOPIC_DISPLAY_NAMES = {
    "numpy": "NumPy",
    "pandas": "Pandas",
    "matplotlib": "Data Visualization",
    "statistics": "Statistics",
    "linear_regression": "Linear Regression",
    "classification": "Classification",
    "clustering": "Clustering",
    "neural_networks": "Neural Networks",
    "deep_learning": "Deep Learning",
    "nlp": "Natural Language Processing",
    "feature_engineering": "Feature Engineering",
    "model_evaluation": "Model Evaluation",
    "python_basics": "Python Basics",
    "data_cleaning": "Data Cleaning",
    "dimensionality_reduction": "Dimensionality Reduction",
}


async def get_dashboard(
    db: AsyncSession,
    user_id: str,
) -> AnalyticsDashboard:
    """
    Build the complete analytics dashboard payload.

    Aggregates:
        - Topic-level accuracy stats
        - Strongest / weakest 3 topics
        - Overall accuracy (weighted by session count)
        - Weekly trend (last 6 weeks)
        - Streak and lesson completion counts
        - Mastered vs needs-work counts

    Returns a single AnalyticsDashboard object that the
    frontend renders without needing additional API calls.
    """
    # Fetch raw analytics rows
    raw_analytics = await analytics_repo.get_analytics_for_user(db, user_id)
    total_lessons = await course_repo.get_total_completed_lessons(db, user_id)
    total_sessions = await assessment_repo.get_results_count_for_user(db, user_id)
    streak = await analytics_repo.get_activity_streak(db, user_id)
    weekly_trend_raw = await analytics_repo.get_weekly_trend(db, user_id, weeks=6)

    # Convert raw analytics to TopicStat schemas
    topic_stats: list[TopicStat] = []
    for row in raw_analytics:
        display_name = TOPIC_DISPLAY_NAMES.get(row.topic_tag, row.topic_tag.replace("_", " ").title())
        trend = _calculate_trend(row.last_score, row.accuracy_pct)
        topic_stats.append(
            TopicStat(
                topic_tag=row.topic_tag,
                display_name=display_name,
                accuracy_pct=row.accuracy_pct,
                sessions_count=row.sessions_count,
                difficulty_level=row.difficulty_level,
                last_score=row.last_score,
                trend=trend,
            )
        )

    # Sort by accuracy
    topic_stats.sort(key=lambda t: t.accuracy_pct)

    # Overall accuracy — weighted average by session count
    overall_accuracy = _compute_overall_accuracy(topic_stats)

    # Strongest = top 3, weakest = bottom 3
    weakest = topic_stats[:3] if len(topic_stats) >= 3 else topic_stats
    strongest = sorted(topic_stats, key=lambda t: t.accuracy_pct, reverse=True)[:3]

    # Mastery counts
    topics_mastered = sum(1 for t in topic_stats if t.accuracy_pct >= 80)
    topics_needs_work = sum(1 for t in topic_stats if t.accuracy_pct < 50)

    # Build weekly trend
    weekly_trend = [
        TrendPoint(
            week_label=w["week_label"],
            accuracy=w["accuracy"],
            sessions=w["sessions"],
        )
        for w in weekly_trend_raw
    ]

    logger.info(
        "Dashboard built for user=%s topics=%d overall=%.1f%%",
        user_id, len(topic_stats), overall_accuracy,
    )

    return AnalyticsDashboard(
        overall_accuracy=overall_accuracy,
        total_sessions=total_sessions,
        total_lessons_done=total_lessons,
        current_streak=streak,
        strongest_topics=strongest,
        weakest_topics=weakest,
        all_topics=topic_stats,
        weekly_trend=weekly_trend,
        topics_mastered=topics_mastered,
        topics_needs_work=topics_needs_work,
    )


async def get_recommendations(
    db: AsyncSession,
    user_id: str,
) -> RecommendationOut:
    """
    Generate AI-powered study recommendations based on analytics.

    Fetches the user's weak and strong topics, then asks GPT
    to write a personalised improvement plan.

    Returns RecommendationOut with text + focus topics + difficulty.
    """
    raw_analytics = await analytics_repo.get_analytics_for_user(db, user_id)

    if not raw_analytics:
        # No data yet — return a generic welcome recommendation
        return RecommendationOut(
            recommendation_text=(
                "Welcome to the AI Learning Platform! Start by taking a quiz "
                "on any course to get personalised recommendations. "
                "Begin with Python Basics or Statistics if you're new to Data Science."
            ),
            focus_topics=[],
            suggested_difficulty="easy",
            generated_at=datetime.now(timezone.utc),
        )

    # Build TopicStat list for the AI prompt
    topic_stats = [
        TopicStat(
            topic_tag=row.topic_tag,
            display_name=TOPIC_DISPLAY_NAMES.get(
                row.topic_tag, row.topic_tag.replace("_", " ").title()
            ),
            accuracy_pct=row.accuracy_pct,
            sessions_count=row.sessions_count,
            difficulty_level=row.difficulty_level,
            last_score=row.last_score,
            trend="stable",
        )
        for row in raw_analytics
    ]

    overall = _compute_overall_accuracy(topic_stats)
    sorted_stats = sorted(topic_stats, key=lambda t: t.accuracy_pct)
    weakest = sorted_stats[:3]
    strongest = sorted(topic_stats, key=lambda t: t.accuracy_pct, reverse=True)[:3]

    # Call GPT for recommendation
    rec_data = await ai_service.get_ai_recommendations(
        weak_topics=weakest,
        strong_topics=strongest,
        overall_accuracy=overall,
    )

    return RecommendationOut(
        recommendation_text=rec_data["recommendation_text"],
        focus_topics=rec_data["focus_topics"],
        suggested_difficulty=rec_data["suggested_difficulty"],
        generated_at=datetime.now(timezone.utc),
    )


# ── Private helpers ────────────────────────────────────────────────────────

def _compute_overall_accuracy(topic_stats: list[TopicStat]) -> float:
    """
    Weighted average accuracy across all topics.
    Topics with more sessions contribute more to the average.
    """
    if not topic_stats:
        return 0.0

    total_weight = sum(t.sessions_count for t in topic_stats)
    if total_weight == 0:
        return 0.0

    weighted_sum = sum(t.accuracy_pct * t.sessions_count for t in topic_stats)
    return round(weighted_sum / total_weight, 1)


def _calculate_trend(last_score: float, running_average: float) -> str:
    """
    Determine if user is improving, declining, or stable on this topic.
    Compares last score to running average.
    """
    diff = last_score - running_average
    if diff >= 10:
        return "improving"
    elif diff <= -10:
        return "declining"
    else:
        return "stable"