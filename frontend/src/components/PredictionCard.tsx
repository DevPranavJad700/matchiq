// recharts not needed for this component — using CSS bars for probability display
import { clsx } from 'clsx';
import type { Prediction, ExplanationFactor } from '../types';
import { Badge, FormDot } from './ui';

// ─── Probability Chart (Visual Half-circle bars) ───────────────────────────────

interface ProbabilityChartProps {
  probabilities: { home_win: number; draw: number; away_win: number };
  homeTeam: string;
  awayTeam: string;
}

export function ProbabilityChart({ probabilities, homeTeam, awayTeam }: ProbabilityChartProps) {
  const data = [
    { name: homeTeam, value: Math.round(probabilities.home_win * 100), fill: '#2979ff' },
    { name: 'Draw', value: Math.round(probabilities.draw * 100), fill: '#ffc107' },
    { name: awayTeam, value: Math.round(probabilities.away_win * 100), fill: '#ff4444' },
  ];

  return (
    <div className="flex flex-col gap-4">
      {/* Bar visualization */}
      {data.map((item) => (
        <div key={item.name} className="flex items-center gap-3">
          <span className="text-xs text-[var(--text-secondary)] w-28 shrink-0 truncate text-right">{item.name}</span>
          <div className="flex-1 bg-[var(--navy-700)] rounded-full h-3 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{
                width: `${item.value}%`,
                background: item.fill,
                boxShadow: `0 0 12px ${item.fill}60`,
              }}
            />
          </div>
          <span className="text-sm font-bold w-10 stat-number" style={{ color: item.fill }}>
            {item.value}%
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── Prediction Card (Full result card) ───────────────────────────────────────

interface PredictionCardProps {
  prediction: Prediction;
  compact?: boolean;
}

const resultLabels = {
  HOME_WIN: 'Home Win',
  DRAW: 'Draw',
  AWAY_WIN: 'Away Win',
};

const confidenceBadge = {
  HIGH: 'high' as const,
  MEDIUM: 'medium' as const,
  LOW: 'low' as const,
};

export function PredictionCard({ prediction, compact = false }: PredictionCardProps) {
  const { home_team, away_team, probabilities, predicted_result, confidence } = prediction;
  const maxProb = Math.max(probabilities.home_win, probabilities.draw, probabilities.away_win);

  return (
    <div className="glass-card p-6">
      {/* Teams row */}
      <div className="flex items-center justify-between mb-6">
        <TeamBadge name={home_team.name} short={home_team.short_name} side="home" />
        <div className="flex flex-col items-center gap-1">
          <span className="text-[var(--text-muted)] text-xs font-medium uppercase tracking-widest">vs</span>
          <div className="flex items-center gap-2">
            <Badge variant={confidenceBadge[confidence as keyof typeof confidenceBadge] || 'neutral'}>
              {confidence} confidence
            </Badge>
          </div>
        </div>
        <TeamBadge name={away_team.name} short={away_team.short_name} side="away" />
      </div>

      {/* Probability bars */}
      <ProbabilityChart
        probabilities={probabilities}
        homeTeam={home_team.name}
        awayTeam={away_team.name}
      />

      {/* Verdict */}
      {!compact && (
        <div className="mt-5 pt-5 border-t border-[var(--border)] flex items-center justify-between">
          <div>
            <p className="text-[var(--text-secondary)] text-xs uppercase tracking-wider">Predicted outcome</p>
            <p className="text-white font-bold text-lg mt-0.5">
              {resultLabels[predicted_result]} — {Math.round(maxProb * 100)}%
            </p>
          </div>
          <div className="text-right">
            <p className="text-[var(--text-muted)] text-xs">Model</p>
            <p className="text-[var(--text-secondary)] text-xs mt-0.5">{prediction.model_version || '—'}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function TeamBadge({ name, short, side }: { name: string; short: string | null; side: 'home' | 'away' }) {
  const color = side === 'home' ? '#2979ff' : '#ff4444';
  return (
    <div className={clsx('flex flex-col items-center gap-2', side === 'away' && 'items-center')}>
      <div
        className="w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-sm"
        style={{ background: `linear-gradient(135deg, ${color}33, ${color}11)`, border: `2px solid ${color}40` }}
      >
        {short || name.slice(0, 3).toUpperCase()}
      </div>
      <span className="text-white font-semibold text-sm text-center max-w-[100px] leading-tight">{name}</span>
    </div>
  );
}

// ─── SHAP Explanation Chart ────────────────────────────────────────────────────

interface ShapChartProps {
  factors: ExplanationFactor[];
}

export function ShapExplanationChart({ factors }: ShapChartProps) {
  if (factors.length === 0) {
    return (
      <p className="text-[var(--text-muted)] text-sm">No explanation data available</p>
    );
  }

  const sorted = [...factors].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact)).slice(0, 8);
  const maxAbs = Math.max(...sorted.map((f) => Math.abs(f.impact)));

  return (
    <div className="flex flex-col gap-3">
      {sorted.map((factor) => {
        const isPositive = factor.impact > 0;
        const pct = maxAbs > 0 ? (Math.abs(factor.impact) / maxAbs) * 100 : 0;
        const color = isPositive ? '#2979ff' : '#ff4444';
        const label = factor.feature.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());

        return (
          <div key={factor.feature} className="group">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-[var(--text-secondary)] truncate max-w-[200px]" title={label}>
                {label}
              </span>
              <span className="text-xs font-mono ml-2" style={{ color }}>
                {isPositive ? '+' : ''}{factor.impact.toFixed(3)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {/* Direction indicator */}
              <div className="w-4 shrink-0 flex justify-center">
                <span style={{ color }} className="text-xs">{isPositive ? '▲' : '▼'}</span>
              </div>
              <div className="flex-1 bg-[var(--navy-700)] rounded-full h-2 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${pct}%`, background: color, boxShadow: `0 0 8px ${color}60` }}
                />
              </div>
            </div>
            {/* Tooltip description */}
            <p className="text-[var(--text-muted)] text-xs mt-1 leading-relaxed opacity-0 group-hover:opacity-100 transition-opacity">
              {factor.description}
            </p>
          </div>
        );
      })}
    </div>
  );
}

// ─── Form Chart ───────────────────────────────────────────────────────────────

export function FormStrip({ results }: { results: ('W' | 'D' | 'L')[] }) {
  return (
    <div className="flex gap-1">
      {results.map((r, i) => (
        <FormDot key={i} result={r} />
      ))}
    </div>
  );
}

// ─── Match Card (List item) ───────────────────────────────────────────────────

import { Link } from 'react-router-dom';
import type { MatchListItem } from '../types';

export function MatchCard({ match }: { match: MatchListItem }) {
  const played = match.result !== null;
  const resultLabel = match.result === 'H' ? 'Home Win' : match.result === 'A' ? 'Away Win' : 'Draw';

  return (
    <Link
      to={`/matches/${match.id}`}
      className="glass-card p-4 flex items-center gap-4 hover:border-[var(--navy-500)] transition-all group"
    >
      <div className="flex-1 flex items-center gap-2">
        <span className="text-sm font-medium text-white truncate">{match.home_team.name}</span>
      </div>
      <div className="flex flex-col items-center gap-0.5 shrink-0">
        {played ? (
          <span className="text-white font-bold text-lg stat-number">
            {match.home_score} – {match.away_score}
          </span>
        ) : (
          <span className="text-[var(--text-muted)] text-sm">vs</span>
        )}
        {played && (
          <Badge variant={match.result === 'H' ? 'win' : match.result === 'A' ? 'loss' : 'draw'}>
            {resultLabel}
          </Badge>
        )}
      </div>
      <div className="flex-1 flex items-center justify-end gap-2">
        <span className="text-sm font-medium text-white truncate text-right">{match.away_team.name}</span>
      </div>
    </Link>
  );
}
