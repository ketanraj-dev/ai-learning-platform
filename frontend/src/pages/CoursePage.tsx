import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { coursesApi } from "../services/api";
import { Navbar } from "../components/shared/Navbar";
import { AIChatPanel } from "../components/learning/AIChatPanel";
import type { Course, Lesson } from "../types/index";

export function CoursePage() {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();
  const [course, setCourse]           = useState<Course | null>(null);
  const [lessons, setLessons]         = useState<Lesson[]>([]);
  const [activeLesson, setActiveLesson] = useState<Lesson | null>(null);
  const [showChat, setShowChat]       = useState(false);
  const [completing, setCompleting]   = useState(false);

  useEffect(() => {
    if (!courseId) return;
    Promise.all([coursesApi.get(courseId), coursesApi.lessons(courseId)])
      .then(([courseRes, lessonsRes]) => {
        setCourse(courseRes.data);
        const lessonList: Lesson[] = lessonsRes.data.lessons;
        setLessons(lessonList);
        const first = lessonList.find((l) => !l.completed) || lessonList[0];
        setActiveLesson(first || null);
      }).catch(console.error);
  }, [courseId]);

  const handleComplete = async () => {
    if (!activeLesson || !courseId || completing) return;
    setCompleting(true);
    try {
      await coursesApi.completeLesson(courseId, activeLesson.id);
      setLessons((prev) =>
        prev.map((l) => l.id === activeLesson.id ? { ...l, completed: true } : l)
      );
      setActiveLesson((prev) => prev ? { ...prev, completed: true } : prev);
      const idx = lessons.findIndex((l) => l.id === activeLesson.id);
      if (idx < lessons.length - 1) setTimeout(() => setActiveLesson(lessons[idx + 1]), 400);
    } catch (e) { console.error(e); }
    finally { setCompleting(false); }
  };

  const renderContent = (content: string) =>
    content.split("\n").map((line, i) => {
      if (line.startsWith("## ")) return <h2 key={i} className="text-lg font-semibold text-slate-100 mt-8 mb-3">{line.slice(3)}</h2>;
      if (line.startsWith("# "))  return <h1 key={i} className="text-xl font-bold text-slate-100 mt-8 mb-4">{line.slice(2)}</h1>;
      if (line.startsWith("```")) return null;
      if (line.startsWith("- ") || line.startsWith("* "))
        return <li key={i} className="text-slate-300 text-sm ml-5 list-disc leading-relaxed">{line.slice(2)}</li>;
      if (line.startsWith("**") && line.endsWith("**"))
        return <p key={i} className="font-semibold text-slate-200 text-sm my-1">{line.slice(2, -2)}</p>;
      if (line.trim() === "") return <div key={i} className="h-3" />;
      if (line.includes("```"))
        return <code key={i} className="font-mono text-sm bg-navy-950 text-brand-400 px-2 py-0.5 rounded">{line.replace(/`/g, "")}</code>;
      return <p key={i} className="text-slate-300 text-sm leading-[1.75]">{line}</p>;
    });

  return (
    <div className="page">
      <Navbar />
      <div className="flex" style={{ height: "calc(100vh - 60px)" }}>

        {/* ── Sidebar ── */}
        <aside className="w-60 bg-navy-950 border-r border-navy-700 flex flex-col overflow-hidden hidden lg:flex">
          <div className="p-4 border-b border-navy-700">
            <button onClick={() => navigate("/dashboard")}
              className="text-xs text-slate-500 hover:text-slate-300 mb-3 flex items-center gap-1 transition-colors">
              <span>←</span> Dashboard
            </button>
            <h2 className="font-semibold text-slate-100 text-sm leading-snug mb-3">
              {course?.title}
            </h2>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${course?.progress_pct || 0}%` }} />
            </div>
            <p className="text-xs text-slate-500 mt-1.5">{course?.progress_pct || 0}% complete</p>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            {lessons.map((lesson) => {
              const isActive = activeLesson?.id === lesson.id;
              return (
                <button key={lesson.id}
                  onClick={() => setActiveLesson(lesson)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-xs mb-0.5
                              transition-all flex items-start gap-2.5
                    ${isActive
                      ? "bg-brand-500/10 border border-brand-500/20 text-brand-400"
                      : "text-slate-400 hover:bg-navy-800 hover:text-slate-200 border border-transparent"
                    }`}>
                  <span className="flex-shrink-0 mt-[1px] text-[10px]">
                    {lesson.completed ? (
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <circle cx="6" cy="6" r="5" fill="#22C55E" fillOpacity="0.2" stroke="#22C55E" strokeWidth="1.5"/>
                        <path d="M3.5 6l1.8 1.8L8.5 4.5" stroke="#22C55E" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    ) : isActive ? (
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <circle cx="6" cy="6" r="5" stroke="#E8843C" strokeWidth="1.5"/>
                        <circle cx="6" cy="6" r="2.5" fill="#E8843C"/>
                      </svg>
                    ) : (
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <circle cx="6" cy="6" r="5" stroke="#2A3D57" strokeWidth="1.5"/>
                      </svg>
                    )}
                  </span>
                  <span className="leading-snug">{lesson.title}</span>
                </button>
              );
            })}
          </div>

          <div className="p-3 border-t border-navy-700">
            <button onClick={() => navigate(`/quiz/${courseId}`)} className="btn-primary w-full text-xs py-2">
              Take quiz
            </button>
          </div>
        </aside>

        {/* ── Main content ── */}
        <main className="flex-1 overflow-y-auto bg-navy-900">
          {activeLesson ? (
            <div className="max-w-2xl mx-auto px-6 py-8">
              {/* Lesson header */}
              <div className="flex items-start justify-between mb-8">
                <div>
                  <div className="flex items-center gap-2.5 mb-2">
                    <span className="text-xs text-slate-500 font-mono">
                      {String(activeLesson.order_index).padStart(2, "0")}
                    </span>
                    {activeLesson.completed && (
                      <span className="badge-easy">Completed</span>
                    )}
                  </div>
                  <h1 className="text-2xl font-bold text-slate-100">{activeLesson.title}</h1>
                </div>
                <button
                  onClick={() => setShowChat(!showChat)}
                  className={`btn-ghost text-sm flex-shrink-0 ml-4
                    ${showChat ? "text-brand-400 bg-brand-500/10" : ""}`}>
                  {showChat ? "Hide AI" : "Ask AI"}
                </button>
              </div>

              <div className={`grid gap-8 ${showChat ? "lg:grid-cols-2" : ""}`}>
                <div className="space-y-1.5">{renderContent(activeLesson.content)}</div>
                {showChat && (
                  <div className="h-[520px] sticky top-4">
                    <AIChatPanel />
                  </div>
                )}
              </div>

              {!activeLesson.completed && (
                <div className="mt-10 pt-6 border-t border-navy-700">
                  <button onClick={handleComplete} disabled={completing} className="btn-primary">
                    {completing ? "Saving…" : "Mark as complete"}
                  </button>
                </div>
              )}

              <div className="flex justify-between mt-8 pt-4">
                {lessons.findIndex((l) => l.id === activeLesson.id) > 0 && (
                  <button onClick={() => {
                    const idx = lessons.findIndex((l) => l.id === activeLesson.id);
                    setActiveLesson(lessons[idx - 1]);
                  }} className="btn-secondary text-sm">← Previous</button>
                )}
                {lessons.findIndex((l) => l.id === activeLesson.id) < lessons.length - 1 && (
                  <button onClick={() => {
                    const idx = lessons.findIndex((l) => l.id === activeLesson.id);
                    setActiveLesson(lessons[idx + 1]);
                  }} className="btn-secondary text-sm ml-auto">Next →</button>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500 text-sm">
              Select a lesson from the sidebar
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
