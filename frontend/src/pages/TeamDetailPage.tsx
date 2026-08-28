import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Zap } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import api from '../services/api';
import { PageLoader, ErrorBanner, StatCard, SectionHeader } from '../components/ui';
import { FormStrip } from '../components/PredictionCard';

export function TeamDetailPage() {
  const { id } = useParams<{ id: string }>();
  const teamId = parseInt(id ?? '0');

  const { data: team, isLoading: teamLoading, error: teamError } = useQuery({
    queryKey: ['team', teamId],
    queryFn: () => api.getTeam(teamId),
    enabled: !!teamId,
  });

  const { data: form } = useQuery({
    queryKey: ['team-form', teamId],
    queryFn: () => api.getTeamForm(teamId, 10),
    enabled: !!teamId,
  });

  const { data: stats } = useQuery({
    queryKey: ['team-stats', teamId],
    queryFn: () => api.getTeamStatistics(teamId),
    enabled: !!teamId,
  });

  const { data: matches } = useQuery({
    queryKey: ['matches', { team_id: teamId }],
    queryFn: () => api.getMatches({ team_id: teamId, page_size: 20 }),
    enabled: !!teamId,
  });

  if (teamLoading) return <PageLoader />;
  if (teamError || !team) return <ErrorBanner message="Team not found" />;

  const recentResults = form?.recent_results.map((r) => r.result as 'W' | 'D' | 'L').slice(0, 5) ?? [];

  // Goal trend chart data
  const goalTrend = form?.recent_results.slice(0, 10).reverse().map((r, i) => ({
    match: i + 1,
    scored: r.goals_scored ?? 0,
    conceded: r.goals_conceded ?? 0,
    opponent: r.opponent,
  })) ?? [];

  return (
    <div className="space-y-6">
      {/* Back + header */}
      <div>
        <Link to="/teams" className="flex items-center gap-1 text-[var(--text-muted)] hover:text-white text-sm mb-4 transition-colors">
          <ArrowLeft size={14} /> Back to Teams
        </Link>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-[var(--navy-700)] border border-[var(--border)] flex items-center justify-center text-xl font-bold text-white">
              {team.short_name || team.name.slice(0, 3).toUpperCase()}
            </div>
            <div>
              <h1 className="text-3xl font-black text-white">{team.name}</h1>
              <p className="text-[var(--text-secondary)] text-sm mt-0.5">
                {team.country} · {stats?.season_year ?? '2023-24'}
              </p>
            </div>
          </div>
          <Link
            to={`/predict`}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#2979ff]/15 border border-[#2979ff]/30 text-[#2979ff] hover:bg-[#2979ff]/25 transition-all text-sm font-medium"
          >
            <Zap size={14} />
            Predict with {team.short_name || team.name}
          </Link>
        </div>
      </div>

      {/* Standing stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          <StatCard label="Position" value={stats.position ?? '—'} accent="blue" />
          <StatCard label="Points" value={stats.points ?? '—'} accent="green" />
          <StatCard label="Played" value={stats.played ?? '—'} />
          <StatCard label="Won" value={stats.won ?? '—'} accent="green" />
          <StatCard label="Drawn" value={stats.drawn ?? '—'} accent="amber" />
          <StatCard label="Lost" value={stats.lost ?? '—'} accent="red" />
          <StatCard label="GD" value={stats.goal_difference ?? '—'} accent={stats.goal_difference && stats.goal_difference > 0 ? 'green' : 'red'} />
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Form */}
        <div className="glass-card p-5">
          <SectionHeader title="Recent Form" subtitle="Last 5 matches" />
          <div className="flex gap-2 mb-6">
            <FormStrip results={recentResults} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center glass-card p-3">
              <p className="text-2xl font-black text-[#00e676] stat-number">{form?.wins_last_5 ?? 0}</p>
              <p className="text-[var(--text-muted)] text-xs mt-1">Wins</p>
            </div>
            <div className="text-center glass-card p-3">
              <p className="text-2xl font-black text-[#ffc107] stat-number">{form?.draws_last_5 ?? 0}</p>
              <p className="text-[var(--text-muted)] text-xs mt-1">Draws</p>
            </div>
            <div className="text-center glass-card p-3">
              <p className="text-2xl font-black text-[#ff4444] stat-number">{form?.losses_last_5 ?? 0}</p>
              <p className="text-[var(--text-muted)] text-xs mt-1">Losses</p>
            </div>
          </div>
        </div>

        {/* Attack/defence stats */}
        {stats && (
          <div className="glass-card p-5">
            <SectionHeader title="Performance Stats" subtitle="Season averages" />
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Avg Goals" value={stats.avg_goals_scored?.toFixed(2) ?? '—'} accent="green" />
              <StatCard label="Avg Conceded" value={stats.avg_goals_conceded?.toFixed(2) ?? '—'} accent="red" />
              <StatCard label="Avg Shots" value={stats.avg_shots?.toFixed(1) ?? '—'} />
              <StatCard label="Avg SOT" value={stats.avg_shots_on_target?.toFixed(1) ?? '—'} />
              {stats.avg_xg != null && (
                <StatCard label="Avg xG" value={stats.avg_xg.toFixed(2)} accent="blue" />
              )}
              <StatCard label="Home Win Rate" value={stats.home_win_rate != null ? `${Math.round(stats.home_win_rate * 100)}%` : '—'} accent="green" />
              <StatCard label="Away Win Rate" value={stats.away_win_rate != null ? `${Math.round(stats.away_win_rate * 100)}%` : '—'} />
            </div>
          </div>
        )}
      </div>

      {/* Goals trend chart */}
      {goalTrend.length > 0 && (
        <div className="glass-card p-5">
          <SectionHeader title="Goals Trend" subtitle="Last 10 matches" />
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={goalTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="match" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: 'var(--navy-800)', border: '1px solid var(--border)', borderRadius: 8 }}
                labelStyle={{ color: 'var(--text-secondary)' }}
              />
              <Line type="monotone" dataKey="scored" stroke="#00e676" strokeWidth={2} dot={{ r: 4, fill: '#00e676' }} name="Goals Scored" />
              <Line type="monotone" dataKey="conceded" stroke="#ff4444" strokeWidth={2} dot={{ r: 4, fill: '#ff4444' }} name="Conceded" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent matches */}
      {matches && matches.items.length > 0 && (
        <div className="glass-card p-5">
          <SectionHeader title="Match History" />
          <div className="space-y-2">
            {matches.items.map((m) => {
              const isHome = m.home_team.id === teamId;
              const opponent = isHome ? m.away_team : m.home_team;
              const teamScore = isHome ? m.home_score : m.away_score;
              const oppScore = isHome ? m.away_score : m.home_score;
              const win = (isHome && m.result === 'H') || (!isHome && m.result === 'A');
              const draw = m.result === 'D';
              const resultColor = win ? '#00e676' : draw ? '#ffc107' : '#ff4444';
              const resultLabel = win ? 'W' : draw ? 'D' : 'L';

              return (
                <Link key={m.id} to={`/matches/${m.id}`} className="flex items-center gap-4 py-2 px-3 rounded-lg hover:bg-[var(--glass-hover)] transition-colors">
                  <span className="w-6 h-6 rounded text-xs font-bold flex items-center justify-center" style={{ color: resultColor, background: `${resultColor}20` }}>{resultLabel}</span>
                  <span className="text-[var(--text-muted)] text-xs w-5">{isHome ? 'H' : 'A'}</span>
                  <span className="text-[var(--text-secondary)] text-sm flex-1 truncate">{opponent.name}</span>
                  <span className="font-bold stat-number text-white text-sm">{teamScore ?? '?'} – {oppScore ?? '?'}</span>
                  <span className="text-[var(--text-muted)] text-xs">{new Date(m.match_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
