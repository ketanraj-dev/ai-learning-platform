import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { coursesApi } from "../services/api";
import { Navbar } from "../components/shared/Navbar";
import { AIChatPanel } from "../components/learning/AIChatPanel";
import type { Course, Lesson } from "../types/index";

export function CoursePage() {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();
  const [course, setCourse] = useState<Course | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [activeLesson, setActiveLesson] = useState<Lesson | null>(null);
  const [showChat, setShowChat] = useState(false);
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    if (!courseId) return;
    Promise.all([
      coursesApi.get(courseId),
      coursesApi.lessons(courseId),
    ]).then(([courseRes, lessonsRes]) => {
      setCourse(courseRes.data);
      const lessonList: Lesson[] = lessonsRes.data.lessons;
      setLessons(lessonList);
      // Auto-select first incomplete lesson
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
      // Auto-advance to next lesson
      const idx = lessons.findIndex((l) => l.id === activeLesson.id);
      if (idx < lessons.length - 1) {
        setTimeout(() => setActiveLesson(lessons[idx + 1]), 400);
      }
    } catch (e) { console.error(e); }
    finally { setCompleting(false); }
  };

  // Render markdown-like content
  const renderContent = (content: string) => {
    return content.split("\n").map((line, i) => {
      if (line.startsWith("## ")) return <h2 key={i} className="text-lg font-semibold text-slate-100 mt-6 mb-2">{line.slice(3)}</h2>;
      if (line.startsWith("# ")) return <h1 key={i} className="text-xl font-semibold text-slate-100 mt-6 mb-3">{line.slice(2)}</h1>;
      if (line.startsWith("```")) return null;
      if (line.startsWith("- ") || line.startsWith("* ")) return <li key={i} className="text-slate-300 text-sm ml-4 list-disc">{line.slice(2)}</li>;
      if (line.startsWith("**") && line.endsWith("**")) return <p key={i} className="font-semibold text-slate-200 text-sm my-1">{line.slice(2, -2)}</p>;
      if (line.trim() === "") return <div key={i} className="h-2" />;
      if (line.includes("```")) return <code key={i} className="font-mono text-sm bg-navy-900 text-brand-300 px-2 py-0.5 rounded">{line.replace(/`/g, "")}</code>;
      return <p key={i} className="text-slate-300 text-sm leading-relaxed">{line}</p>;
    });
  };

  return (
    <div className="page">
      <Navbar />
      <div className="flex h-[calc(100vh-64px)]">
        {/* Sidebar */}
        <aside className="w-64 bg-navy-900 border-r border-navy-800 flex flex-col overflow-hidden hidden lg:flex">
          <div className="p-4 border-b border-navy-800">
            <button onClick={() => navigate("/dashboard")} className="text-xs text-slate-500 hover:text-slate-300 mb-2 block">
              ← Dashboard
            </button>
            <h2 className="font-semibold text-slate-100 text-sm leading-snug">
              {course?.title}
            </h2>
            <div className="mt-2 progress-bar">
              <div className="progress-fill" style={{ width: `${course?.progress_pct || 0}%` }} />
            </div>
            <p className="text-xs text-slate-500 mt-1">{course?.progress_pct || 0}% complete</p>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {lessons.map((lesson) => (
              <button key={lesson.id}
                onClick={() => setActiveLesson(lesson)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-xs mb-1 transition-all flex items-start gap-2
                  ${activeLesson?.id === lesson.id
                    ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
                    : "text-slate-400 hover:bg-navy-800 hover:text-slate-200"
                  }`}>
                <span className="flex-shrink-0 mt-0.5">
                  {lesson.completed ? "✅" : activeLesson?.id === lesson.id ? "▶" : "○"}
                </span>
                <span className="leading-snug">{lesson.title}</span>
              </button>
            ))}
          </div>
          <div className="p-3 border-t border-navy-800">
            <button onClick={() => navigate(`/quiz/${courseId}`)} className="btn-primary w-full text-xs py-2">
              Take Quiz
            </button>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto">
          {activeLesson ? (
            <div className="max-w-3xl mx-auto px-6 py-8">
              {/* Lesson header */}
              <div className="flex items-start justify-between mb-6">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs text-slate-500">Lesson {activeLesson.order_index}</span>
                    {activeLesson.completed && <span className="badge-easy">Completed</span>}
                  </div>
                  <h1 className="text-2xl font-semibold text-slate-100">{activeLesson.title}</h1>
                </div>
                <button onClick={() => setShowChat(!showChat)}
                  className={`btn-ghost text-sm flex-shrink-0 ${showChat ? "text-brand-400" : ""}`}>
                  🤖 {showChat ? "Hide AI" : "Ask AI"}
                </button>
              </div>

              {/* Two-column layout when chat is open */}
              <div className={`grid gap-6 ${showChat ? "lg:grid-cols-2" : ""}`}>
                {/* Lesson content */}
                <div className="space-y-1">
                  {renderContent(activeLesson.content)}
                </div>
                {/* AI Chat */}
                {showChat && (
                  <div className="h-[500px] sticky top-4">
                    <AIChatPanel />
                  </div>
                )}
              </div>

              {/* Complete button */}
              {!activeLesson.completed && (
                <div className="mt-8 pt-6 border-t border-navy-800">
                  <button onClick={handleComplete} disabled={completing} className="btn-primary">
                    {completing ? "Saving..." : "✓ Mark as Complete"}
                  </button>
                </div>
              )}

              {/* Navigation */}
              <div className="flex justify-between mt-6">
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
            <div className="flex items-center justify-center h-full text-slate-500">
              Select a lesson from the sidebar
            </div>
          )}
        </main>
      </div>
    </div>
  );
}