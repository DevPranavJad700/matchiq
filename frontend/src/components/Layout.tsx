import { Link, useLocation } from 'react-router-dom';
import { BarChart3, Home, Zap, Users, Calendar, TrendingUp } from 'lucide-react';
import { clsx } from 'clsx';

const navItems = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/predict', label: 'Predictor', icon: Zap },
  { to: '/teams', label: 'Teams', icon: Users },
  { to: '/matches', label: 'Matches', icon: Calendar },
  { to: '/analytics', label: 'Analytics', icon: TrendingUp },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-ambient-mesh" style={{ background: 'var(--navy-950)' }}>
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-[var(--border)] backdrop-blur-xl transition-colors duration-300"
        style={{ background: 'rgba(8,14,26,0.85)' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#2979ff] to-[#7c3aed] flex items-center justify-center shadow-[0_0_20px_rgba(41,121,255,0.5)] group-hover:scale-105 group-hover:shadow-[0_0_28px_rgba(41,121,255,0.7)] transition-all duration-300">
                <BarChart3 size={20} className="text-white transform group-hover:rotate-6 transition-transform" />
              </div>
              <div className="flex flex-col">
                <span className="font-extrabold text-xl tracking-tight text-white leading-none">
                  Match<span className="gradient-text">IQ</span>
                </span>
                <span className="text-[10px] text-[var(--text-muted)] font-medium tracking-wider uppercase mt-0.5">
                  Predictive Analytics
                </span>
              </div>
            </Link>

            {/* Desktop nav */}
            <nav className="hidden md:flex items-center gap-1.5 p-1 rounded-2xl bg-[rgba(13,21,39,0.6)] border border-[var(--border)]">
              {navItems.map(({ to, label, icon: Icon }) => {
                const active = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));
                return (
                  <Link
                    key={to}
                    to={to}
                    className={clsx(
                      'flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-sm font-semibold transition-all duration-200 relative',
                      active
                        ? 'text-white bg-gradient-to-r from-[rgba(41,121,255,0.25)] to-[rgba(124,58,237,0.25)] border border-[rgba(41,121,255,0.4)] shadow-[0_0_12px_rgba(41,121,255,0.2)]'
                        : 'text-[var(--text-secondary)] hover:text-white hover:bg-[var(--glass-hover)]'
                    )}
                  >
                    <Icon size={16} className={clsx(active ? 'text-[#60a5fa]' : 'text-[var(--text-muted)]')} />
                    {label}
                  </Link>
                );
              })}
            </nav>

            {/* Demo badge */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full border border-[rgba(0,230,118,0.3)] bg-[rgba(0,230,118,0.08)] shadow-[0_0_12px_rgba(0,230,118,0.15)]">
              <div className="w-2 h-2 rounded-full bg-[#00e676] animate-pulse" />
              <span className="text-xs font-semibold text-[#00e676]">Live Model Ready</span>
            </div>
          </div>
        </div>

        {/* Mobile nav */}
        <div className="md:hidden border-t border-[var(--border)] bg-[rgba(13,21,39,0.95)]">
          <div className="flex overflow-x-auto px-4 py-2 gap-1.5 no-scrollbar">
            {navItems.map(({ to, label, icon: Icon }) => {
              const active = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));
              return (
                <Link
                  key={to}
                  to={to}
                  className={clsx(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all',
                    active
                      ? 'bg-gradient-to-r from-[#2979ff] to-[#7c3aed] text-white shadow-md'
                      : 'text-[var(--text-secondary)] hover:text-white'
                  )}
                >
                  <Icon size={14} />
                  {label}
                </Link>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--border)] py-6 text-center bg-[rgba(8,14,26,0.6)] backdrop-blur-md">
        <p className="text-[var(--text-muted)] text-xs font-medium">
          MatchIQ Premier League Prediction Engine · Powered by FastAPI, React 19, XGBoost & SHAP XAI
        </p>
      </footer>
    </div>
  );
}
