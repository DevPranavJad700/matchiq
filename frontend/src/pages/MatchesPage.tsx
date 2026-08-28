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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black text-white">Matches</h1>
          <p className="text-[var(--text-secondary)] mt-1">{data?.total} matches · Page {page} of {totalPages}</p>
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
            className="px-4 py-2 rounded-lg border border-[var(--border)] text-sm text-[var(--text-secondary)] hover:text-white hover:border-[var(--navy-500)] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            Previous
          </button>
          <span className="text-[var(--text-muted)] text-sm px-4">
            {page} / {totalPages}
          </span>
          <button
            id="next-page"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            className="px-4 py-2 rounded-lg border border-[var(--border)] text-sm text-[var(--text-secondary)] hover:text-white hover:border-[var(--navy-500)] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
