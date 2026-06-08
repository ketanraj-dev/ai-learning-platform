import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { authApi } from "../services/api";
import { useAuthStore } from "../store/auth.store";
import { FaceCapture } from "../components/auth/FaceCapture";

export function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [faceBlob, setFaceBlob] = useState<Blob | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const navigate = useNavigate();

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
    <div className="min-h-screen bg-navy-950 flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-96 h-96
                        bg-brand-500/8 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md animate-slide-up relative">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-brand-500 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-brand-500/30">
            <span className="text-white text-2xl font-bold">AI</span>
          </div>
          <h1 className="text-2xl font-semibold text-slate-100">Create account</h1>
          <p className="text-slate-500 text-sm mt-1">Start your AI/ML learning journey</p>
        </div>

        <div className="card">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3
                            text-red-400 text-sm mb-4">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Full name</label>
              <input value={name} onChange={(e) => setName(e.target.value)}
                placeholder="John Doe" className="input" required />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com" className="input" required />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder="Min. 6 characters" className="input" minLength={6} required />
            </div>

            {/* Face registration — optional */}
            <div className="border border-navy-700 rounded-xl p-4 bg-navy-900/50">
              <p className="text-xs text-slate-400 mb-3">
                📷 <span className="text-slate-300 font-medium">Face Login</span>
                <span className="ml-1">(optional — enables face recognition login)</span>
              </p>
              <FaceCapture
                onCapture={setFaceBlob}
                onClear={() => setFaceBlob(null)}
                captured={!!faceBlob}
              />
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
              {loading ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <p className="text-center text-sm text-slate-500 mt-4">
            Already have an account?{" "}
            <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}