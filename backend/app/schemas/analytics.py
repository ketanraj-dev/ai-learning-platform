"""
app/schemas/analytics.py
-------------------------
Response shapes for the analytics dashboard.

These schemas mirror what the frontend charts expect:
  - TrendPoint      → Recharts LineChart data
  - TopicStat       → Recharts BarChart / RadarChart data
  - AnalyticsDashboard → the full dashboard page payload
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Topic-level stats ──────────────────────────────────────────────────────

class TopicStat(BaseModel):
    """
    Performance stats for one topic.
    Used in both bar charts and the strength/weakness lists.

    Example:
        topic_tag    = "numpy"
        display_name = "NumPy"
        accuracy_pct = 85.0
        sessions     = 4
        difficulty   = "medium"
        trend        = "improving"
    """
    topic_tag: str
    display_name: str                   # human-readable label for the chart
    accuracy_pct: float = Field(..., ge=0.0, le=100.0)
    sessions_count: int
    difficulty_level: str               # current adaptive difficulty
    last_score: float
    trend: str = "stable"               # "improving" | "declining" | "stable"

    model_config = {"from_attributes": True}


# ── Trend data ─────────────────────────────────────────────────────────────

class TrendPoint(BaseModel):
    """
    One data point on the weekly trend line chart.

    week_label: human readable — "Week 1", "May 27", etc.
    accuracy:   average score across all quizzes that week
    sessions:   number of quiz attempts that week
    """
    week_label: str
    accuracy: float
    sessions: int


# ── AI recommendation ──────────────────────────────────────────────────────

class RecommendationOut(BaseModel):
    """
    AI-generated study plan returned from GET /analytics/me/recommendations.

    recommendation_text: full paragraph from GPT
    focus_topics: list of topic_tags to prioritize (for frontend highlighting)
    suggested_difficulty: what difficulty to use next
    """
    recommendation_text: str
    focus_topics: list[str]
    suggested_difficulty: str
    generated_at: datetime


# ── Full dashboard payload ─────────────────────────────────────────────────

class AnalyticsDashboard(BaseModel):
    """
    Everything the analytics page needs in one response.
    Returned from GET /analytics/me

    Design decision: one fat response instead of 4 separate calls.
    Dashboard loads in one request — better perceived performance.

    Fields:
        overall_accuracy  — weighted average across all topics
        total_sessions    — total quizzes taken
        strongest_topics  — top 3 topics by accuracy (for green highlights)
        weakest_topics    — bottom 3 topics by accuracy (for red highlights)
        all_topics        — full list for the bar chart
        weekly_trend      — last 6 weeks of data for line chart
        current_streak    — consecutive days with at least one session
        total_lessons_done — lessons completed count
    """
    overall_accuracy: float = Field(..., ge=0.0, le=100.0)
    total_sessions: int
    total_lessons_done: int
    current_streak: int                 # days in a row with activity

    strongest_topics: list[TopicStat]   # top 3 — shown as strengths
    weakest_topics: list[TopicStat]     # bottom 3 — shown as areas to improve
    all_topics: list[TopicStat]         # all topics for the full bar chart

    weekly_trend: list[TrendPoint]      # last 6 weeks for line chart

    # Adaptive summary
    topics_mastered: int                # topics with accuracy >= 80%
    topics_needs_work: int              # topics with accuracy < 50%


# ── Chat schemas ───────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """One message in the AI chat history."""
    role: str           # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    """
    Body for POST /ai/chat
    history contains the last N messages for context window.
    """
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=10)
    # max 10 history items = last 5 exchanges = keeps token cost low


class TranscribeResponse(BaseModel):
    """Returned from POST /ai/transcribe"""
    text: str               # the transcribed text from Whisper
    language: Optional[str] = None