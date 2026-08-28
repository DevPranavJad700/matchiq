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
    { name: homeTeam, value: Math.round(probabilities.home_win * 100), fill: '#2979ff', glow: 'rgba(41,121,255,0.4)' },
    { name: 'Draw', value: Math.round(probabilities.draw * 100), fill: '#ffc107', glow: 'rgba(255,193,7,0.4)' },
    { name: awayTeam, value: Math.round(probabilities.away_win * 100), fill: '#ff4444', glow: 'rgba(255,68,68,0.4)' },
  ];

  return (
    <div className="flex flex-col gap-4 py-2">
      {/* Bar visualization */}
      {data.map((item) => (
        <div key={item.name} className="flex items-center gap-3 group">
          <span className="text-xs font-bold text-[var(--text-secondary)] w-28 shrink-0 truncate text-right">{item.name}</span>
          <div className="flex-1 bg-[var(--navy-800)] rounded-full h-3.5 overflow-hidden p-0.5 border border-[var(--border)]">
            <div
              className="h-full rounded-full transition-all duration-1000 cubic-bezier(0.16, 1, 0.3, 1)"
              style={{
                width: `${item.value}%`,
                background: `linear-gradient(90deg, ${item.fill}, ${item.fill}dd)`,
                boxShadow: `0 0 16px ${item.glow}`,
              }}
            />
          </div>
          <span className="text-sm font-black w-12 text-right stat-number" style={{ color: item.fill }}>
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
    <div className="glass-card p-6 shadow-2xl relative overflow-hidden border border-[#2979ff]/30">
      {/* Top accent glow line */}
      <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-[#2979ff] via-[#7c3aed] to-[#00e676]" />

      {/* Teams row */}
      <div className="flex items-center justify-between mb-6">
        <TeamBadge name={home_team.name} short={home_team.short_name} side="home" />
        <div className="flex flex-col items-center gap-1.5">
          <div className="w-9 h-9 rounded-full bg-[var(--navy-800)] border border-[var(--border)] flex items-center justify-center shadow-inner">
            <span className="text-[var(--text-secondary)] text-xs font-black uppercase tracking-widest">VS</span>
          </div>
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
        <div className="mt-6 pt-5 border-t border-[var(--border)] flex items-center justify-between">
          <div>
            <p className="text-[var(--text-secondary)] text-xs font-bold uppercase tracking-wider">Predicted Match Outcome</p>
            <p className="text-white font-extrabold text-xl mt-0.5">
              <span className="gradient-text">{resultLabels[predicted_result]} — {Math.round(maxProb * 100)}%</span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-[var(--text-muted)] text-xs font-medium">Model Engine</p>
            <p className="text-[#60a5fa] text-xs font-bold mt-0.5">{prediction.model_version || 'XGBoost v1.2'}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function TeamBadge({ name, short, side }: { name: string; short: string | null; side: 'home' | 'away' }) {
  const color = side === 'home' ? '#2979ff' : '#ff4444';
  return (
    <div className={clsx('flex flex-col items-center gap-2.5', side === 'away' && 'items-center')}>
      <div
        className="w-16 h-16 rounded-2xl flex items-center justify-center text-white font-extrabold text-base shadow-lg transition-transform duration-300 hover:scale-110"
        style={{
          background: `linear-gradient(135deg, ${color}44, ${color}11)`,
          border: `2px solid ${color}60`,
          boxShadow: `0 0 20px ${color}30`,
        }}
      >
        {short || name.slice(0, 3).toUpperCase()}
      </div>
      <span className="text-white font-bold text-sm text-center max-w-[110px] leading-tight">{name}</span>
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
    <div className="flex flex-col gap-3.5">
      {sorted.map((factor) => {
        const isPositive = factor.impact > 0;
        const pct = maxAbs > 0 ? (Math.abs(factor.impact) / maxAbs) * 100 : 0;
        const color = isPositive ? '#00e676' : '#ff4444';
        const label = factor.feature.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());

        return (
          <div key={factor.feature} className="group p-2 rounded-xl hover:bg-[var(--glass-hover)] transition-colors">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold text-[var(--text-primary)] truncate max-w-[220px]" title={label}>
                {label}
              </span>
              <span className="text-xs font-mono font-bold ml-2 px-2 py-0.5 rounded bg-[var(--navy-800)] border border-[var(--border)]" style={{ color }}>
                {isPositive ? '+' : ''}{factor.impact.toFixed(3)}
              </span>
            </div>
            <div className="flex items-center gap-2.5">
              <div className="w-4 shrink-0 flex justify-center">
                <span style={{ color }} className="text-xs font-black">{isPositive ? '▲' : '▼'}</span>
              </div>
              <div className="flex-1 bg-[var(--navy-800)] rounded-full h-2.5 overflow-hidden p-0.5 border border-[var(--border)]">
                <div
                  className="h-full rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${pct}%`, background: color, boxShadow: `0 0 10px ${color}80` }}
                />
              </div>
            </div>
            <p className="text-[var(--text-secondary)] text-xs mt-1.5 leading-relaxed font-medium hidden group-hover:block animate-fade-in">
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

  return (
    <Link
      to={`/matches/${match.id}`}
      className="glass-card p-4 flex items-center gap-4 hover:border-[#2979ff]/40 transition-all group duration-300"
    >
      <div className="flex-1 flex items-center gap-2">
        <span className="text-sm font-bold text-white truncate group-hover:text-[#60a5fa] transition-colors">{match.home_team.name}</span>
      </div>
      <div className="flex flex-col items-center gap-1 shrink-0">
        {played ? (
          <span className="text-white font-extrabold text-lg stat-number bg-[var(--navy-800)] px-3 py-0.5 rounded-lg border border-[var(--border)]">
            {match.home_score} – {match.away_score}
          </span>
        ) : (
          <span className="text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider">VS</span>
        )}
        {played && (
          <Badge variant={match.result === 'H' ? 'win' : match.result === 'A' ? 'loss' : 'draw'}>
            {resultLabel}
          </Badge>
        )}
      </div>
      <div className="flex-1 flex items-center justify-end gap-2">
        <span className="text-sm font-bold text-white truncate text-right group-hover:text-[#60a5fa] transition-colors">{match.away_team.name}</span>
      </div>
    </Link>
  );
}
