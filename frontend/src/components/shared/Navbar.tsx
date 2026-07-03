import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../../store/auth.store";
import { authApi } from "../../services/api";

function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={Math.round(size * 1.2)} viewBox="0 0 146 176" fill="none" xmlns="http://www.w3.org/2000/svg">
      <g stroke="#FFC72C" strokeWidth="7" strokeLinecap="round">
        <line x1="95" y1="8" x2="88" y2="30" />
        <line x1="55" y1="14" x2="66" y2="34" />
        <line x1="22" y1="36" x2="40" y2="50" />
        <line x1="6" y1="72" x2="28" y2="76" />
        <line x1="14" y1="108" x2="34" y2="98" />
      </g>
      <circle cx="88" cy="80" r="58" fill="#FFC72C" />
      <path
        d="M100 32 C78 26, 56 40, 58 62 C59 78, 74 88, 90 80 C99 75, 98 63, 88 61"
        fill="none" stroke="#F8FAFC" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round"
      />
      <path d="M88 61 C82 74, 84 92, 100 104" fill="none" stroke="#F8FAFC" strokeWidth="7" strokeLinecap="round" />
      <path d="M62 118 L118 118" fill="none" stroke="#F8FAFC" strokeWidth="7" strokeLinecap="round" />
      <path d="M58 132 L128 132" fill="none" stroke="#F8FAFC" strokeWidth="7" strokeLinecap="round" />
      <path d="M56 146 L140 168" fill="none" stroke="#F8FAFC" strokeWidth="7" strokeLinecap="round" />
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
            Smart Education
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
