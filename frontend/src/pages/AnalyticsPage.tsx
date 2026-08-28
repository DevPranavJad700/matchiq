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
        <span className="text-[#54C878] text-xs font-bold uppercase tracking-wider">Football Data Journalism</span>
        <h1 className="text-3xl font-extrabold text-[#F4F5F2] tracking-tight mt-1">
          League Performance Trends
        </h1>
        <p className="text-[#9DA4AA] mt-1 text-sm font-medium">
          {analytics.league.name} · Season {analytics.season} Metrics
        </p>
      </div>

      {/* Charts row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Top scoring teams */}
        <div className="glass-card p-5 border border-[var(--border)]">
          <h2 className="text-[#F4F5F2] font-semibold text-base mb-4">
            Top Scoring Teams (Goals / Match)
          </h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={top_scorers_teams.slice(0, 8)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis type="number" tick={{ fill: '#9DA4AA', fontSize: 11 }} />
              <YAxis dataKey="team" type="category" width={120} tick={{ fill: '#F4F5F2', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#171B1F', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6, fontSize: 12 }}
                formatter={(v) => [`${(Number(v) || 0).toFixed(2)} goals/match`, 'Attack'] as [string, string]}
              />
              <Bar dataKey="avg_goals" radius={[0, 4, 4, 0]}>
                {top_scorers_teams.slice(0, 8).map((_, i) => (
                  <Cell key={i} fill="#54C878" opacity={1 - i * 0.08} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Best defences */}
        <div className="glass-card p-5 border border-[var(--border)]">
          <h2 className="text-[#F4F5F2] font-semibold text-base mb-4">
            Best Defensive Units (Conceded / Match)
          </h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={best_defences_teams.slice(0, 8)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis type="number" tick={{ fill: '#9DA4AA', fontSize: 11 }} />
              <YAxis dataKey="team" type="category" width={120} tick={{ fill: '#F4F5F2', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#171B1F', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6, fontSize: 12 }}
                formatter={(v) => [`${(Number(v) || 0).toFixed(2)} conceded/match`, 'Defence'] as [string, string]}
              />
              <Bar dataKey="avg_conceded" radius={[0, 4, 4, 0]}>
                {best_defences_teams.slice(0, 8).map((_, i) => (
                  <Cell key={i} fill="#3B82F6" opacity={1 - i * 0.08} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* League Table */}
      <div className="glass-card p-5 border border-[var(--border)]">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[#F4F5F2] font-bold text-lg">Official League Standings</h2>
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-[#171B1F] text-[#9DA4AA] border border-[var(--border)]">
            2023-2024 Season
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[#5C636A] text-xs font-semibold uppercase tracking-wider border-b border-[var(--border)] bg-[#171B1F]">
                <th className="py-2.5 px-3 text-left w-10">#</th>
                <th className="py-2.5 px-4 text-left">Team</th>
                <th className="py-2.5 px-3 text-center">P</th>
                <th className="py-2.5 px-3 text-center">W</th>
                <th className="py-2.5 px-3 text-center">D</th>
                <th className="py-2.5 px-3 text-center">L</th>
                <th className="py-2.5 px-3 text-center">GF</th>
                <th className="py-2.5 px-3 text-center">GA</th>
                <th className="py-2.5 px-3 text-center">GD</th>
                <th className="py-2.5 px-4 text-center font-bold text-[#F4F5F2]">Pts</th>
              </tr>
            </thead>
            <tbody>
              {table.map((row, idx) => (
                <tr
                  key={row.position}
                  id={`league-row-${row.position}`}
                  className="table-row-hover border-b border-[var(--border)]"
                >
                  <td className="py-2.5 px-3">
                    <span className={`w-5 h-5 rounded flex items-center justify-center text-xs font-bold ${
                      idx < 4 ? 'bg-[#3B82F6]/20 text-[#3B82F6]' : idx < 6 ? 'bg-[#54C878]/20 text-[#54C878]' : idx >= table.length - 3 ? 'bg-[#EF4444]/20 text-[#EF4444]' : 'text-[#5C636A]'
                    }`}>{row.position}</span>
                  </td>
                  <td className="py-2.5 px-4">
                    <span className="text-[#F4F5F2] font-semibold">{row.team.name}</span>
                  </td>
                  <td className="py-2.5 px-3 text-center text-[#9DA4AA] stat-number">{row.played}</td>
                  <td className="py-2.5 px-3 text-center text-[#54C878] font-medium stat-number">{row.won}</td>
                  <td className="py-2.5 px-3 text-center text-[#F59E0B] font-medium stat-number">{row.drawn}</td>
                  <td className="py-2.5 px-3 text-center text-[#EF4444] font-medium stat-number">{row.lost}</td>
                  <td className="py-2.5 px-3 text-center text-[#9DA4AA] stat-number">{row.goals_for}</td>
                  <td className="py-2.5 px-3 text-center text-[#9DA4AA] stat-number">{row.goals_against}</td>
                  <td className="py-2.5 px-3 text-center font-semibold stat-number">
                    <span className={row.goal_difference > 0 ? 'text-[#54C878]' : row.goal_difference < 0 ? 'text-[#EF4444]' : 'text-[#5C636A]'}>
                      {row.goal_difference > 0 ? '+' : ''}{row.goal_difference}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-center">
                    <span className="font-bold text-[#F4F5F2] text-sm stat-number">{row.points}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
