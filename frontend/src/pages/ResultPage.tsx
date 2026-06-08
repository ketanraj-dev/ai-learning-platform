import { useLocation, useNavigate } from "react-router-dom";
import { Navbar } from "../components/shared/Navbar";
import type { QuizResult } from "../types/index";

export function ResultPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const result: QuizResult = state?.result;

  if (!result) { navigate("/dashboard"); return null; }

  const scoreColor = result.score >= 80 ? "text-green-400" : result.score >= 50 ? "text-yellow-400" : "text-red-400";
  const scoreBg = result.score >= 80 ? "bg-green-500/10 border-green-500/20" : result.score >= 50 ? "bg-yellow-500/10 border-yellow-500/20" : "bg-red-500/10 border-red-500/20";

  return (
    <div className="page">
      <Navbar />
      <div className="page-content max-w-2xl mx-auto">
        {/* Score card */}
        <div className={`card border ${scoreBg} text-center mb-6 animate-slide-up`}>
          <div className={`text-6xl font-bold ${scoreColor} mb-2`}>
            {result.score.toFixed(0)}%
          </div>
          <p className="text-slate-300 font-medium mb-1">{result.performance_message}</p>
          <p className="text-slate-500 text-sm">
            {result.correct_count} correct out of {result.total_questions} questions
          </p>
          <div className="flex justify-center gap-3 mt-4">
            <span className={`badge-${result.difficulty_level === "easy" ? "easy" : result.difficulty_level === "hard" ? "hard" : "medium"}`}>
              {result.difficulty_level} difficulty
            </span>
            <span className="badge-info">Next: {result.next_difficulty}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 mb-8">
          <button onClick={() => navigate(`/quiz/${result.course_id}`)} className="btn-primary flex-1">
            Try Again
          </button>
          <button onClick={() => navigate("/dashboard")} className="btn-secondary flex-1">
            Dashboard
          </button>
          <button onClick={() => navigate("/analytics")} className="btn-ghost">
            Analytics
          </button>
        </div>

        {/* Question breakdown */}
        <div className="section-title">Question Review</div>
        <div className="space-y-3">
          {result.question_results.map((qr, i) => (
            <div key={i} className={`card border animate-fade-in
              ${qr.is_correct ? "border-green-500/20" : "border-red-500/20"}`}
              style={{ animationDelay: `${i * 40}ms` }}>
              <div className="flex items-start gap-3">
                <span className={`text-lg flex-shrink-0 mt-0.5 ${qr.is_correct ? "text-green-400" : "text-red-400"}`}>
                  {qr.is_correct ? "✓" : "✗"}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200 font-medium mb-2">{qr.question_text}</p>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500 w-20 flex-shrink-0">Your answer:</span>
                      <span className={`text-xs font-medium ${qr.is_correct ? "text-green-400" : "text-red-400"}`}>
                        {qr.user_answer || "—"}
                      </span>
                    </div>
                    {!qr.is_correct && (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-500 w-20 flex-shrink-0">Correct:</span>
                        <span className="text-xs font-medium text-green-400">{qr.correct_answer}</span>
                      </div>
                    )}
                    {qr.explanation && (
                      <p className="text-xs text-slate-500 mt-2 leading-relaxed border-t border-navy-700 pt-2">
                        💡 {qr.explanation}
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