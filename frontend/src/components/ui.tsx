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
  const iconBgs = {
    green: 'bg-[#00e676]/10 text-[#00e676] border-[#00e676]/20',
    blue: 'bg-[#2979ff]/10 text-[#2979ff] border-[#2979ff]/20',
    amber: 'bg-[#ffc107]/10 text-[#ffc107] border-[#ffc107]/20',
    red: 'bg-[#ff4444]/10 text-[#ff4444] border-[#ff4444]/20',
    default: 'bg-[var(--navy-600)]/30 text-white border-white/10',
  };

  return (
    <div className="glass-card p-5 flex flex-col gap-2 relative overflow-hidden group">
      <div className="flex items-center justify-between z-10">
        <span className="text-[var(--text-secondary)] text-xs font-bold uppercase tracking-wider">{label}</span>
        {icon && (
          <div className={clsx('w-8 h-8 rounded-xl flex items-center justify-center border transition-transform duration-300 group-hover:scale-110', iconBgs[accent])}>
            {icon}
          </div>
        )}
      </div>
      <div className="flex items-baseline gap-2 z-10">
        <span className={clsx('text-3xl font-extrabold stat-number tracking-tight', accentColors[accent])}>{value}</span>
      </div>
      {sub && <span className="text-[var(--text-muted)] text-xs font-medium z-10">{sub}</span>}
      
      {/* Decorative gradient glow on hover */}
      <div className="absolute -right-6 -bottom-6 w-20 h-20 rounded-full bg-gradient-to-br from-[#2979ff]/10 to-transparent blur-xl group-hover:scale-150 transition-transform duration-500 pointer-events-none" />
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
    win: 'badge-win shadow-[0_0_10px_rgba(0,230,118,0.2)]',
    draw: 'badge-draw shadow-[0_0_10px_rgba(255,193,7,0.2)]',
    loss: 'badge-loss shadow-[0_0_10px_rgba(255,68,68,0.2)]',
    high: 'badge-high shadow-[0_0_10px_rgba(0,230,118,0.2)]',
    medium: 'badge-medium shadow-[0_0_10px_rgba(255,193,7,0.2)]',
    low: 'badge-low shadow-[0_0_10px_rgba(255,68,68,0.2)]',
    neutral: 'bg-[var(--navy-700)] text-[var(--text-secondary)] border border-[var(--border)]',
  };

  return (
    <span className={clsx(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold tracking-wide transition-all duration-200 hover:scale-105',
      classes[variant]
    )}>
      {children}
    </span>
  );
}

// ─── Form Dot ─────────────────────────────────────────────────────────────────

export function FormDot({ result }: { result: 'W' | 'D' | 'L' }) {
  const colors = {
    W: 'bg-[#00e676] text-black shadow-[0_0_12px_rgba(0,230,118,0.6)]',
    D: 'bg-[#ffc107] text-black shadow-[0_0_12px_rgba(255,193,7,0.6)]',
    L: 'bg-[#ff4444] text-white shadow-[0_0_12px_rgba(255,68,68,0.6)]',
  };
  return (
    <div className={clsx('w-7 h-7 rounded-full flex items-center justify-center text-xs font-black transition-transform duration-200 hover:scale-115 cursor-default', colors[result])}>
      {result}
    </div>
  );
}

// ─── Error Banner ─────────────────────────────────────────────────────────────

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="glass-card border border-[#ff4444]/40 p-4 flex items-center justify-between gap-4 bg-[rgba(255,68,68,0.05)]">
      <div className="flex items-center gap-3">
        <span className="text-[#ff4444] text-xl animate-bounce">⚠</span>
        <p className="text-[var(--text-secondary)] text-sm font-medium">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs text-[#2979ff] hover:text-white font-semibold transition-all border border-[#2979ff]/40 rounded-xl px-4 py-1.5 hover:bg-[#2979ff]/20"
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
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center animate-fade-in">
      <span className="text-5xl animate-float">{icon}</span>
      <h3 className="text-[var(--text-primary)] font-bold text-xl">{title}</h3>
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
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
      <div>
        <h2 className="text-white font-extrabold text-2xl tracking-tight flex items-center gap-2">
          {title}
        </h2>
        {subtitle && <p className="text-[var(--text-secondary)] text-sm font-medium mt-0.5">{subtitle}</p>}
      </div>
      {right && <div className="self-start sm:self-auto">{right}</div>}
    </div>
  );
}

// ─── Loading Spinner ──────────────────────────────────────────────────────────

export function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = { sm: 'w-4 h-4 border-2', md: 'w-8 h-8 border-3', lg: 'w-12 h-12 border-4' };
  return (
    <div className={clsx(
      'rounded-full border-[var(--navy-600)] border-t-[#2979ff] border-r-[#7c3aed] animate-spin shadow-[0_0_16px_rgba(41,121,255,0.4)]',
      sizes[size]
    )} />
  );
}

// ─── Page Loader ──────────────────────────────────────────────────────────────

export function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-64 animate-fade-in">
      <div className="flex flex-col items-center gap-4">
        <Spinner size="lg" />
        <p className="text-[var(--text-secondary)] text-sm font-semibold tracking-wide">Loading MatchIQ Insights...</p>
      </div>
    </div>
  );
}
