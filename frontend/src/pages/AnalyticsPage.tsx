import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import api from '../services/api';
import { PageLoader, ErrorBanner, EmptyState } from '../components/ui';

export function AnalyticsPage() {
  const { data: leagues } = useQuery({ queryKey: ['leagues'], queryFn: api.getLeagues });
  const leagueId = leagues?.[0]?.id;

  const { data: analytics, isLoading, error, refetch } = useQuery({
    queryKey: ['league-analytics', leagueId],
    queryFn: () => api.getLeagueAnalytics(leagueId!),
    enabled: !!leagueId,
  });

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorBanner message="Failed to load analytics" onRetry={refetch} />;
  if (!analytics) return <EmptyState title="No analytics available" message="Seed the database first" />;

  const { table, top_scorers_teams, best_defences_teams } = analytics;

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          League <span className="gradient-text">Analytics</span>
        </h1>
        <p className="text-[var(--text-secondary)] mt-1 font-medium">
          {analytics.league.name} · Season {analytics.season} Metrics Breakdown
        </p>
      </div>

      {/* Charts row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Top scoring teams */}
        <div className="glass-card p-6 border border-[#00e676]/20 shadow-xl">
          <h2 className="text-white font-extrabold text-lg mb-4 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#00e676]" /> Top Scoring Teams (Goals / Match)
          </h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={top_scorers_teams.slice(0, 8)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 600 }} />
              <YAxis dataKey="team" type="category" width={130} tick={{ fill: '#f8fafc', fontSize: 11, fontWeight: 600 }} />
              <Tooltip
                contentStyle={{ background: '#0d1527', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 12, fontSize: 12, fontWeight: 600 }}
                formatter={(v) => [`${(Number(v) || 0).toFixed(2)} avg goals`, 'Attack Strength'] as [string, string]}
              />
              <Bar dataKey="avg_goals" radius={[0, 6, 6, 0]}>
                {top_scorers_teams.slice(0, 8).map((_, i) => (
                  <Cell key={i} fill={`rgba(0, 230, 118, ${0.95 - i * 0.08})`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Best defences */}
        <div className="glass-card p-6 border border-[#2979ff]/20 shadow-xl">
          <h2 className="text-white font-extrabold text-lg mb-4 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#2979ff]" /> Best Defensive Units (Conceded / Match)
          </h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={best_defences_teams.slice(0, 8)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 600 }} />
              <YAxis dataKey="team" type="category" width={130} tick={{ fill: '#f8fafc', fontSize: 11, fontWeight: 600 }} />
              <Tooltip
                contentStyle={{ background: '#0d1527', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 12, fontSize: 12, fontWeight: 600 }}
                formatter={(v) => [`${(Number(v) || 0).toFixed(2)} avg conceded`, 'Defensive Strength'] as [string, string]}
              />
              <Bar dataKey="avg_conceded" radius={[0, 6, 6, 0]}>
                {best_defences_teams.slice(0, 8).map((_, i) => (
                  <Cell key={i} fill={`rgba(41, 121, 255, ${0.95 - i * 0.08})`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* League Table */}
      <div className="glass-card p-6 border border-[var(--border)] shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-white font-extrabold text-2xl tracking-tight">Official League Standings</h2>
          <span className="text-xs font-semibold px-3 py-1 rounded-full bg-[var(--navy-800)] text-[var(--text-secondary)] border border-[var(--border)]">
            2023-2024 Season
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider border-b border-[var(--border)] bg-[var(--navy-900)]">
                <th className="py-3 px-3 text-left w-10">#</th>
                <th className="py-3 px-4 text-left">Team</th>
                <th className="py-3 px-3 text-center">P</th>
                <th className="py-3 px-3 text-center">W</th>
                <th className="py-3 px-3 text-center">D</th>
                <th className="py-3 px-3 text-center">L</th>
                <th className="py-3 px-3 text-center">GF</th>
                <th className="py-3 px-3 text-center">GA</th>
                <th className="py-3 px-3 text-center">GD</th>
                <th className="py-3 px-4 text-center font-black text-white">Pts</th>
              </tr>
            </thead>
            <tbody>
              {table.map((row, idx) => (
                <tr
                  key={row.position}
                  id={`league-row-${row.position}`}
                  className="table-row-hover border-b border-[var(--border)] border-opacity-40 transition-colors"
                >
                  <td className="py-3 px-3">
                    <span className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold ${
                      idx < 4 ? 'bg-[#2979ff]/20 text-[#2979ff] border border-[#2979ff]/40' : idx < 6 ? 'bg-[#00e676]/20 text-[#00e676] border border-[#00e676]/40' : idx >= table.length - 3 ? 'bg-[#ff4444]/20 text-[#ff4444] border border-[#ff4444]/40' : 'text-[var(--text-muted)]'
                    }`}>{row.position}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-white font-bold">{row.team.name}</span>
                  </td>
                  <td className="py-3 px-3 text-center text-[var(--text-secondary)] font-medium stat-number">{row.played}</td>
                  <td className="py-3 px-3 text-center text-[#00e676] font-bold stat-number">{row.won}</td>
                  <td className="py-3 px-3 text-center text-[#ffc107] font-bold stat-number">{row.drawn}</td>
                  <td className="py-3 px-3 text-center text-[#ff4444] font-bold stat-number">{row.lost}</td>
                  <td className="py-3 px-3 text-center text-[var(--text-secondary)] font-medium stat-number">{row.goals_for}</td>
                  <td className="py-3 px-3 text-center text-[var(--text-secondary)] font-medium stat-number">{row.goals_against}</td>
                  <td className="py-3 px-3 text-center font-bold stat-number">
                    <span className={row.goal_difference > 0 ? 'text-[#00e676]' : row.goal_difference < 0 ? 'text-[#ff4444]' : 'text-[var(--text-muted)]'}>
                      {row.goal_difference > 0 ? '+' : ''}{row.goal_difference}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="font-black text-white text-base stat-number">{row.points}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-5 mt-5 pt-4 border-t border-[var(--border)] text-xs font-semibold text-[var(--text-muted)]">
          <span className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#2979ff]" /> UEFA Champions League</span>
          <span className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#00e676]" /> UEFA Europa League</span>
          <span className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#ff4444]" /> Relegation Zone</span>
        </div>
      </div>
    </div>
  );
}
