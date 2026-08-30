import { Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Home, Zap, Users, Calendar, TrendingUp } from 'lucide-react';
import { clsx } from 'clsx';
import api from '../services/api';

const navItems = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/predict', label: 'Predictor', icon: Zap },
  { to: '/teams', label: 'Teams', icon: Users },
  { to: '/matches', label: 'Matches', icon: Calendar },
  { to: '/analytics', label: 'Analytics', icon: TrendingUp },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30000,
  });

  const isModelActive = health?.model_loaded ?? false;

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-base)' }}>
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[#0B0D0F]/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 group">
              <div className="w-2.5 h-2.5 rounded-full bg-[#54C878]" />
              <span className="font-extrabold text-xl tracking-tight text-[#F4F5F2]">
                Match<span className="text-[#54C878]">IQ</span>
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
                      'flex items-center gap-2 px-3.5 py-2 rounded-md text-sm font-medium transition-colors relative',
                      active
                        ? 'text-[#F4F5F2] bg-[#171B1F]'
                        : 'text-[#9DA4AA] hover:text-[#F4F5F2] hover:bg-[#111417]'
                    )}
                  >
                    <Icon size={15} className={clsx(active ? 'text-[#54C878]' : 'text-[#5C636A]')} />
                    {label}
                    {active && (
                      <span className="absolute bottom-0 left-3.5 right-3.5 h-[2px] bg-[#54C878] rounded-full" />
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* Product Status Indicator */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-md border border-[var(--border)] bg-[#111417]">
              <div className={clsx('w-1.5 h-1.5 rounded-full', isModelActive ? 'bg-[#54C878]' : 'bg-[#F59E0B]')} />
              <span className="text-xs font-semibold text-[#9DA4AA]">
                {isModelActive ? 'Model Engine Active' : 'Model Engine Offline'}
              </span>
            </div>
          </div>
        </div>

        {/* Mobile nav */}
        <div className="md:hidden border-t border-[var(--border)] bg-[#111417]">
          <div className="flex overflow-x-auto px-4 py-2 gap-1 no-scrollbar">
            {navItems.map(({ to, label, icon: Icon }) => {
              const active = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));
              return (
                <Link
                  key={to}
                  to={to}
                  className={clsx(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold whitespace-nowrap transition-colors',
                    active
                      ? 'bg-[#171B1F] text-[#F4F5F2] border-b-2 border-[#54C878]'
                      : 'text-[#9DA4AA]'
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
      <footer className="border-t border-[var(--border)] py-6 text-center bg-[#111417]">
        <p className="text-[#5C636A] text-xs font-medium">
          MatchIQ · Football intelligence, simplified · Data through 2025–26 season · Powered by Calibrated Logistic Regression & Dixon-Coles Goal Engine
        </p>
      </footer>
    </div>
  );
}
