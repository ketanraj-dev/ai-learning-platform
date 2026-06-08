import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { coursesApi } from "../services/api";
import { useAuthStore } from "../store/auth.store";
import { Navbar } from "../components/shared/Navbar";
import type { Course } from "../types/index";

const DIFFICULTY_LABEL = ["", "Beginner", "Intermediate", "Advanced"];
const SUBJECT_EMOJI: Record<string, string> = {
  Python: "🐍", "Machine Learning": "🤖", "Deep Learning": "🧠",
  NLP: "💬", Statistics: "📊",
};

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

  return (
    <div className="page">
      <Navbar />
      <div className="page-content">
        {/* Welcome header */}
        <div className="mb-8 animate-slide-up">
          <h1 className="text-2xl font-semibold text-slate-100">
            Welcome back, <span className="text-brand-400">{user?.name?.split(" ")[0]}</span> 👋
          </h1>
          <p className="text-slate-500 mt-1">Continue your Data Science &amp; AI/ML journey</p>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Courses", value: courses.length, icon: "📚" },
            { label: "Overall Progress", value: `${overallProgress}%`, icon: "📈" },
            { label: "Completed", value: courses.filter((c) => c.progress_pct === 100).length, icon: "✅" },
            { label: "In Progress", value: courses.filter((c) => c.progress_pct > 0 && c.progress_pct < 100).length, icon: "⚡" },
          ].map((s) => (
            <div key={s.label} className="card text-center animate-fade-in">
              <div className="text-2xl mb-1">{s.icon}</div>
              <div className="text-xl font-semibold text-slate-100">{s.value}</div>
              <div className="text-xs text-slate-500 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Courses grid */}
        <div className="section-title">Your Courses</div>

        {loading ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="card animate-pulse">
                <div className="h-4 bg-navy-700 rounded w-3/4 mb-3" />
                <div className="h-3 bg-navy-700 rounded w-full mb-2" />
                <div className="h-3 bg-navy-700 rounded w-2/3" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.map((course, i) => (
              <div
                key={course.id}
                className="card-hover animate-fade-in"
                style={{ animationDelay: `${i * 60}ms` }}
                onClick={() => navigate(`/course/${course.id}`)}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <span className="text-2xl">
                    {SUBJECT_EMOJI[course.subject] || "📖"}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium
                    ${course.difficulty === 1 ? "bg-green-500/10 text-green-400" :
                      course.difficulty === 2 ? "bg-yellow-500/10 text-yellow-400" :
                      "bg-red-500/10 text-red-400"}`}>
                    {DIFFICULTY_LABEL[course.difficulty]}
                  </span>
                </div>

                {/* Info */}
                <h3 className="font-semibold text-slate-100 mb-1 leading-snug">
                  {course.title}
                </h3>
                <p className="text-xs text-slate-500 mb-4 line-clamp-2">
                  {course.description}
                </p>

                {/* Progress */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>{course.completed_lessons}/{course.total_lessons} lessons</span>
                    <span className="text-brand-400 font-medium">{course.progress_pct}%</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${course.progress_pct}%` }} />
                  </div>
                </div>

                {/* Action */}
                <div className="mt-4 flex gap-2">
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
            ))}
          </div>
        )}
      </div>
    </div>
  );
}