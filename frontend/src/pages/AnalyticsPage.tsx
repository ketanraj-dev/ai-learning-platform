import { useEffect, useState } from "react";
import { analyticsApi } from "../services/api";
import { Navbar } from "../components/shared/Navbar";
import { TrendChart, TopicsBarChart, TopicsRadar } from "../components/analytics/Charts";
import type { AnalyticsDashboard, Recommendation } from "../types/index";

export function AnalyticsPage() {
  const [data, setData]           = useState<AnalyticsDashboard | null>(null);
  const [rec, setRec]             = useState<Recommendation | null>(null);
  const [loadingRec, setLoadingRec] = useState(false);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    analyticsApi.dashboard()
      .then((res) => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const loadRecommendation = async () => {
    setLoadingRec(true);
    try { const res = await analyticsApi.recommendations(); setRec(res.data); }
    catch (e) { console.error(e); }
    finally { setLoadingRec(false); }
  };

  if (loading) return (
    <div className="page">
      <Navbar />
      <div className="page-content">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse h-24">
              <div className="h-2.5 bg-navy-700 rounded w-1/2 mb-3" />
              <div className="h-6 bg-navy-700 rounded w-3/4" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
  if (!data) return null;

  const statItems = [
    { label: "Overall accuracy", value: `${data.overall_accuracy.toFixed(1)}%`, color: data.overall_accuracy >= 70 ? "#22C55E" : "#F59E0B" },
    { label: "Total sessions",   value: data.total_sessions,                    color: "#5B8AF0" },
    { label: "Day streak",       value: `${data.current_streak}d`,              color: "#E8843C" },
    { label: "Lessons done",     value: data.total_lessons_done,                color: "#22C55E" },
  ];

  return (
    <div className="page">
      <Navbar />
      <div className="page-content">

        {/* Page header */}
        <div className="mb-8 animate-slide-up">
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Learning analytics</h1>
          <p className="text-slate-500 text-sm">Your performance insights and progress over time</p>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          {statItems.map((s) => (
            <div key={s.label}
              className="bg-navy-800 border border-navy-700 rounded-2xl p-5 border-l-[3px] animate-fade-in"
              style={{ borderLeftColor: s.color }}>
              <p className="text-xs text-slate-500 mb-1">{s.label}</p>
              <p className="font-display text-2xl font-bold" style={{ color: s.color }}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Mastery summary */}
        <div className="flex gap-2 mb-6 flex-wrap">
          <span className="badge-easy">{data.topics_mastered} mastered</span>
          <span className="badge-hard">{data.topics_needs_work} need work</span>
          <span className="badge-info">{data.all_topics.length} total topics</span>
        </div>

        {/* Charts */}
        <div className="grid lg:grid-cols-2 gap-4 mb-4">
          <div className="card animate-fade-in">
            <p className="section-title">Weekly accuracy</p>
            {data.weekly_trend.length > 0 ? (
              <TrendChart data={data.weekly_trend} />
            ) : (
              <div className="h-48 flex items-center justify-center text-slate-500 text-sm">
                Take quizzes to see your trend
              </div>
            )}
          </div>
          <div className="card animate-fade-in">
            <p className="section-title">Topic coverage</p>
            {data.all_topics.length > 0 ? (
              <TopicsRadar data={data.all_topics} />
            ) : (
              <div className="h-48 flex items-center justify-center text-slate-500 text-sm">
                Complete quizzes to see coverage
              </div>
            )}
          </div>
        </div>

        {data.all_topics.length > 0 && (
          <div className="card mb-4 animate-fade-in">
            <p className="section-title">Accuracy by topic</p>
            <TopicsBarChart data={data.all_topics} />
          </div>
        )}

        {/* Strengths & Weaknesses */}
        <div className="grid sm:grid-cols-2 gap-4 mb-4">
          <div className="card animate-fade-in">
            <p className="section-title">Strongest topics</p>
            {data.strongest_topics.length > 0 ? (
              <div className="space-y-3">
                {data.strongest_topics.map((t) => (
                  <div key={t.topic_tag} className="flex items-center justify-between">
                    <span className="text-sm text-slate-300">{t.display_name}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1 bg-navy-700 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full transition-all duration-700"
                             style={{ width: `${t.accuracy_pct}%` }} />
                      </div>
                      <span className="text-xs text-emerald-400 font-medium w-9 text-right">
                        {t.accuracy_pct.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-slate-500">No data yet</p>}
          </div>

          <div className="card animate-fade-in">
            <p className="section-title">Needs improvement</p>
            {data.weakest_topics.length > 0 ? (
              <div className="space-y-3">
                {data.weakest_topics.map((t) => (
                  <div key={t.topic_tag} className="flex items-center justify-between">
                    <span className="text-sm text-slate-300">{t.display_name}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1 bg-navy-700 rounded-full overflow-hidden">
                        <div className="h-full bg-red-500 rounded-full transition-all duration-700"
                             style={{ width: `${t.accuracy_pct}%` }} />
                      </div>
                      <span className="text-xs text-red-400 font-medium w-9 text-right">
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
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="section-title mb-0.5">AI study recommendation</p>
              <p className="text-xs text-slate-500">Personalised based on your performance</p>
            </div>
            <button onClick={loadRecommendation} disabled={loadingRec}
              className="btn-secondary text-xs py-1.5">
              {loadingRec ? "Generating…" : rec ? "Refresh" : "Generate"}
            </button>
          </div>

          {rec ? (
            <div className="space-y-3">
              <p className="text-sm text-slate-300 leading-relaxed">{rec.recommendation_text}</p>
              {rec.focus_topics.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-3 border-t border-navy-700">
                  <span className="text-xs text-slate-500 self-center">Focus on:</span>
                  {rec.focus_topics.map((t) => (
                    <span key={t} className="badge-info">{t.replace(/_/g, " ")}</span>
                  ))}
                </div>
              )}
              <p className="text-xs text-slate-500">
                Suggested next difficulty:{" "}
                <span className="text-brand-400 font-medium">{rec.suggested_difficulty}</span>
              </p>
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              Generate a personalised AI study plan based on your quiz history.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
