"""
app/api/v1/analytics.py
------------------------
Analytics dashboard router — all read-only, all protected.
"""

from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.schemas.analytics import AnalyticsDashboard, RecommendationOut, TrendPoint
from app.services import analytics_service
from app.repositories import analytics_repo

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/me", response_model=AnalyticsDashboard)
async def get_my_analytics(current_user: CurrentUser, db: DB):
    """
    Get the complete analytics dashboard for the current user.

    Returns everything the dashboard page needs in one call:
        - overall_accuracy: weighted average across all topics
        - strongest_topics: top 3 by accuracy (shown as green cards)
        - weakest_topics:   bottom 3 (shown as red cards / improvement targets)
        - all_topics:       full list for the bar chart
        - weekly_trend:     last 6 weeks for the line chart
        - current_streak:   consecutive active days
        - total_sessions:   total quizzes taken
        - total_lessons_done
        - topics_mastered / topics_needs_work counts
    """
    return await analytics_service.get_dashboard(db, current_user.id)


@router.get("/me/trend", response_model=list[TrendPoint])
async def get_my_trend(
    current_user: CurrentUser,
    db: DB,
):
    """
    Get weekly accuracy trend for the last 6 weeks.
    Returns [{week_label, accuracy, sessions}] for the line chart.
    """
    raw = await analytics_repo.get_weekly_trend(db, current_user.id, weeks=6)
    return [TrendPoint(**w) for w in raw]


@router.get("/me/recommendations", response_model=RecommendationOut)
async def get_my_recommendations(current_user: CurrentUser, db: DB):
    """
    Get AI-generated personalised study recommendations.

    Analyses weak topics and generates a specific improvement plan.
    Calls GPT-4o-mini — takes 2-4 seconds.

    Cached recommendation is not implemented (academic project scope) —
    each call generates a fresh recommendation.
    """
    return await analytics_service.get_recommendations(db, current_user.id)