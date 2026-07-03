import { useLocation, useNavigate } from "react-router-dom";
import { Navbar } from "../components/shared/Navbar";
import type { QuizResult } from "../types/index";

function ScoreRing({ score }: { score: number }) {
  const r = 52;
  const circumference = 2 * Math.PI * r;
  const dash = (score / 100) * circumference;

  const color = score >= 80 ? "#22C55E" : score >= 50 ? "#F59E0B" : "#EF4444";

  return (
    <div className="relative inline-flex items-center justify-center w-36 h-36">
      <svg width="144" height="144" className="-rotate-90">
        <circle cx="72" cy="72" r={r} fill="none" stroke="#1C2B40" strokeWidth="8" />
        <circle cx="72" cy="72" r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - dash}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1s ease" }}
        />
      </svg>
      <div className="absolute text-center">
        <span className="font-display text-3xl font-bold" style={{ color }}>
          {score.toFixed(0)}
        </span>
        <span className="block text-xs text-slate-500 mt-0.5">%</span>
      </div>
    </div>
  );
}

export function ResultPage() {
  const { state }  = useLocation();
  const navigate   = useNavigate();
  const result: QuizResult = state?.result;

  if (!result) { navigate("/dashboard"); return null; }

  const scoreLabel = result.score >= 80 ? "Excellent" : result.score >= 50 ? "Good effort" : "Keep practising";

  return (
    <div className="page">
      <Navbar />
      <div className="page-content max-w-2xl mx-auto">

        {/* Score hero */}
        <div className="card text-center mb-6 animate-slide-up py-10">
          <ScoreRing score={result.score} />
          <h2 className="font-display text-xl font-bold text-slate-100 mt-4 mb-1">{scoreLabel}</h2>
          <p className="text-slate-400 text-sm">{result.performance_message}</p>
          <p className="text-slate-500 text-xs mt-2">
            {result.correct_count} correct · {result.total_questions} questions
          </p>
          <div className="flex justify-center gap-2 mt-4">
            <span className={`badge-${result.difficulty_level === "easy" ? "easy" : result.difficulty_level === "hard" ? "hard" : "medium"}`}>
              {result.difficulty_level}
            </span>
            <span className="badge-info">Next: {result.next_difficulty}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 mb-8">
          <button onClick={() => navigate(`/quiz/${result.course_id}`)} className="btn-primary flex-1">
            Try again
          </button>
          <button onClick={() => navigate("/dashboard")} className="btn-secondary flex-1">
            Dashboard
          </button>
          <button onClick={() => navigate("/analytics")} className="btn-ghost">
            Analytics
          </button>
        </div>

        {/* Question breakdown */}
        <p className="section-title">Question review</p>
        <div className="space-y-3">
          {result.question_results.map((qr, i) => (
            <div key={i}
              className={`card border animate-fade-in
                ${qr.is_correct ? "border-emerald-500/20" : "border-red-500/20"}`}
              style={{ animationDelay: `${i * 40}ms` }}>
              <div className="flex items-start gap-3">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5
                  ${qr.is_correct ? "bg-emerald-500/15" : "bg-red-500/15"}`}>
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                    {qr.is_correct
                      ? <path d="M2 5l2.2 2.2L8 3" stroke="#22C55E" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      : <path d="M2.5 2.5l5 5M7.5 2.5l-5 5" stroke="#EF4444" strokeWidth="1.5" strokeLinecap="round"/>
                    }
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200 font-medium mb-2.5">{qr.question_text}</p>
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500 w-20 flex-shrink-0">Your answer</span>
                      <span className={`text-xs font-medium
                        ${qr.is_correct ? "text-emerald-400" : "text-red-400"}`}>
                        {qr.user_answer || "—"}
                      </span>
                    </div>
                    {!qr.is_correct && (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-500 w-20 flex-shrink-0">Correct</span>
                        <span className="text-xs font-medium text-emerald-400">{qr.correct_answer}</span>
                      </div>
                    )}
                    {qr.explanation && (
                      <p className="text-xs text-slate-500 mt-2 leading-relaxed border-t border-navy-700 pt-2">
                        {qr.explanation}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
