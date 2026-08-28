import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { PageLoader, ErrorBanner } from '../components/ui';
import { MatchCard } from '../components/PredictionCard';

export function MatchesPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['matches', { page }],
    queryFn: () => api.getMatches({ page, page_size: 25 }),
  });

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorBanner message="Failed to load matches" onRetry={refetch} />;

  const totalPages = data ? Math.ceil(data.total / 25) : 1;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
        <div>
          <span className="text-[#54C878] text-xs font-bold uppercase tracking-wider">Fixtures</span>
          <h1 className="text-3xl font-extrabold text-[#F4F5F2] tracking-tight mt-1">Match History</h1>
          <p className="text-[#9DA4AA] text-sm mt-0.5">{data?.total} matches · Page {page} of {totalPages}</p>
        </div>
      </div>

      <div className="space-y-2">
        {data?.items.map((m) => <MatchCard key={m.id} match={m} />) ?? null}
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
    </div>
  );
}
