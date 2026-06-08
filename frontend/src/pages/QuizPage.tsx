import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { assessmentsApi } from "../services/api";
import { Navbar } from "../components/shared/Navbar";
import type { QuizData, Question } from "../types/index";

export function QuizPage() {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState<QuizData | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [current, setCurrent] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [loading, setLoading] = useState(true);
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

  // Timer
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

  const formatTime = (s: number) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, "0")}`;
  const q: Question | undefined = quiz?.questions[current];
  const answered = Object.keys(answers).length;

  if (loading) return (
    <div className="page">
      <Navbar />
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400 animate-pulse">Loading quiz...</div>
      </div>
    </div>
  );

  if (!quiz) return null;

  return (
    <div className="page">
      <Navbar />
      <div className="page-content max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 animate-slide-up">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className={`badge-${quiz.difficulty_level === "easy" ? "easy" : quiz.difficulty_level === "hard" ? "hard" : "medium"}`}>
                {quiz.difficulty_level}
              </span>
              <span className="text-xs text-slate-500">{answered}/{quiz.total_questions} answered</span>
            </div>
            <h1 className="text-xl font-semibold text-slate-100">Quiz</h1>
          </div>
          {quiz.time_limit_mins > 0 && (
            <div className={`font-mono text-lg font-semibold ${timeLeft < 60 ? "text-red-400 animate-pulse" : "text-brand-400"}`}>
              ⏱ {formatTime(timeLeft)}
            </div>
          )}
        </div>

        {/* Progress */}
        <div className="progress-bar mb-6">
          <div className="progress-fill" style={{ width: `${((current + 1) / quiz.total_questions) * 100}%` }} />
        </div>

        {/* Question */}
        {q && (
          <div className="card animate-fade-in" key={q.id}>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs text-slate-500">Question {current + 1} of {quiz.total_questions}</span>
              <span className="badge-info">{q.topic_tag.replace(/_/g, " ")}</span>
            </div>
            <p className="text-slate-100 font-medium mb-6 leading-relaxed text-lg">
              {q.question_text}
            </p>

            {/* Options */}
            <div className="space-y-3">
              {q.options.map((opt) => {
                const selected = answers[q.id] === opt;
                return (
                  <button key={opt}
                    onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: opt }))}
                    className={`w-full text-left px-4 py-3.5 rounded-xl border text-sm
                      transition-all duration-150 active:scale-[0.99]
                      ${selected
                        ? "bg-brand-500/10 border-brand-500/60 text-brand-300"
                        : "bg-navy-900 border-navy-700 text-slate-300 hover:border-navy-600 hover:bg-navy-800"
                      }`}>
                    <span className={`inline-flex w-6 h-6 rounded-full border mr-3 items-center justify-center text-xs flex-shrink-0
                      ${selected ? "border-brand-400 bg-brand-500/20 text-brand-400" : "border-navy-600"}`}>
                      {selected ? "●" : "○"}
                    </span>
                    {opt}
                  </button>
                );
              })}
            </div>

            {/* Navigation */}
            <div className="flex justify-between mt-6 pt-4 border-t border-navy-700">
              <button onClick={() => setCurrent((p) => Math.max(0, p - 1))}
                disabled={current === 0} className="btn-secondary text-sm">
                ← Back
              </button>
              <div className="flex gap-2">
                {current < quiz.total_questions - 1 ? (
                  <button onClick={() => setCurrent((p) => p + 1)} className="btn-primary text-sm">
                    Next →
                  </button>
                ) : (
                  <button
                    onClick={handleSubmit}
                    disabled={submitting || answered === 0}
                    className="btn-primary text-sm"
                  >
                    {submitting ? "Submitting..." : `Submit (${answered}/${quiz.total_questions})`}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Question navigator dots */}
        <div className="flex flex-wrap gap-2 mt-4 justify-center">
          {quiz.questions.map((question, i) => (
            <button key={i} onClick={() => setCurrent(i)}
              className={`w-8 h-8 rounded-lg text-xs font-medium transition-all
                ${i === current ? "bg-brand-500 text-white" :
                  answers[question.id] ? "bg-brand-500/20 text-brand-400 border border-brand-500/30" :
                  "bg-navy-800 text-slate-500 hover:bg-navy-700"}`}>
              {i + 1}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}