import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { authApi } from "../services/api";
import { useAuthStore } from "../store/auth.store";
import { FaceCapture } from "../components/auth/FaceCapture";

export function LoginPage() {
  const [tab, setTab] = useState<"password" | "face">("password");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [faceBlob, setFaceBlob] = useState<Blob | null>(null);
  const { login } = useAuthStore();
  const navigate = useNavigate();

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
  if (!faceBlob) { 
    setError("Please capture your face first."); 
    return; 
  }
  
  // Debug: check blob size
  console.log("Face blob size:", faceBlob.size, "type:", faceBlob.type);
  
  if (faceBlob.size < 1000) {
    setError("Image capture failed — too small. Please retake.");
    return;
  }
  
  setError(""); 
  setLoading(true);
  try {
    const res = await authApi.faceLogin(faceBlob);
    login(res.data.user, res.data.access_token, res.data.refresh_token);
    navigate("/dashboard");
  } catch (err: any) {
    setError(err.response?.data?.detail || "Face not recognised. Try password login.");
  } finally { 
    setLoading(false); 
  }
};

  return (
    <div className="min-h-screen bg-navy-950 flex items-center justify-center p-4">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96
                        bg-brand-500/10 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md animate-slide-up relative">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-brand-500 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-brand-500/30">
            <span className="text-white text-2xl font-bold">AI</span>
          </div>
          <h1 className="text-2xl font-semibold text-slate-100">Welcome back</h1>
          <p className="text-slate-500 text-sm mt-1">Sign in to your learning account</p>
        </div>

        <div className="card space-y-5">
          {/* Tab switcher */}
          <div className="flex rounded-xl bg-navy-900 p-1 gap-1">
            {(["password", "face"] as const).map((t) => (
              <button key={t} onClick={() => { setTab(t); setError(""); }}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all
                  ${tab === t ? "bg-brand-500 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"}`}>
                {t === "password" ? "🔑 Password" : "📷 Face ID"}
              </button>
            ))}
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3
                            text-red-400 text-sm">{error}</div>
          )}

          {tab === "password" ? (
            <form onSubmit={handlePasswordLogin} className="space-y-4">
              <div>
                <label className="text-xs text-slate-400 mb-1.5 block">Email</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com" className="input" required />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1.5 block">Password</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••" className="input" required />
              </div>
              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading ? "Signing in..." : "Sign In"}
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
                {loading ? "Verifying face..." : "Sign In with Face"}
              </button>
            </div>
          )}

          <p className="text-center text-sm text-slate-500">
            No account?{" "}
            <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}