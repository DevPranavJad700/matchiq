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
    { name: homeTeam, value: Math.round(probabilities.home_win * 100), fill: '#54C878' },
    { name: 'Draw', value: Math.round(probabilities.draw * 100), fill: '#F59E0B' },
    { name: awayTeam, value: Math.round(probabilities.away_win * 100), fill: '#EF4444' },
  ];

  return (
    <div className="flex flex-col gap-3 py-2">
      {/* Bar visualization */}
      {data.map((item) => (
        <div key={item.name} className="flex items-center gap-3">
          <span className="text-xs font-semibold text-[#9DA4AA] w-28 shrink-0 truncate text-right">{item.name}</span>
          <div className="flex-1 bg-[#171B1F] rounded-md h-2.5 overflow-hidden border border-[var(--border)]">
            <div
              className="h-full rounded-md transition-all duration-500 ease-out"
              style={{
                width: `${item.value}%`,
                background: item.fill,
              }}
            />
          </div>
          <span className="text-sm font-bold w-12 text-right stat-number" style={{ color: item.fill }}>
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
        <div className="flex flex-col items-center gap-1.5">
          <span className="text-[#5C636A] text-xs font-bold uppercase tracking-widest">vs</span>
          <Badge variant={confidenceBadge[confidence as keyof typeof confidenceBadge] || 'neutral'}>
            {confidence} confidence
          </Badge>
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
        <div className="mt-5 pt-4 border-t border-[var(--border)] flex items-center justify-between">
          <div>
            <p className="text-[#9DA4AA] text-xs font-semibold uppercase tracking-wider">Predicted Match Outcome</p>
            <p className="text-[#F4F5F2] font-bold text-lg mt-0.5">
              <span>{resultLabels[predicted_result]} — {Math.round(maxProb * 100)}%</span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-[#5C636A] text-xs font-medium">Model Engine</p>
            <p className="text-[#9DA4AA] text-xs font-semibold mt-0.5">{prediction.model_version || 'XGBoost v1.2'}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function TeamBadge({ name, short, side }: { name: string; short: string | null; side: 'home' | 'away' }) {
  const isHome = side === 'home';
  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={clsx(
          'w-14 h-14 rounded-xl flex items-center justify-center font-bold text-sm border',
          isHome ? 'bg-[#171B1F] text-[#F4F5F2] border-[var(--border-strong)]' : 'bg-[#171B1F] text-[#9DA4AA] border-[var(--border)]'
        )}
      >
        {short || name.slice(0, 3).toUpperCase()}
      </div>
      <span className="text-[#F4F5F2] font-semibold text-sm text-center max-w-[110px] leading-tight">{name}</span>
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
      <p className="text-[#5C636A] text-sm">No explanation data available</p>
    );
  }

  const sorted = [...factors].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact)).slice(0, 8);
  const maxAbs = Math.max(...sorted.map((f) => Math.abs(f.impact)), 0.001);

  return (
    <div className="flex flex-col gap-3">
      {sorted.map((factor) => {
        const isPositive = factor.impact >= 0;
        const pct = Math.min(100, Math.max(8, (Math.abs(factor.impact) / maxAbs) * 100));
        const color = isPositive ? '#54C878' : '#EF4444';
        const label = factor.feature.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());

        return (
          <div key={factor.feature} className="py-1 border-b border-[var(--border)] last:border-b-0">
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-sm font-semibold text-[#F4F5F2] truncate max-w-[240px]" title={factor.description}>
                {label}
              </span>
              <span className="text-xs font-mono font-bold" style={{ color }}>
                {isPositive ? '+' : ''}{factor.impact.toFixed(3)}
              </span>
            </div>
            {factor.description && (
              <p className="text-[11px] text-[#9DA4AA] leading-snug mb-1.5" title={factor.description}>
                {factor.description}
              </p>
            )}
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-[#171B1F] rounded-full h-2 overflow-hidden border border-[var(--border)]">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{ width: `${pct}%`, background: color }}
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Form Strip ───────────────────────────────────────────────────────────────

export function FormStrip({ results }: { results: ('W' | 'D' | 'L')[] }) {
  return (
    <div className="flex gap-1.5">
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
  const is2026_27 = match.season_id === 32 || (match.match_date && match.match_date.startsWith('2026')) || (match.match_date && match.match_date.startsWith('2027'));

  return (
    <Link
      to={`/matches/${match.id}`}
      className="glass-card p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[#171B1F] border border-[var(--border)] transition-colors group"
    >
      <div className="flex items-center gap-2 sm:w-28 shrink-0">
        {match.matchday && (
          <span className="px-2 py-0.5 rounded bg-[#171B1F] text-[11px] font-bold text-[#54C878] border border-[var(--border)]">
            MW {match.matchday}
          </span>
        )}
        {is2026_27 && (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#3B82F6]/15 text-[#3B82F6] border border-[#3B82F6]/30 hidden sm:inline">
            AI Pred
          </span>
        )}
      </div>

      <div className="flex-1 flex items-center justify-between sm:justify-center gap-4">
        <div className="flex-1 text-left sm:text-right">
          <span className="text-sm font-bold text-[#F4F5F2] group-hover:text-[#54C878] transition-colors truncate">
            {match.home_team.name}
          </span>
        </div>

        <div className="flex flex-col items-center gap-0.5 shrink-0 px-2">
          {played ? (
            <span className="text-[#F4F5F2] font-extrabold text-base stat-number">
              {match.home_score} – {match.away_score}
            </span>
          ) : (
            <span className="text-[#5C636A] text-xs font-bold uppercase tracking-wider">VS</span>
          )}
          {played && (
            <Badge variant={match.result === 'H' ? 'win' : match.result === 'A' ? 'loss' : 'draw'}>
              {resultLabel}
            </Badge>
          )}
        </div>

        <div className="flex-1 text-right sm:text-left">
          <span className="text-sm font-bold text-[#F4F5F2] group-hover:text-[#54C878] transition-colors truncate">
            {match.away_team.name}
          </span>
        </div>
      </div>

      <div className="text-right sm:w-28 shrink-0">
        <span className="text-[11px] text-[#9DA4AA] font-mono">
          {match.match_date ? new Date(match.match_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : ''}
        </span>
      </div>
    </Link>
  );
}
