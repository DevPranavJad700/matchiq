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
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--navy-950)' }}>
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-[var(--border)] backdrop-blur-xl"
        style={{ background: 'rgba(8,14,26,0.9)' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-lg bg-[#2979ff] flex items-center justify-center shadow-[0_0_16px_rgba(41,121,255,0.4)] group-hover:shadow-[0_0_24px_rgba(41,121,255,0.6)] transition-shadow">
                <BarChart3 size={18} className="text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight">
                Match<span className="text-[#2979ff]">IQ</span>
              </span>
            </Link>

            {/* Desktop nav */}
            <nav className="hidden md:flex items-center gap-1">
              {navItems.map(({ to, label, icon: Icon }) => {
                const active = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));
                return (
                  <Link
                    key={to}
                    to={to}
                    className={clsx(
                      'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all',
                      active
                        ? 'bg-[rgba(41,121,255,0.15)] text-white border border-[rgba(41,121,255,0.3)]'
                        : 'text-[var(--text-secondary)] hover:text-white hover:bg-[var(--glass)]'
                    )}
                  >
                    <Icon size={15} />
                    {label}
                  </Link>
                );
              })}
            </nav>

            {/* Demo badge */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full border border-[rgba(255,193,7,0.3)] bg-[rgba(255,193,7,0.08)]">
              <div className="w-1.5 h-1.5 rounded-full bg-[#ffc107] animate-pulse" />
              <span className="text-xs font-medium text-[#ffc107]">Demo Data</span>
            </div>
          </div>
        </div>

        {/* Mobile nav */}
        <div className="md:hidden border-t border-[var(--border)]">
          <div className="flex overflow-x-auto px-4 py-2 gap-1 no-scrollbar">
            {navItems.map(({ to, label, icon: Icon }) => {
              const active = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));
              return (
                <Link
                  key={to}
                  to={to}
                  className={clsx(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all',
                    active
                      ? 'bg-[rgba(41,121,255,0.15)] text-white'
                      : 'text-[var(--text-secondary)]'
                  )}
                >
                  <Icon size={13} />
                  {label}
                </Link>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--border)] py-4 text-center">
        <p className="text-[var(--text-muted)] text-xs">
          MatchIQ — Football Prediction Platform · Demo Data Only · Built with FastAPI + React + XGBoost
        </p>
      </footer>
    </div>
  );
}
