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
    <div className="space-y-6 animate-fade-in">
      <div>
        <span className="text-[#54C878] text-xs font-bold uppercase tracking-wider">Directory</span>
        <h1 className="text-3xl font-extrabold text-[#F4F5F2] tracking-tight mt-1">Premier League Teams</h1>
        <p className="text-[#9DA4AA] text-sm mt-0.5">{teams.length} teams · {leagues?.[0]?.name ?? 'English Premier League'}</p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {teams.map((team) => (
          <Link
            key={team.id}
            to={`/teams/${team.id}`}
            id={`team-card-${team.id}`}
            className="glass-card p-3.5 flex items-center gap-3 hover:bg-[#171B1F] transition-colors group"
          >
            <div className="w-9 h-9 rounded bg-[#171B1F] border border-[var(--border-strong)] flex items-center justify-center text-xs font-bold text-[#F4F5F2] shrink-0">
              {team.short_name || team.name.slice(0, 3).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[#F4F5F2] font-semibold text-sm truncate">{team.name}</p>
              <p className="text-[#5C636A] text-xs">{team.country || 'England'}</p>
            </div>
            <ChevronRight size={14} className="text-[#5C636A] group-hover:text-[#F4F5F2] transition-colors" />
          </Link>
        ))}
      </div>
    </div>
  );
}
