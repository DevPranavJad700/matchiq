import { clsx } from 'clsx';

// ─── Loading Skeleton ──────────────────────────────────────────────────────────

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={clsx('shimmer rounded-lg', className)} />
  );
}

// ─── Stat Card ────────────────────────────────────────────────────────────────

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon?: React.ReactNode;
  accent?: 'green' | 'blue' | 'amber' | 'red' | 'default';
}

const accentColors = {
  green: 'text-[#00e676]',
  blue: 'text-[#2979ff]',
  amber: 'text-[#ffc107]',
  red: 'text-[#ff4444]',
  default: 'text-white',
};

export function StatCard({ label, value, sub, icon, accent = 'default' }: StatCardProps) {
  return (
    <div className="glass-card p-4 flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className="text-[var(--text-secondary)] text-xs font-medium uppercase tracking-wider">{label}</span>
        {icon && <span className="text-[var(--text-muted)]">{icon}</span>}
      </div>
      <span className={clsx('text-2xl font-bold stat-number', accentColors[accent])}>{value}</span>
      {sub && <span className="text-[var(--text-muted)] text-xs">{sub}</span>}
    </div>
  );
}

// ─── Badge ────────────────────────────────────────────────────────────────────

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'win' | 'draw' | 'loss' | 'high' | 'medium' | 'low' | 'neutral';
}

export function Badge({ children, variant = 'neutral' }: BadgeProps) {
  const classes = {
    win: 'badge-win',
    draw: 'badge-draw',
    loss: 'badge-loss',
    high: 'badge-high',
    medium: 'badge-medium',
    low: 'badge-low',
    neutral: 'bg-[var(--navy-600)] text-[var(--text-secondary)]',
  };

  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold',
      classes[variant]
    )}>
      {children}
    </span>
  );
}

// ─── Form Dot ─────────────────────────────────────────────────────────────────

export function FormDot({ result }: { result: 'W' | 'D' | 'L' }) {
  const colors = {
    W: 'bg-[#00e676] shadow-[0_0_8px_rgba(0,230,118,0.5)]',
    D: 'bg-[#ffc107] shadow-[0_0_8px_rgba(255,193,7,0.5)]',
    L: 'bg-[#ff4444] shadow-[0_0_8px_rgba(255,68,68,0.5)]',
  };
  return (
    <div className={clsx('w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-black', colors[result])}>
      {result}
    </div>
  );
}

// ─── Error Banner ─────────────────────────────────────────────────────────────

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="glass-card border border-[#ff4444]/30 p-4 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <span className="text-[#ff4444] text-xl">⚠</span>
        <p className="text-[var(--text-secondary)] text-sm">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs text-[#2979ff] hover:text-white transition-colors border border-[#2979ff]/30 rounded px-3 py-1"
        >
          Retry
        </button>
      )}
    </div>
  );
}

// ─── Empty State ──────────────────────────────────────────────────────────────

export function EmptyState({ title, message, icon = '⚽' }: {
  title: string;
  message?: string;
  icon?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
      <span className="text-5xl">{icon}</span>
      <h3 className="text-[var(--text-primary)] font-semibold text-lg">{title}</h3>
      {message && <p className="text-[var(--text-secondary)] text-sm max-w-xs">{message}</p>}
    </div>
  );
}

// ─── Section Header ───────────────────────────────────────────────────────────

export function SectionHeader({ title, subtitle, right }: {
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h2 className="text-white font-bold text-xl">{title}</h2>
        {subtitle && <p className="text-[var(--text-secondary)] text-sm mt-0.5">{subtitle}</p>}
      </div>
      {right && <div>{right}</div>}
    </div>
  );
}

// ─── Loading Spinner ──────────────────────────────────────────────────────────

export function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' };
  return (
    <div className={clsx(
      'rounded-full border-2 border-[var(--navy-600)] border-t-[#2979ff] animate-spin',
      sizes[size]
    )} />
  );
}

// ─── Page Loader ──────────────────────────────────────────────────────────────

export function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-64">
      <div className="flex flex-col items-center gap-3">
        <Spinner size="lg" />
        <p className="text-[var(--text-secondary)] text-sm">Loading...</p>
      </div>
    </div>
  );
}
