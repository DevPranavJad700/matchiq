import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, Search } from 'lucide-react';
import { clsx } from 'clsx';
import api from '../services/api';
import { Spinner } from './ui';

interface TeamSelectorProps {
  label: string;
  value: number | null;
  onChange: (teamId: number | null) => void;
  excludeId?: number | null;
  id: string;
}

export function TeamSelector({ label, value, onChange, excludeId, id }: TeamSelectorProps) {
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);

  const { data: teams, isLoading } = useQuery({
    queryKey: ['teams'],
    queryFn: () => api.getTeams(),
    staleTime: 5 * 60 * 1000,
  });

  const filtered = teams?.filter(
    (t) =>
      t.id !== excludeId &&
      t.name.toLowerCase().includes(search.toLowerCase())
  ) ?? [];

  const selected = teams?.find((t) => t.id === value);

  return (
    <div className="relative" id={id}>
      <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-2">
        {label}
      </label>

      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={clsx(
          'w-full flex items-center justify-between px-4 py-3 rounded-xl border transition-all',
          'bg-[var(--navy-800)] text-left',
          open
            ? 'border-[#2979ff] shadow-[0_0_0_3px_rgba(41,121,255,0.15)]'
            : 'border-[var(--border)] hover:border-[var(--navy-500)]'
        )}
      >
        {selected ? (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[var(--navy-600)] flex items-center justify-center text-xs font-bold text-white">
              {selected.short_name || selected.name.slice(0, 3).toUpperCase()}
            </div>
            <span className="font-medium text-white">{selected.name}</span>
          </div>
        ) : (
          <span className="text-[var(--text-muted)]">
            {isLoading ? 'Loading teams...' : 'Select a team...'}
          </span>
        )}
        <ChevronDown
          size={16}
          className={clsx(
            'text-[var(--text-muted)] transition-transform duration-200',
            open && 'rotate-180'
          )}
        />
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute z-50 w-full mt-2 rounded-xl border border-[var(--border)] bg-[var(--navy-800)] shadow-2xl overflow-hidden">
          {/* Search */}
          <div className="p-2 border-b border-[var(--border)]">
            <div className="flex items-center gap-2 px-3 py-2 bg-[var(--navy-700)] rounded-lg">
              <Search size={14} className="text-[var(--text-muted)]" />
              <input
                autoFocus
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search teams..."
                className="flex-1 bg-transparent text-sm text-white placeholder-[var(--text-muted)] outline-none"
              />
            </div>
          </div>

          {/* Options */}
          <div className="max-h-60 overflow-y-auto">
            {isLoading ? (
              <div className="flex justify-center py-6">
                <Spinner size="sm" />
              </div>
            ) : filtered.length === 0 ? (
              <p className="text-center text-[var(--text-muted)] text-sm py-6">No teams found</p>
            ) : (
              filtered.map((team) => (
                <button
                  key={team.id}
                  type="button"
                  onClick={() => {
                    onChange(team.id);
                    setOpen(false);
                    setSearch('');
                  }}
                  className={clsx(
                    'w-full flex items-center gap-3 px-4 py-3 text-left transition-colors',
                    team.id === value
                      ? 'bg-[rgba(41,121,255,0.15)] text-white'
                      : 'hover:bg-[var(--glass-hover)] text-[var(--text-secondary)] hover:text-white'
                  )}
                >
                  <div className="w-7 h-7 rounded-full bg-[var(--navy-600)] flex items-center justify-center text-xs font-bold text-white shrink-0">
                    {team.short_name || team.name.slice(0, 3).toUpperCase()}
                  </div>
                  <span className="text-sm font-medium">{team.name}</span>
                </button>
              ))
            )}
          </div>
        </div>
      )}

      {/* Close on outside click */}
      {open && (
        <div className="fixed inset-0 z-40" onClick={() => { setOpen(false); setSearch(''); }} />
      )}
    </div>
  );
}
