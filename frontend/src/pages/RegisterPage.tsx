import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { authApi } from "../services/api";
import { useAuthStore } from "../store/auth.store";
import { FaceCapture } from "../components/auth/FaceCapture";

function LogoMark() {
  return (
    <svg width="36" height="36" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="28" height="28" rx="7" fill="#E8843C" />
      <rect x="6"  y="16" width="4" height="7"  rx="1.5" fill="white" />
      <rect x="12" y="11" width="4" height="12" rx="1.5" fill="white" />
      <rect x="18" y="7"  width="4" height="16" rx="1.5" fill="rgba(255,255,255,0.6)" />
    </svg>
  );
}

export function RegisterPage() {
  const [name, setName]         = useState("");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [faceBlob, setFaceBlob] = useState<Blob | null>(null);
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const { login }               = useAuthStore();
  const navigate                = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const form = new FormData();
      form.append("name", name);
      form.append("email", email);
      form.append("password", password);
      if (faceBlob) form.append("face_image", faceBlob, "face.jpg");
      const res = await authApi.register(form);
      login(res.data.user, res.data.access_token, res.data.refresh_token);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed. Please try again.");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex">
      {/* ── Left identity panel (desktop only) ── */}
      <div className="hidden lg:flex lg:w-5/12 flex-col justify-between p-14 bg-navy-950 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                          w-96 h-96 bg-brand-500/12 rounded-full blur-3xl animate-glow" />
        </div>

        <div className="relative">
          <div className="flex items-center gap-3 mb-16">
            <LogoMark />
            <span className="font-display font-semibold text-lg text-slate-100">LearnAI</span>
          </div>

          <h2 className="font-display text-[2.6rem] font-bold text-slate-100 leading-[1.1] mb-5">
            Start your<br />AI&thinsp;/&thinsp;ML<br />journey.
          </h2>
          <p className="text-slate-400 text-sm leading-relaxed max-w-xs">
            Join learners studying Python, Machine Learning, Deep Learning,
            NLP, and Statistics — all in one place.
          </p>
        </div>

        <div className="relative">
          <div className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-navy-800/60
                          border border-navy-700 text-xs text-slate-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
            Free to get started — no credit card required
          </div>
        </div>
      </div>

      {/* ── Right form panel ── */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-10 bg-navy-900">
        <div className="w-full max-w-sm animate-slide-up">
          {/* Mobile logo */}
          <div className="flex items-center gap-2.5 mb-10 lg:hidden">
            <LogoMark />
            <span className="font-display font-semibold text-slate-100">LearnAI</span>
          </div>

          <h1 className="font-display text-2xl font-bold text-slate-100 mb-1">Create account</h1>
          <p className="text-slate-500 text-sm mb-7">Start your AI&thinsp;/&thinsp;ML learning journey</p>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3
                            text-red-400 text-sm mb-5">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-400 mb-1.5 block">Full name</label>
              <input value={name} onChange={(e) => setName(e.target.value)}
                placeholder="Jane Smith" className="input" required />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400 mb-1.5 block">Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com" className="input" required />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400 mb-1.5 block">Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters" className="input" minLength={6} required />
            </div>

            {/* Face registration */}
            <div className="rounded-xl border border-navy-700 bg-navy-950/60 p-4">
              <p className="text-xs font-medium text-slate-300 mb-0.5">Face ID login</p>
              <p className="text-xs text-slate-500 mb-3">Optional — enables biometric sign-in</p>
              <FaceCapture
                onCapture={setFaceBlob}
                onClear={() => setFaceBlob(null)}
                captured={!!faceBlob}
              />
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="text-center text-sm text-slate-500 mt-6">
            Already have an account?{" "}
            <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
