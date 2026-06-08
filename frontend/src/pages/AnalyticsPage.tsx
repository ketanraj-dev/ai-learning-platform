import { useEffect, useState } from "react";
import { analyticsApi } from "../services/api";
import { Navbar } from "../components/shared/Navbar";
import { TrendChart, TopicsBarChart, TopicsRadar } from "../components/analytics/Charts";
import type { AnalyticsDashboard, Recommendation } from "../types/index";

export function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsDashboard | null>(null);
  const [rec, setRec] = useState<Recommendation | null>(null);
  const [loadingRec, setLoadingRec] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsApi.dashboard()
      .then((res) => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const loadRecommendation = async () => {
    setLoadingRec(true);
    try {
      const res = await analyticsApi.recommendations();
      setRec(res.data);
    } catch (e) { console.error(e); }
    finally { setLoadingRec(false); }
  };

  if (loading) return (
    <div className="page">
      <Navbar />
      <div className="page-content">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse h-24">
              <div className="h-3 bg-navy-700 rounded w-1/2 mb-3" />
              <div className="h-6 bg-navy-700 rounded w-3/4" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  if (!data) return null;

  return (
    <div className="page">
      <Navbar />
      <div className="page-content">
        <div className="mb-6 animate-slide-up">
          <h1 className="text-2xl font-semibold text-slate-100">Learning Analytics</h1>
          <p className="text-slate-500 text-sm mt-1">Your performance insights and progress</p>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {[
            { label: "Overall Accuracy", value: `${data.overall_accuracy.toFixed(1)}%`, icon: "🎯", color: data.overall_accuracy >= 70 ? "text-green-400" : "text-yellow-400" },
            { label: "Total Sessions", value: data.total_sessions, icon: "📝", color: "text-brand-400" },
            { label: "Current Streak", value: `${data.current_streak}d`, icon: "🔥", color: "text-orange-400" },
            { label: "Lessons Done", value: data.total_lessons_done, icon: "✅", color: "text-green-400" },
          ].map((s) => (
            <div key={s.label} className="card animate-fade-in">
              <p className="text-xs text-slate-500 mb-1">{s.icon} {s.label}</p>
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Mastery pills */}
        <div className="flex gap-3 mb-6 flex-wrap">
          <div className="badge-easy">{data.topics_mastered} topics mastered</div>
          <div className="badge-hard">{data.topics_needs_work} need work</div>
          <div className="badge-info">{data.all_topics.length} total topics</div>
        </div>

        {/* Charts row */}
        <div className="grid lg:grid-cols-2 gap-4 mb-6">
          <div className="card animate-fade-in">
            <p className="section-title">Weekly Accuracy Trend</p>
            {data.weekly_trend.length > 0 ? (
              <TrendChart data={data.weekly_trend} />
            ) : (
              <div className="h-48 flex items-center justify-center text-slate-500 text-sm">
                Take quizzes to see your trend
              </div>
            )}
          </div>
          <div className="card animate-fade-in">
            <p className="section-title">Topic Coverage</p>
            {data.all_topics.length > 0 ? (
              <TopicsRadar data={data.all_topics} />
            ) : (
              <div className="h-48 flex items-center justify-center text-slate-500 text-sm">
                Complete quizzes to see coverage
              </div>
            )}
          </div>
        </div>

        {/* Full bar chart */}
        {data.all_topics.length > 0 && (
          <div className="card mb-6 animate-fade-in">
            <p className="section-title">Accuracy by Topic</p>
            <TopicsBarChart data={data.all_topics} />
          </div>
        )}

        {/* Strengths & Weaknesses */}
        <div className="grid sm:grid-cols-2 gap-4 mb-6">
          <div className="card animate-fade-in">
            <p className="section-title">💪 Strongest Topics</p>
            {data.strongest_topics.length > 0 ? (
              <div className="space-y-2">
                {data.strongest_topics.map((t) => (
                  <div key={t.topic_tag} className="flex items-center justify-between">
                    <span className="text-sm text-slate-300">{t.display_name}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 progress-bar">
                        <div className="progress-fill bg-green-500" style={{ width: `${t.accuracy_pct}%` }} />
                      </div>
                      <span className="text-xs text-green-400 font-medium w-10 text-right">
                        {t.accuracy_pct.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-slate-500">No data yet</p>}
          </div>
          <div className="card animate-fade-in">
            <p className="section-title">📈 Needs Improvement</p>
            {data.weakest_topics.length > 0 ? (
              <div className="space-y-2">
                {data.weakest_topics.map((t) => (
                  <div key={t.topic_tag} className="flex items-center justify-between">
                    <span className="text-sm text-slate-300">{t.display_name}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 progress-bar">
                        <div className="progress-fill bg-red-500" style={{ width: `${t.accuracy_pct}%` }} />
                      </div>
                      <span className="text-xs text-red-400 font-medium w-10 text-right">
                        {t.accuracy_pct.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-slate-500">No data yet</p>}
          </div>
        </div>

        {/* AI Recommendation */}
        <div className="card animate-fade-in">
          <div className="flex items-center justify-between mb-3">
            <p className="section-title mb-0">🤖 AI Study Recommendation</p>
            <button onClick={loadRecommendation} disabled={loadingRec} className="btn-secondary text-xs py-1.5">
              {loadingRec ? "Generating..." : rec ? "Refresh" : "Generate"}
            </button>
          </div>
          {rec ? (
            <div className="space-y-3">
              <p className="text-sm text-slate-300 leading-relaxed">{rec.recommendation_text}</p>
              {rec.focus_topics.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-2 border-t border-navy-700">
                  <span className="text-xs text-slate-500">Focus on:</span>
                  {rec.focus_topics.map((t) => (
                    <span key={t} className="badge-info">{t.replace(/_/g, " ")}</span>
                  ))}
                </div>
              )}
              <p className="text-xs text-slate-500">Suggested next difficulty: <span className="text-brand-400">{rec.suggested_difficulty}</span></p>
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              Click "Generate" to get a personalised AI study plan based on your performance.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}