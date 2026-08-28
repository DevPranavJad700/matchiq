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
  green: 'text-[#54C878]',
  blue: 'text-[#3B82F6]',
  amber: 'text-[#F59E0B]',
  red: 'text-[#EF4444]',
  default: 'text-[#F4F5F2]',
};

export function StatCard({ label, value, sub, icon, accent = 'default' }: StatCardProps) {
  return (
    <div className="glass-card p-4 flex flex-col justify-between">
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[#9DA4AA] text-xs font-semibold uppercase tracking-wider">{label}</span>
        {icon && <span className="text-[#5C636A]">{icon}</span>}
      </div>
      <div className="flex items-baseline gap-2">
        <span className={clsx('text-2xl font-bold stat-number tracking-tight', accentColors[accent])}>{value}</span>
      </div>
      {sub && <span className="text-[#5C636A] text-xs mt-1 font-medium">{sub}</span>}
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
    neutral: 'bg-[#171B1F] text-[#9DA4AA] border border-[var(--border)]',
  };

  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold tracking-wide',
      classes[variant]
    )}>
      {children}
    </span>
  );
}

// ─── Form Dot ─────────────────────────────────────────────────────────────────

export function FormDot({ result }: { result: 'W' | 'D' | 'L' }) {
  const colors = {
    W: 'bg-[#54C878] text-[#0B0D0F]',
    D: 'bg-[#F59E0B] text-[#0B0D0F]',
    L: 'bg-[#EF4444] text-[#F4F5F2]',
  };
  return (
    <div className={clsx('w-6 h-6 rounded flex items-center justify-center text-xs font-bold shrink-0', colors[result])}>
      {result}
    </div>
  );
}

// ─── Error Banner ─────────────────────────────────────────────────────────────

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="glass-card border border-[#EF4444]/30 p-4 flex items-center justify-between gap-4 bg-[#EF4444]/05">
      <div className="flex items-center gap-3">
        <span className="text-[#EF4444] text-base font-bold">⚠</span>
        <p className="text-[#9DA4AA] text-sm font-medium">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs text-[#F4F5F2] hover:text-[#54C878] font-semibold transition-colors border border-[var(--border)] rounded-md px-3 py-1.5 bg-[#171B1F]"
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
    <div className="flex flex-col items-center justify-center py-16 gap-2 text-center animate-fade-in">
      <span className="text-4xl mb-1">{icon}</span>
      <h3 className="text-[#F4F5F2] font-bold text-lg">{title}</h3>
      {message && <p className="text-[#9DA4AA] text-sm max-w-sm">{message}</p>}
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
    <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 mb-4">
      <div>
        <h2 className="text-[#F4F5F2] font-bold text-xl tracking-tight">
          {title}
        </h2>
        {subtitle && <p className="text-[#9DA4AA] text-sm font-normal mt-0.5">{subtitle}</p>}
      </div>
      {right && <div className="self-start sm:self-auto">{right}</div>}
    </div>
  );
}

// ─── Loading Spinner ──────────────────────────────────────────────────────────

export function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = { sm: 'w-4 h-4 border-2', md: 'w-6 h-6 border-2', lg: 'w-10 h-10 border-3' };
  return (
    <div className={clsx(
      'rounded-full border-[var(--border-strong)] border-t-[#54C878] animate-spin',
      sizes[size]
    )} />
  );
}

// ─── Page Loader ──────────────────────────────────────────────────────────────

export function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-64 animate-fade-in">
      <div className="flex flex-col items-center gap-3">
        <Spinner size="lg" />
        <p className="text-[#9DA4AA] text-sm font-medium">Loading match data...</p>
      </div>
    </div>
  );
}
