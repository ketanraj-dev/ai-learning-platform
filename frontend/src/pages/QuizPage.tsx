import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { assessmentsApi } from "../services/api";
import { Navbar } from "../components/shared/Navbar";
import type { QuizData, Question } from "../types/index";

export function QuizPage() {
  const { courseId }    = useParams<{ courseId: string }>();
  const navigate        = useNavigate();
  const [quiz, setQuiz] = useState<QuizData | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [current, setCurrent] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [loading, setLoading]   = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const startTime = useRef(Date.now());

  useEffect(() => {
    if (!courseId) return;
    assessmentsApi.getQuiz(courseId, 10)
      .then((res) => {
        setQuiz(res.data);
        setTimeLeft(res.data.time_limit_mins * 60);
        startTime.current = Date.now();
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [courseId]);

  useEffect(() => {
    if (!quiz || timeLeft <= 0) return;
    const t = setInterval(() => setTimeLeft((p) => {
      if (p <= 1) { clearInterval(t); handleSubmit(); return 0; }
      return p - 1;
    }), 1000);
    return () => clearInterval(t);
  }, [quiz, timeLeft]);

  const handleSubmit = async () => {
    if (!quiz || submitting) return;
    setSubmitting(true);
    const timeTaken = Math.round((Date.now() - startTime.current) / 1000);
    try {
      const res = await assessmentsApi.submitQuiz({
        course_id: quiz.course_id,
        answers: Object.entries(answers).map(([question_id, selected_answer]) => ({
          question_id, selected_answer,
        })),
        time_taken_seconds: timeTaken,
      });
      navigate("/result", { state: { result: res.data } });
    } catch (e) { console.error(e); setSubmitting(false); }
  };

  const formatTime = (s: number) =>
    `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, "0")}`;

  const q: Question | undefined = quiz?.questions[current];
  const answered = Object.keys(answers).length;

  if (loading) return (
    <div className="page">
      <Navbar />
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-500 text-sm animate-pulse">Loading quiz…</div>
      </div>
    </div>
  );
  if (!quiz) return null;

  return (
    <div className="page">
      <Navbar />
      <div className="page-content max-w-2xl mx-auto">

        {/* Header */}
        <div className="flex items-start justify-between mb-6 animate-slide-up">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className={`badge-${quiz.difficulty_level === "easy" ? "easy" : quiz.difficulty_level === "hard" ? "hard" : "medium"}`}>
                {quiz.difficulty_level}
              </span>
              <span className="text-xs text-slate-500">{answered} of {quiz.total_questions} answered</span>
            </div>
            <h1 className="text-xl font-bold text-slate-100">Quiz</h1>
          </div>

          {quiz.time_limit_mins > 0 && (
            <div className={`font-mono text-lg font-semibold px-3 py-1.5 rounded-lg border
              ${timeLeft < 60
                ? "text-red-400 bg-red-500/10 border-red-500/20 animate-pulse"
                : "text-slate-200 bg-navy-800 border-navy-700"}`}>
              {formatTime(timeLeft)}
            </div>
          )}
        </div>

        {/* Overall progress */}
        <div className="progress-bar mb-7">
          <div className="progress-fill" style={{ width: `${((current + 1) / quiz.total_questions) * 100}%` }} />
        </div>

        {/* Question card */}
        {q && (
          <div className="card animate-fade-in" key={q.id}>
            <div className="flex items-center justify-between mb-5">
              <span className="text-xs text-slate-500 font-mono">
                {String(current + 1).padStart(2, "0")} / {String(quiz.total_questions).padStart(2, "0")}
              </span>
              <span className="badge-info">{q.topic_tag.replace(/_/g, " ")}</span>
            </div>

            <p className="text-slate-100 font-medium mb-6 leading-relaxed text-base">
              {q.question_text}
            </p>

            {/* Options */}
            <div className="space-y-2.5">
              {q.options.map((opt, optIdx) => {
                const selected = answers[q.id] === opt;
                const label = String.fromCharCode(65 + optIdx);
                return (
                  <button key={opt}
                    onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: opt }))}
                    className={`w-full text-left px-4 py-3.5 rounded-xl border text-sm
                                transition-all duration-150 active:scale-[0.99] flex items-center gap-3
                      ${selected
                        ? "bg-brand-500/10 border-brand-500/40 text-slate-100"
                        : "bg-navy-950 border-navy-700 text-slate-300 hover:border-navy-600 hover:bg-navy-800"
                      }`}>
                    <span className={`w-6 h-6 rounded-full border flex items-center justify-center
                                      text-xs font-semibold flex-shrink-0 transition-all
                      ${selected
                        ? "border-brand-400 bg-brand-500/20 text-brand-400"
                        : "border-navy-600 text-slate-600"}`}
                      style={{ fontFamily: "Space Grotesk, sans-serif" }}>
                      {label}
                    </span>
                    {opt}
                  </button>
                );
              })}
            </div>

            {/* Navigation */}
            <div className="flex justify-between mt-6 pt-5 border-t border-navy-700">
              <button onClick={() => setCurrent((p) => Math.max(0, p - 1))}
                disabled={current === 0} className="btn-secondary text-sm">
                ← Back
              </button>
              {current < quiz.total_questions - 1 ? (
                <button onClick={() => setCurrent((p) => p + 1)} className="btn-primary text-sm">
                  Next →
                </button>
              ) : (
                <button onClick={handleSubmit}
                  disabled={submitting || answered === 0}
                  className="btn-primary text-sm">
                  {submitting ? "Submitting…" : `Submit (${answered}/${quiz.total_questions})`}
                </button>
              )}
            </div>
          </div>
        )}

        {/* Question navigator */}
        <div className="flex flex-wrap gap-1.5 mt-4 justify-center">
          {quiz.questions.map((question, i) => (
            <button key={i} onClick={() => setCurrent(i)}
              className={`w-8 h-8 rounded-lg text-xs font-semibold transition-all
                ${i === current
                  ? "bg-brand-500 text-white"
                  : answers[question.id]
                  ? "bg-brand-500/15 text-brand-400 border border-brand-500/25"
                  : "bg-navy-800 text-slate-500 hover:bg-navy-700 border border-navy-700"}`}
              style={{ fontFamily: "Space Grotesk, sans-serif" }}>
              {i + 1}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
