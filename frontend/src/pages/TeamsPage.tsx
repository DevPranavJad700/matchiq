import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import api from '../services/api';
import { PageLoader, ErrorBanner, EmptyState } from '../components/ui';

export function TeamsPage() {
  const { data: leagues } = useQuery({ queryKey: ['leagues'], queryFn: api.getLeagues });
  const { data: teams, isLoading, error, refetch } = useQuery({
    queryKey: ['teams'],
    queryFn: () => api.getTeams(),
  });

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorBanner message="Failed to load teams" onRetry={refetch} />;
  if (!teams?.length) return <EmptyState title="No teams found" message="Seed the database first" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black text-white">Teams</h1>
        <p className="text-[var(--text-secondary)] mt-1">{teams.length} teams · {leagues?.[0]?.name ?? ''}</p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {teams.map((team) => (
          <Link
            key={team.id}
            to={`/teams/${team.id}`}
            id={`team-card-${team.id}`}
            className="glass-card p-4 flex items-center gap-3 hover:border-[#2979ff]/40 transition-all group"
          >
            <div className="w-10 h-10 rounded-full bg-[var(--navy-600)] flex items-center justify-center text-sm font-bold text-white shrink-0 group-hover:bg-[#2979ff]/20 transition-colors">
              {team.short_name || team.name.slice(0, 3).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white font-medium text-sm truncate">{team.name}</p>
              <p className="text-[var(--text-muted)] text-xs">{team.country || 'England'}</p>
            </div>
            <ChevronRight size={14} className="text-[var(--text-muted)] group-hover:text-[#2979ff] transition-colors" />
          </Link>
        ))}
      </div>
    </div>
  );
}
