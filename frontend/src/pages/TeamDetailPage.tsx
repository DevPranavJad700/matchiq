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
    <div className="space-y-6 animate-fade-in">
      {/* Back + header */}
      <div>
        <Link to="/teams" className="flex items-center gap-1 text-[#9DA4AA] hover:text-[#F4F5F2] text-xs mb-3 transition-colors">
          <ArrowLeft size={12} /> Back to Teams
        </Link>
        <div className="flex items-center justify-between flex-wrap gap-4 py-2 border-b border-[var(--border)]">
          <div className="flex items-center gap-3.5">
            <div className="w-14 h-14 rounded-lg bg-[#171B1F] border border-[var(--border-strong)] flex items-center justify-center text-lg font-bold text-[#F4F5F2]">
              {team.short_name || team.name.slice(0, 3).toUpperCase()}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[#F4F5F2]">{team.name}</h1>
              <p className="text-[#9DA4AA] text-xs mt-0.5">
                {team.country} · Premier League {stats?.season_year ?? '2023-24'}
              </p>
            </div>
          </div>
          <Link
            to={`/predict`}
            className="flex items-center gap-1.5 px-4 py-2 btn-primary text-xs font-semibold"
          >
            <Zap size={14} />
            Predict with {team.short_name || team.name}
          </Link>
        </div>
      </div>

      {/* Standing stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
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
          <div className="flex gap-2 mb-4">
            <FormStrip results={recentResults} />
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-2.5 rounded-md bg-[#171B1F] border border-[var(--border)]">
              <p className="text-xl font-bold text-[#54C878] stat-number">{form?.wins_last_5 ?? 0}</p>
              <p className="text-[#5C636A] text-xs mt-0.5 font-medium">Wins</p>
            </div>
            <div className="p-2.5 rounded-md bg-[#171B1F] border border-[var(--border)]">
              <p className="text-xl font-bold text-[#F59E0B] stat-number">{form?.draws_last_5 ?? 0}</p>
              <p className="text-[#5C636A] text-xs mt-0.5 font-medium">Draws</p>
            </div>
            <div className="p-2.5 rounded-md bg-[#171B1F] border border-[var(--border)]">
              <p className="text-xl font-bold text-[#EF4444] stat-number">{form?.losses_last_5 ?? 0}</p>
              <p className="text-[#5C636A] text-xs mt-0.5 font-medium">Losses</p>
            </div>
          </div>
        </div>

        {/* Attack/defence stats */}
        {stats && (
          <div className="glass-card p-5">
            <SectionHeader title="Performance Stats" subtitle="Season averages" />
            <div className="grid grid-cols-2 gap-2.5">
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
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={goalTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="match" tick={{ fill: '#9DA4AA', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9DA4AA', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#171B1F', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6 }}
                labelStyle={{ color: '#9DA4AA' }}
              />
              <Line type="monotone" dataKey="scored" stroke="#54C878" strokeWidth={2} dot={{ r: 3, fill: '#54C878' }} name="Goals Scored" />
              <Line type="monotone" dataKey="conceded" stroke="#EF4444" strokeWidth={2} dot={{ r: 3, fill: '#EF4444' }} name="Conceded" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent matches */}
      {matches && matches.items.length > 0 && (
        <div className="glass-card p-5">
          <SectionHeader title="Match History" />
          <div className="space-y-1">
            {matches.items.map((m) => {
              const isHome = m.home_team.id === teamId;
              const opponent = isHome ? m.away_team : m.home_team;
              const teamScore = isHome ? m.home_score : m.away_score;
              const oppScore = isHome ? m.away_score : m.home_score;
              const win = (isHome && m.result === 'H') || (!isHome && m.result === 'A');
              const draw = m.result === 'D';
              const resultColor = win ? '#54C878' : draw ? '#F59E0B' : '#EF4444';
              const resultLabel = win ? 'W' : draw ? 'D' : 'L';

              return (
                <Link key={m.id} to={`/matches/${m.id}`} className="flex items-center gap-4 py-2 px-3 rounded-md hover:bg-[#171B1F] transition-colors">
                  <span className="w-5 h-5 rounded text-xs font-bold flex items-center justify-center" style={{ color: resultColor, background: `${resultColor}15` }}>{resultLabel}</span>
                  <span className="text-[#5C636A] text-xs w-4">{isHome ? 'H' : 'A'}</span>
                  <span className="text-[#F4F5F2] text-sm flex-1 truncate font-medium">{opponent.name}</span>
                  <span className="font-bold stat-number text-[#F4F5F2] text-sm">{teamScore ?? '?'} – {oppScore ?? '?'}</span>
                  <span className="text-[#5C636A] text-xs">{new Date(m.match_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
