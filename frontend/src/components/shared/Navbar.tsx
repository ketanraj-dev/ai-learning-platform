import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../../store/auth.store";
import { authApi } from "../../services/api";

function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="28" height="28" rx="7" fill="#E8843C" />
      <rect x="6"  y="16" width="4" height="7"  rx="1.5" fill="white" />
      <rect x="12" y="11" width="4" height="12" rx="1.5" fill="white" />
      <rect x="18" y="7"  width="4" height="16" rx="1.5" fill="rgba(255,255,255,0.6)" />
    </svg>
  );
}

export function Navbar() {
  const { user, logout, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    try { await authApi.logout(); } catch {}
    logout();
    navigate("/login");
  };

  const navLink = (path: string) =>
    location.pathname.startsWith(path)
      ? "text-slate-100 font-medium relative after:absolute after:bottom-0 after:inset-x-1 after:h-0.5 after:bg-brand-500 after:rounded-full"
      : "text-slate-400 hover:text-slate-200";

  if (!isAuthenticated) return null;

  return (
    <nav className="sticky top-0 z-50 bg-navy-900/90 backdrop-blur-md border-b border-navy-700">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-15 flex items-center justify-between" style={{ height: 60 }}>
        {/* Logo */}
        <Link to="/dashboard" className="flex items-center gap-2.5 group">
          <LogoMark size={28} />
          <span className="font-display font-semibold text-base text-slate-100 hidden sm:block tracking-tight">
            LearnAI
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {[
            { to: "/dashboard", label: "Dashboard" },
            { to: "/scan",      label: "Scan"      },
            { to: "/analytics", label: "Analytics" },
          ].map(({ to, label }) => (
            <Link key={to} to={to}
              className={`relative px-3 py-1.5 rounded-lg text-sm transition-all duration-150 ${navLink(to)}`}>
              {label}
            </Link>
          ))}
        </div>

        {/* User menu */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex flex-col items-end">
            <p className="text-sm font-medium text-slate-200 leading-tight">{user?.name}</p>
            <p className="text-xs text-slate-500 leading-tight">{user?.email}</p>
          </div>

          <div className="w-8 h-8 rounded-full bg-brand-500/20 border border-brand-500/30
                         flex items-center justify-center text-brand-400 font-display font-semibold text-sm">
            {user?.name?.charAt(0).toUpperCase()}
          </div>

          <button onClick={handleLogout}
            className="text-slate-500 hover:text-slate-300 text-sm transition-colors duration-150 ml-1">
            Sign out
          </button>
        </div>
      </div>
    </nav>
  );
}
