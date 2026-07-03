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

const FEATURES = [
  { title: "Adaptive quizzes",   desc: "Difficulty adjusts automatically as your skills grow" },
  { title: "AICA tutor",         desc: "Ask questions mid-lesson and get AI answers instantly" },
  { title: "Face ID login",      desc: "Biometric authentication — no password required" },
];

export function LoginPage() {
  const [tab, setTab]           = useState<"password" | "face">("password");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [faceBlob, setFaceBlob] = useState<Blob | null>(null);
  const { login }               = useAuthStore();
  const navigate                = useNavigate();

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const res = await authApi.login(email, password);
      login(res.data.user, res.data.access_token, res.data.refresh_token);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed. Check your credentials.");
    } finally { setLoading(false); }
  };

  const handleFaceLogin = async () => {
    if (!faceBlob) { setError("Please capture your face first."); return; }
    if (faceBlob.size < 1000) { setError("Image capture failed — too small. Please retake."); return; }
    setError(""); setLoading(true);
    try {
      const res = await authApi.faceLogin(faceBlob);
      login(res.data.user, res.data.access_token, res.data.refresh_token);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Face not recognised. Try password login.");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex">
      {/* ── Left identity panel (desktop only) ── */}
      <div className="hidden lg:flex lg:w-5/12 flex-col justify-between p-14 bg-navy-950 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                          w-96 h-96 bg-brand-500/12 rounded-full blur-3xl animate-glow" />
          <div className="absolute bottom-0 left-0 right-0 h-32
                          bg-gradient-to-t from-navy-950/60 to-transparent" />
        </div>

        <div className="relative">
          <div className="flex items-center gap-3 mb-16">
            <LogoMark />
            <span className="font-display font-semibold text-lg text-slate-100">LearnAI</span>
          </div>

          <h2 className="font-display text-[2.6rem] font-bold text-slate-100 leading-[1.1] mb-5">
            Train your mind<br />on machine<br />learning.
          </h2>
          <p className="text-slate-400 text-sm leading-relaxed max-w-xs">
            Structured AI&thinsp;/&thinsp;ML courses with adaptive quizzes
            and a live AI tutor — learn faster, retain more.
          </p>
        </div>

        <div className="relative space-y-6">
          {FEATURES.map(({ title, desc }) => (
            <div key={title} className="flex gap-3 items-start">
              <div className="w-1.5 h-1.5 rounded-full bg-brand-400 mt-[5px] flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-slate-200">{title}</p>
                <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
              </div>
            </div>
          ))}
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

          <h1 className="font-display text-2xl font-bold text-slate-100 mb-1">Welcome back</h1>
          <p className="text-slate-500 text-sm mb-7">Sign in to continue your journey</p>

          {/* Tab switcher */}
          <div className="flex rounded-xl bg-navy-800 border border-navy-700 p-1 gap-1 mb-6">
            {(["password", "face"] as const).map((t) => (
              <button key={t} onClick={() => { setTab(t); setError(""); }}
                className={`flex-1 py-2 rounded-lg text-sm transition-all
                  ${tab === t
                    ? "bg-brand-500 text-white font-semibold shadow-sm"
                    : "text-slate-400 hover:text-slate-200"}`}
                style={{ fontFamily: "Space Grotesk, sans-serif" }}>
                {t === "password" ? "Password" : "Face ID"}
              </button>
            ))}
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3
                            text-red-400 text-sm mb-5">{error}</div>
          )}

          {tab === "password" ? (
            <form onSubmit={handlePasswordLogin} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-400 mb-1.5 block">Email</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com" className="input" required />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-400 mb-1.5 block">Password</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••" className="input" required />
              </div>
              <button type="submit" disabled={loading} className="btn-primary w-full mt-1">
                {loading ? "Signing in…" : "Sign in"}
              </button>
            </form>
          ) : (
            <div className="space-y-4">
              <FaceCapture
                onCapture={setFaceBlob}
                onClear={() => setFaceBlob(null)}
                captured={!!faceBlob}
                label="Look at the camera to sign in"
              />
              <button onClick={handleFaceLogin} disabled={loading || !faceBlob} className="btn-primary w-full">
                {loading ? "Verifying…" : "Sign in with Face ID"}
              </button>
            </div>
          )}

          <p className="text-center text-sm text-slate-500 mt-8">
            No account?{" "}
            <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium transition-colors">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
