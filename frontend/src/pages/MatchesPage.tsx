import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Calendar, Users, RotateCcw, ChevronLeft, ChevronRight } from 'lucide-react';
import api from '../services/api';
import { PageLoader, ErrorBanner } from '../components/ui';
import { MatchCard } from '../components/PredictionCard';
import type { MatchListItem } from '../types';

export function MatchesPage() {
  const [page, setPage] = useState(1);
  const [selectedTeamId, setSelectedTeamId] = useState<number | undefined>();
  const [selectedSeasonId, setSelectedSeasonId] = useState<number | undefined>();
  const [selectedMatchday, setSelectedMatchday] = useState<number | undefined>();

  const { data: leagues } = useQuery({ queryKey: ['leagues'], queryFn: api.getLeagues });
  const leagueId = leagues?.[0]?.id;

  const { data: seasons } = useQuery({
    queryKey: ['league-seasons', leagueId],
    queryFn: () => (leagueId ? api.getLeagueSeasons(leagueId) : Promise.resolve([])),
    enabled: !!leagueId,
  });

  // Default to 2026-27 season once seasons load
  useEffect(() => {
    if (seasons && seasons.length > 0 && selectedSeasonId === undefined) {
      const season2627 = seasons.find((s) => s.year === '2026-27');
      if (season2627) {
        setSelectedSeasonId(season2627.id);
      }
    }
  }, [seasons, selectedSeasonId]);

  const { data: teams } = useQuery({ queryKey: ['teams'], queryFn: () => api.getTeams() });

  const pageSize = selectedMatchday ? 10 : 20;

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['matches', { page, team_id: selectedTeamId, season_id: selectedSeasonId, matchday: selectedMatchday, pageSize }],
    queryFn: () =>
      api.getMatches({
        page,
        page_size: pageSize,
        team_id: selectedTeamId,
        season_id: selectedSeasonId,
        matchday: selectedMatchday,
      }),
  });

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;
  const currentSeason = seasons?.find((s) => s.id === selectedSeasonId);
  const is2026_27 = currentSeason?.year === '2026-27';

  const handleResetFilters = () => {
    setSelectedTeamId(undefined);
    setSelectedMatchday(undefined);
    setPage(1);
  };

  // Group matches by matchday for clean section rendering
  const groupedMatches = useMemo(() => {
    if (!data?.items) return [];
    const groups: { matchday: number | null; matches: MatchListItem[] }[] = [];
    const map = new Map<number | null, MatchListItem[]>();

    for (const match of data.items) {
      const md = match.matchday ?? null;
      if (!map.has(md)) {
        map.set(md, []);
      }
      map.get(md)!.push(match);
    }

    for (const [matchday, matches] of map.entries()) {
      groups.push({ matchday, matches });
    }
    return groups;
  }, [data?.items]);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[#54C878] text-xs font-bold uppercase tracking-wider">Historical & Projected Archives</span>
            {is2026_27 && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#3B82F6]/15 text-[#3B82F6] border border-[#3B82F6]/30">
                2026–27 AI Projected Season
              </span>
            )}
          </div>
          <h1 className="text-3xl font-extrabold text-[#F4F5F2] tracking-tight mt-1">Match Fixtures & Results</h1>
          <p className="text-[#9DA4AA] text-sm mt-0.5">
            {data?.total?.toLocaleString() ?? 0} matches {is2026_27 ? '(All 38 Matchweeks / 380 Fixtures)' : 'across Premier League seasons'}
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Season Filter */}
          <div className="flex items-center gap-1.5 bg-[#171B1F] py-1.5 px-3 rounded-lg border border-[var(--border)]">
            <Calendar size={14} className="text-[#54C878]" />
            <select
              id="filter-season"
              value={selectedSeasonId ?? ''}
              onChange={(e) => {
                setSelectedSeasonId(e.target.value ? Number(e.target.value) : undefined);
                setSelectedMatchday(undefined);
                setPage(1);
              }}
              className="bg-transparent text-xs font-semibold text-[#F4F5F2] focus:outline-none cursor-pointer"
            >
              <option value="" className="bg-[#171B1F] text-[#9DA4AA]">All Seasons</option>
              {seasons?.map((s) => (
                <option key={s.id} value={s.id} className="bg-[#171B1F] text-[#F4F5F2]">
                  {s.year === '2026-27' ? `${s.year} (AI Predicted)` : `${s.year} Season`}
                </option>
              ))}
            </select>
          </div>

          {/* Team Filter */}
          <div className="flex items-center gap-1.5 bg-[#171B1F] py-1.5 px-3 rounded-lg border border-[var(--border)]">
            <Users size={14} className="text-[#3B82F6]" />
            <select
              id="filter-team"
              value={selectedTeamId ?? ''}
              onChange={(e) => {
                setSelectedTeamId(e.target.value ? Number(e.target.value) : undefined);
                setPage(1);
              }}
              className="bg-transparent text-xs font-semibold text-[#F4F5F2] focus:outline-none cursor-pointer"
            >
              <option value="" className="bg-[#171B1F] text-[#9DA4AA]">All Teams</option>
              {teams?.map((t) => (
                <option key={t.id} value={t.id} className="bg-[#171B1F] text-[#F4F5F2]">
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          {/* Reset Filters */}
          {(selectedTeamId !== undefined || selectedMatchday !== undefined) && (
            <button
              onClick={handleResetFilters}
              className="flex items-center gap-1 text-xs text-[#9DA4AA] hover:text-[#F4F5F2] px-2 py-1.5 rounded hover:bg-[#171B1F] transition-colors"
            >
              <RotateCcw size={13} />
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Matchweek Quick-Select Horizontal Slider Bar */}
      {selectedSeasonId && (
        <div className="glass-card p-3 border border-[var(--border)]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-[#9DA4AA] uppercase tracking-wider">Select Matchweek (1 – 38)</span>
            {selectedMatchday && (
              <span className="text-xs text-[#54C878] font-bold">
                Showing Matchweek {selectedMatchday} (10 Fixtures)
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar scroll-smooth">
            <button
              onClick={() => {
                setSelectedMatchday(undefined);
                setPage(1);
              }}
              className={`px-3 py-1 rounded-md text-xs font-bold shrink-0 transition-colors ${
                selectedMatchday === undefined
                  ? 'bg-[#54C878] text-[#0D0F11]'
                  : 'bg-[#171B1F] text-[#9DA4AA] hover:text-[#F4F5F2] border border-[var(--border)]'
              }`}
            >
              All MWs
            </button>
            {Array.from({ length: 38 }, (_, i) => i + 1).map((mw) => (
              <button
                key={mw}
                onClick={() => {
                  setSelectedMatchday(mw);
                  setPage(1);
                }}
                className={`px-2.5 py-1 rounded-md text-xs font-bold shrink-0 transition-colors ${
                  selectedMatchday === mw
                    ? 'bg-[#54C878] text-[#0D0F11]'
                    : 'bg-[#171B1F] text-[#9DA4AA] hover:text-[#F4F5F2] border border-[var(--border)]'
                }`}
              >
                MW {mw}
              </button>
            ))}
          </div>
        </div>
      )}

      {isLoading ? (
        <PageLoader />
      ) : error ? (
        <ErrorBanner message="Failed to load matches" onRetry={refetch} />
      ) : data?.items.length === 0 ? (
        <div className="text-center py-12 glass-card border border-[var(--border)]">
          <p className="text-[#F4F5F2] font-semibold text-base">No matches found</p>
          <p className="text-[#9DA4AA] text-xs mt-1">Try selecting a different season or matchweek filter.</p>
          <button
            onClick={handleResetFilters}
            className="mt-4 px-3 py-1.5 rounded bg-[#171B1F] border border-[var(--border)] text-xs text-[#54C878] font-semibold hover:bg-[#22272B] transition-colors"
          >
            Clear Filters
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {groupedMatches.map((group) => (
            <div key={group.matchday ?? 'other'} className="space-y-2.5">
              {group.matchday && (
                <div className="flex items-center justify-between px-1 border-b border-[var(--border)] pb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-extrabold text-[#F4F5F2]">
                      Matchweek {group.matchday}
                    </span>
                    {is2026_27 && (
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#3B82F6]/15 text-[#3B82F6] border border-[#3B82F6]/30">
                        AI Model Projected
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-[#9DA4AA] font-mono">
                    {group.matches.length} {group.matches.length === 1 ? 'Match' : 'Matches'}
                  </span>
                </div>
              )}
              <div className="space-y-2">
                {group.matches.map((m) => (
                  <MatchCard key={m.id} match={m} />
                ))}
              </div>
            </div>
          ))}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <button
                id="prev-page"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="flex items-center gap-1 px-3.5 py-1.5 rounded-md border border-[var(--border)] text-xs font-semibold text-[#9DA4AA] hover:text-[#F4F5F2] hover:bg-[#171B1F] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft size={14} />
                Previous
              </button>
              <span className="text-[#5C636A] text-xs px-3 font-medium">
                Page {page} of {totalPages}
              </span>
              <button
                id="next-page"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="flex items-center gap-1 px-3.5 py-1.5 rounded-md border border-[var(--border)] text-xs font-semibold text-[#9DA4AA] hover:text-[#F4F5F2] hover:bg-[#171B1F] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Next
                <ChevronRight size={14} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
