import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { coursesApi } from "../services/api";
import { useAuthStore } from "../store/auth.store";
import { Navbar } from "../components/shared/Navbar";
import type { Course } from "../types/index";

const DIFFICULTY_LABEL = ["", "Beginner", "Intermediate", "Advanced"];

// Subject colors drawn from the fields' own visual identities
const SUBJECT_COLOR: Record<string, string> = {
  "Python":           "#3B82F6",
  "Machine Learning": "#8B5CF6",
  "Deep Learning":    "#EC4899",
  "NLP":              "#10B981",
  "Statistics":       "#F59E0B",
};

const STAT_ACCENT = ["#5B8AF0", "#E8843C", "#22C55E", "#F59E0B"];

export function DashboardPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    coursesApi.list()
      .then((res) => setCourses(res.data.courses))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const overallProgress = courses.length
    ? Math.round(courses.reduce((s, c) => s + c.progress_pct, 0) / courses.length)
    : 0;

  const stats = [
    { label: "Courses",     value: courses.length },
    { label: "Progress",    value: `${overallProgress}%` },
    { label: "Completed",   value: courses.filter((c) => c.progress_pct === 100).length },
    { label: "In progress", value: courses.filter((c) => c.progress_pct > 0 && c.progress_pct < 100).length },
  ];

  return (
    <div className="page">
      <Navbar />
      <div className="page-content">

        {/* Welcome banner */}
        <div className="mb-8 animate-slide-up rounded-2xl bg-navy-800 border border-navy-700
                        p-6 sm:p-8 relative overflow-hidden">
          <div className="absolute right-0 top-0 w-72 h-72 bg-brand-500/5 rounded-full
                          blur-3xl pointer-events-none" />
          <div className="relative">
            <p className="text-xs font-semibold text-brand-400 uppercase tracking-widest mb-2"
               style={{ fontFamily: "Space Grotesk, sans-serif" }}>
              Welcome back
            </p>
            <h1 className="text-3xl font-bold text-slate-100 mb-1">
              {user?.name?.split(" ")[0]}
            </h1>
            <p className="text-slate-500 text-sm">
              Data Science &amp; AI&thinsp;/&thinsp;ML · Your learning journey continues
            </p>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          {stats.map((s, i) => (
            <div key={s.label} className="bg-navy-800 border border-navy-700 rounded-2xl p-5
                                          border-l-[3px] animate-fade-in"
              style={{ borderLeftColor: STAT_ACCENT[i] }}>
              <div className="text-2xl font-bold text-slate-100 mb-0.5"
                   style={{ fontFamily: "Space Grotesk, sans-serif" }}>
                {s.value}
              </div>
              <div className="text-xs text-slate-500">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Courses section */}
        <p className="section-title">Your courses</p>

        {loading ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="card animate-pulse">
                <div className="h-3 bg-navy-700 rounded w-3/4 mb-4" />
                <div className="h-2.5 bg-navy-700 rounded w-full mb-2" />
                <div className="h-2.5 bg-navy-700 rounded w-2/3" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.map((course, i) => {
              const accentColor = SUBJECT_COLOR[course.subject] || "#5B8AF0";
              return (
                <div
                  key={course.id}
                  onClick={() => navigate(`/course/${course.id}`)}
                  className="relative group bg-navy-800 border border-navy-700 hover:border-navy-600
                             hover:bg-[#1A2840] rounded-2xl p-5 cursor-pointer transition-all
                             duration-200 animate-fade-in overflow-hidden"
                  style={{ animationDelay: `${i * 55}ms` }}
                >
                  {/* Subject color strip */}
                  <div className="absolute left-0 inset-y-0 w-[3px] rounded-l-2xl"
                       style={{ backgroundColor: accentColor }} />

                  {/* Header row */}
                  <div className="flex items-center justify-between mb-3 pl-2">
                    <span className="text-[10px] font-semibold uppercase tracking-wider"
                          style={{ color: accentColor, fontFamily: "Space Grotesk, sans-serif" }}>
                      {course.subject}
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium
                      ${course.difficulty === 1
                        ? "bg-emerald-500/10 text-emerald-400"
                        : course.difficulty === 2
                        ? "bg-amber-500/10 text-amber-400"
                        : "bg-red-500/10 text-red-400"}`}>
                      {DIFFICULTY_LABEL[course.difficulty]}
                    </span>
                  </div>

                  {/* Title + description */}
                  <h3 className="font-semibold text-slate-100 mb-1 leading-snug pl-2">
                    {course.title}
                  </h3>
                  <p className="text-xs text-slate-500 mb-4 line-clamp-2 leading-relaxed pl-2">
                    {course.description}
                  </p>

                  {/* Progress */}
                  <div className="pl-2 space-y-1.5">
                    <div className="flex justify-between text-xs text-slate-500">
                      <span>{course.completed_lessons}/{course.total_lessons} lessons</span>
                      <span className="font-medium" style={{ color: accentColor }}>
                        {course.progress_pct}%
                      </span>
                    </div>
                    <div className="h-1 bg-navy-700 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-700"
                           style={{ width: `${course.progress_pct}%`, backgroundColor: accentColor }} />
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="mt-4 flex gap-2 pl-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); navigate(`/course/${course.id}`); }}
                      className="btn-secondary text-xs py-1.5 flex-1"
                    >
                      {course.progress_pct === 0 ? "Start" : course.progress_pct === 100 ? "Review" : "Continue"}
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); navigate(`/quiz/${course.id}`); }}
                      className="btn-ghost text-xs py-1.5 px-3"
                    >
                      Quiz
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
