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
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-black text-white">Analytics</h1>
        <p className="text-[var(--text-secondary)] mt-1">
          {analytics.league.name} · {analytics.season}
        </p>
      </div>

      {/* Charts row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Top scoring teams */}
        <div className="glass-card p-5">
          <h2 className="text-white font-bold text-lg mb-4">Top Scoring Teams</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={top_scorers_teams.slice(0, 8)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis dataKey="team" type="category" width={120} tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: 'var(--navy-800)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                formatter={(v) => [`${(Number(v) || 0).toFixed(2)} avg`, 'Goals/Match'] as [string, string]}
              />
              <Bar dataKey="avg_goals" radius={[0, 4, 4, 0]}>
                {top_scorers_teams.slice(0, 8).map((_, i) => (
                  <Cell key={i} fill={`rgba(0, 230, 118, ${0.9 - i * 0.08})`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Best defences */}
        <div className="glass-card p-5">
          <h2 className="text-white font-bold text-lg mb-4">Best Defences</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={best_defences_teams.slice(0, 8)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis dataKey="team" type="category" width={120} tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: 'var(--navy-800)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                formatter={(v) => [`${(Number(v) || 0).toFixed(2)} avg`, 'Goals Conceded/Match'] as [string, string]}
              />
              <Bar dataKey="avg_conceded" radius={[0, 4, 4, 0]}>
                {best_defences_teams.slice(0, 8).map((_, i) => (
                  <Cell key={i} fill={`rgba(41, 121, 255, ${0.9 - i * 0.08})`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* League Table */}
      <div className="glass-card p-5">
        <h2 className="text-white font-bold text-xl mb-5">League Table</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[var(--text-muted)] text-xs uppercase tracking-wider border-b border-[var(--border)]">
                <th className="py-2 px-3 text-left w-8">#</th>
                <th className="py-2 px-3 text-left">Team</th>
                <th className="py-2 px-3 text-center">P</th>
                <th className="py-2 px-3 text-center">W</th>
                <th className="py-2 px-3 text-center">D</th>
                <th className="py-2 px-3 text-center">L</th>
                <th className="py-2 px-3 text-center">GF</th>
                <th className="py-2 px-3 text-center">GA</th>
                <th className="py-2 px-3 text-center">GD</th>
                <th className="py-2 px-3 text-center font-bold">Pts</th>
              </tr>
            </thead>
            <tbody>
              {table.map((row, idx) => (
                <tr
                  key={row.position}
                  id={`league-row-${row.position}`}
                  className="table-row-hover border-b border-[var(--border)] border-opacity-50 transition-colors"
                >
                  <td className="py-2 px-3">
                    <span className={`text-xs font-bold ${
                      idx < 4 ? 'text-[#2979ff]' : idx < 6 ? 'text-[#00e676]' : idx >= table.length - 3 ? 'text-[#ff4444]' : 'text-[var(--text-muted)]'
                    }`}>{row.position}</span>
                  </td>
                  <td className="py-2 px-3">
                    <span className="text-white font-medium">{row.team.name}</span>
                  </td>
                  <td className="py-2 px-3 text-center text-[var(--text-secondary)] stat-number">{row.played}</td>
                  <td className="py-2 px-3 text-center text-[#00e676] stat-number">{row.won}</td>
                  <td className="py-2 px-3 text-center text-[#ffc107] stat-number">{row.drawn}</td>
                  <td className="py-2 px-3 text-center text-[#ff4444] stat-number">{row.lost}</td>
                  <td className="py-2 px-3 text-center text-[var(--text-secondary)] stat-number">{row.goals_for}</td>
                  <td className="py-2 px-3 text-center text-[var(--text-secondary)] stat-number">{row.goals_against}</td>
                  <td className="py-2 px-3 text-center stat-number">
                    <span className={row.goal_difference > 0 ? 'text-[#00e676]' : row.goal_difference < 0 ? 'text-[#ff4444]' : 'text-[var(--text-muted)]'}>
                      {row.goal_difference > 0 ? '+' : ''}{row.goal_difference}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span className="font-black text-white stat-number">{row.points}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-4 mt-4 pt-4 border-t border-[var(--border)] text-xs text-[var(--text-muted)]">
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#2979ff]" /> Champions League</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#00e676]" /> Europa League</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#ff4444]" /> Relegation</span>
        </div>
      </div>
    </div>
  );
}
