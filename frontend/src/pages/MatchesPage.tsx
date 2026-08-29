import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Calendar, Users, RotateCcw } from 'lucide-react';
import api from '../services/api';
import { PageLoader, ErrorBanner } from '../components/ui';
import { MatchCard } from '../components/PredictionCard';

export function MatchesPage() {
  const [page, setPage] = useState(1);
  const [selectedTeamId, setSelectedTeamId] = useState<number | undefined>();
  const [selectedSeasonId, setSelectedSeasonId] = useState<number | undefined>();

  const { data: leagues } = useQuery({ queryKey: ['leagues'], queryFn: api.getLeagues });
  const leagueId = leagues?.[0]?.id;

  const { data: seasons } = useQuery({
    queryKey: ['league-seasons', leagueId],
    queryFn: () => (leagueId ? api.getLeagueSeasons(leagueId) : Promise.resolve([])),
    enabled: !!leagueId,
  });

  const { data: teams } = useQuery({ queryKey: ['teams'], queryFn: () => api.getTeams() });

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['matches', { page, team_id: selectedTeamId, season_id: selectedSeasonId }],
    queryFn: () =>
      api.getMatches({
        page,
        page_size: 20,
        team_id: selectedTeamId,
        season_id: selectedSeasonId,
      }),
  });

  const totalPages = data ? Math.ceil(data.total / 20) : 1;

  const handleResetFilters = () => {
    setSelectedTeamId(undefined);
    setSelectedSeasonId(undefined);
    setPage(1);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
        <div>
          <span className="text-[#54C878] text-xs font-bold uppercase tracking-wider">Historical Archives</span>
          <h1 className="text-3xl font-extrabold text-[#F4F5F2] tracking-tight mt-1">Match Fixtures & Results</h1>
          <p className="text-[#9DA4AA] text-sm mt-0.5">
            {data?.total?.toLocaleString() ?? 0} authentic matches across 13 Premier League seasons
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
                setPage(1);
              }}
              className="bg-transparent text-xs font-semibold text-[#F4F5F2] focus:outline-none cursor-pointer"
            >
              <option value="" className="bg-[#171B1F] text-[#9DA4AA]">All Seasons</option>
              {seasons?.map((s) => (
                <option key={s.id} value={s.id} className="bg-[#171B1F] text-[#F4F5F2]">
                  {s.year} Season
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
          {(selectedTeamId !== undefined || selectedSeasonId !== undefined) && (
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

      {isLoading ? (
        <PageLoader />
      ) : error ? (
        <ErrorBanner message="Failed to load matches" onRetry={refetch} />
      ) : data?.items.length === 0 ? (
        <div className="text-center py-12 glass-card border border-[var(--border)]">
          <p className="text-[#F4F5F2] font-semibold text-base">No matches found</p>
          <p className="text-[#9DA4AA] text-xs mt-1">Try selecting a different season or team filter.</p>
          <button
            onClick={handleResetFilters}
            className="mt-4 px-3 py-1.5 rounded bg-[#171B1F] border border-[var(--border)] text-xs text-[#54C878] font-semibold hover:bg-[#22272B] transition-colors"
          >
            Clear Filters
          </button>
        </div>
      ) : (
        <>
          <div className="space-y-2">
            {data?.items.map((m) => <MatchCard key={m.id} match={m} />)}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <button
                id="prev-page"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3.5 py-1.5 rounded-md border border-[var(--border)] text-xs font-semibold text-[#9DA4AA] hover:text-[#F4F5F2] hover:bg-[#171B1F] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <span className="text-[#5C636A] text-xs px-3 font-medium">
                Page {page} of {totalPages}
              </span>
              <button
                id="next-page"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="px-3.5 py-1.5 rounded-md border border-[var(--border)] text-xs font-semibold text-[#9DA4AA] hover:text-[#F4F5F2] hover:bg-[#171B1F] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
