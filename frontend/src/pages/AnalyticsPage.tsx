import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Trophy, Shield, Flame, Calendar } from 'lucide-react';
import api from '../services/api';
import { PageLoader, ErrorBanner, EmptyState } from '../components/ui';

export function AnalyticsPage() {
  const [selectedSeason, setSelectedSeason] = useState<string>('2026-27');
  const { data: leagues } = useQuery({ queryKey: ['leagues'], queryFn: api.getLeagues });
  const leagueId = leagues?.[0]?.id;

  const { data: analytics, isLoading, error, refetch } = useQuery({
    queryKey: ['league-analytics', leagueId, selectedSeason],
    queryFn: () => api.getLeagueAnalytics(leagueId!, selectedSeason),
    enabled: !!leagueId,
  });

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorBanner message="Failed to load analytics" onRetry={refetch} />;
  if (!analytics) return <EmptyState title="No analytics available" message="Seed the database first" />;

  const { table, top_scorers_teams, best_defences_teams, available_seasons } = analytics;
  const seasonsList = available_seasons && available_seasons.length > 0
    ? available_seasons
    : [
        '2026-27', '2025-26', '2024-25', '2023-24', '2022-23', '2021-22',
        '2020-21', '2019-20', '2018-19', '2017-18',
        '2016-17', '2015-16', '2014-15', '2013-14',
      ];

  const isPredictedSeason = (analytics.season || selectedSeason) === '2026-27';
  const champion = table[0];
  const topAttack = top_scorers_teams[0];
  const topDefence = best_defences_teams[0];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Header with Season Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[#54C878] text-xs font-bold uppercase tracking-wider">Historical & Predictive Football Intelligence</span>
            {isPredictedSeason && (
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#54C878]/15 text-[#54C878] border border-[#54C878]/30">
                AI Predicted Season
              </span>
            )}
          </div>
          <h1 className="text-3xl font-extrabold text-[#F4F5F2] tracking-tight mt-1">
            Premier League Standings & Trends
          </h1>
          <p className="text-[#9DA4AA] mt-1 text-sm font-medium">
            {analytics.league.name} · Complete Standings ({seasonsList[seasonsList.length - 1]} to {seasonsList[0]})
          </p>
        </div>

        {/* Season Selector Dropdown */}
        <div className="flex items-center gap-2 bg-[#171B1F] p-1.5 rounded-lg border border-[var(--border)] self-start md:self-auto">
          <Calendar size={16} className="text-[#54C878] ml-2" />
          <span className="text-xs text-[#9DA4AA] font-semibold hidden sm:inline">Season:</span>
          <select
            id="season-selector"
            value={analytics.season || selectedSeason}
            onChange={(e) => setSelectedSeason(e.target.value)}
            className="bg-transparent text-sm font-bold text-[#F4F5F2] py-1 px-2.5 rounded focus:outline-none cursor-pointer"
          >
            {seasonsList.map((s) => (
              <option key={s} value={s} className="bg-[#171B1F] text-[#F4F5F2]">
                {s === '2026-27' ? `${s} (AI Predicted)` : `${s} Season`}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Season Quick Highlights */}
      {champion && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="glass-card p-4 border border-[var(--border)] flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-lg bg-[#3B82F6]/15 border border-[#3B82F6]/30 flex items-center justify-center text-[#3B82F6] shrink-0">
              <Trophy size={20} />
            </div>
            <div>
              <p className="text-[11px] font-bold text-[#9DA4AA] uppercase tracking-wider">
                {isPredictedSeason ? 'Projected Champions (2026-27)' : `Season Champions (${analytics.season})`}
              </p>
              <p className="text-base font-extrabold text-[#F4F5F2] truncate">{champion.team.name}</p>
              <p className="text-xs text-[#54C878] font-semibold">{champion.points} pts · {champion.won} wins · GD {champion.goal_difference > 0 ? `+${champion.goal_difference}` : champion.goal_difference}</p>
            </div>
          </div>

          {topAttack && (
            <div className="glass-card p-4 border border-[var(--border)] flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-lg bg-[#54C878]/15 border border-[#54C878]/30 flex items-center justify-center text-[#54C878] shrink-0">
                <Flame size={20} />
              </div>
              <div>
                <p className="text-[11px] font-bold text-[#9DA4AA] uppercase tracking-wider">Most Prolific Attack</p>
                <p className="text-base font-extrabold text-[#F4F5F2] truncate">{topAttack.team}</p>
                <p className="text-xs text-[#54C878] font-semibold">{topAttack.avg_goals.toFixed(2)} goals / match</p>
              </div>
            </div>
          )}

          {topDefence && (
            <div className="glass-card p-4 border border-[var(--border)] flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-lg bg-[#F59E0B]/15 border border-[#F59E0B]/30 flex items-center justify-center text-[#F59E0B] shrink-0">
                <Shield size={20} />
              </div>
              <div>
                <p className="text-[11px] font-bold text-[#9DA4AA] uppercase tracking-wider">Strictest Defence</p>
                <p className="text-base font-extrabold text-[#F4F5F2] truncate">{topDefence.team}</p>
                <p className="text-xs text-[#3B82F6] font-semibold">{topDefence.avg_conceded.toFixed(2)} conceded / match</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Charts row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Top scoring teams */}
        <div className="glass-card p-5 border border-[var(--border)]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[#F4F5F2] font-semibold text-base">
              Top Scoring Teams (Goals / Match)
            </h2>
            <span className="text-xs text-[#9DA4AA] font-mono">{analytics.season}</span>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={top_scorers_teams.slice(0, 8)} layout="vertical" margin={{ top: 5, right: 25, left: 5, bottom: 15 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" horizontal={false} />
              <XAxis
                type="number"
                stroke="#9DA4AA"
                tick={{ fill: '#F4F5F2', fontSize: 12, fontWeight: 600 }}
                tickLine={{ stroke: '#5C636A' }}
                axisLine={{ stroke: 'rgba(255,255,255,0.15)' }}
              />
              <YAxis
                dataKey="team"
                type="category"
                width={145}
                stroke="#9DA4AA"
                tick={{ fill: '#F4F5F2', fontSize: 12, fontWeight: 600 }}
                tickLine={false}
                axisLine={{ stroke: 'rgba(255,255,255,0.15)' }}
              />
              <Tooltip
                contentStyle={{ background: '#171B1F', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 6, fontSize: 12, color: '#F4F5F2' }}
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
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[#F4F5F2] font-semibold text-base">
              Best Defensive Units (Conceded / Match)
            </h2>
            <span className="text-xs text-[#9DA4AA] font-mono">{analytics.season}</span>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={best_defences_teams.slice(0, 8)} layout="vertical" margin={{ top: 5, right: 25, left: 5, bottom: 15 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" horizontal={false} />
              <XAxis
                type="number"
                stroke="#9DA4AA"
                tick={{ fill: '#F4F5F2', fontSize: 12, fontWeight: 600 }}
                tickLine={{ stroke: '#5C636A' }}
                axisLine={{ stroke: 'rgba(255,255,255,0.15)' }}
              />
              <YAxis
                dataKey="team"
                type="category"
                width={145}
                stroke="#9DA4AA"
                tick={{ fill: '#F4F5F2', fontSize: 12, fontWeight: 600 }}
                tickLine={false}
                axisLine={{ stroke: 'rgba(255,255,255,0.15)' }}
              />
              <Tooltip
                contentStyle={{ background: '#171B1F', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 6, fontSize: 12, color: '#F4F5F2' }}
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
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-[#F4F5F2] font-bold text-lg">
              {isPredictedSeason ? 'AI Projected League Standings (380 Matches)' : 'Official League Standings'}
            </h2>
            <p className="text-xs text-[#9DA4AA] mt-0.5">
              {isPredictedSeason
                ? 'Simulated final table based on 10,000 Monte Carlo runs and 45-feature ML Random Forest probabilities'
                : `Authentic match outcomes and points from the ${analytics.season} campaign`}
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-[#3B82F6]">
              <span className="w-2 h-2 rounded-full bg-[#3B82F6]"></span> UCL
            </span>
            <span className="flex items-center gap-1.5 text-[#54C878]">
              <span className="w-2 h-2 rounded-full bg-[#54C878]"></span> UEL
            </span>
            <span className="flex items-center gap-1.5 text-[#EF4444]">
              <span className="w-2 h-2 rounded-full bg-[#EF4444]"></span> Relegation
            </span>
          </div>
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
                      idx < 4 ? 'bg-[#3B82F6]/20 text-[#3B82F6]' : idx === 4 ? 'bg-[#54C878]/20 text-[#54C878]' : idx >= table.length - 3 ? 'bg-[#EF4444]/20 text-[#EF4444]' : 'text-[#5C636A]'
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
