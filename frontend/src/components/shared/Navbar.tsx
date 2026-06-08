import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../../store/auth.store";
import { authApi } from "../../services/api";

export function Navbar() {
  const { user, logout, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    try { await authApi.logout(); } catch {}
    logout();
    navigate("/login");
  };

  const isActive = (path: string) =>
    location.pathname.startsWith(path)
      ? "text-brand-400 font-medium"
      : "text-slate-400 hover:text-slate-200";

  if (!isAuthenticated) return null;

  return (
    <nav className="sticky top-0 z-50 bg-navy-900/80 backdrop-blur-md border-b border-navy-800">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/dashboard" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
            <span className="text-white text-sm font-bold">AI</span>
          </div>
          <span className="font-semibold text-slate-100 hidden sm:block">
            LearnAI
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          <Link to="/dashboard" className={`btn-ghost text-sm ${isActive("/dashboard")}`}>
            Dashboard
          </Link>
          <Link to="/analytics" className={`btn-ghost text-sm ${isActive("/analytics")}`}>
            Analytics
          </Link>
        </div>

        {/* User menu */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:block text-right">
            <p className="text-sm font-medium text-slate-200">{user?.name}</p>
            <p className="text-xs text-slate-500">{user?.email}</p>
          </div>
          <div className="w-9 h-9 rounded-full bg-brand-500/20 border border-brand-500/30
                          flex items-center justify-center text-brand-400 font-semibold text-sm">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <button onClick={handleLogout} className="btn-ghost text-sm text-slate-400">
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}