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
      <label className="block text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-2">
        {label}
      </label>

      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={clsx(
          'w-full flex items-center justify-between px-4 py-3.5 rounded-2xl border transition-all duration-300',
          'bg-[var(--navy-800)] text-left shadow-lg',
          open
            ? 'border-[#2979ff] shadow-[0_0_20px_rgba(41,121,255,0.25)] ring-2 ring-[#2979ff]/20'
            : 'border-[var(--border)] hover:border-[#2979ff]/50'
        )}
      >
        {selected ? (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#2979ff] to-[#7c3aed] flex items-center justify-center text-xs font-extrabold text-white shadow-md">
              {selected.short_name || selected.name.slice(0, 3).toUpperCase()}
            </div>
            <span className="font-bold text-white text-base">{selected.name}</span>
          </div>
        ) : (
          <span className="text-[var(--text-muted)] font-medium">
            {isLoading ? 'Loading Premier League teams...' : 'Select a team...'}
          </span>
        )}
        <ChevronDown
          size={18}
          className={clsx(
            'text-[var(--text-muted)] transition-transform duration-300',
            open && 'rotate-180 text-[#60a5fa]'
          )}
        />
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute z-50 w-full mt-2 rounded-2xl border border-[var(--border)] bg-[var(--navy-900)] shadow-2xl overflow-hidden backdrop-blur-2xl animate-scale-in">
          {/* Search */}
          <div className="p-3 border-b border-[var(--border)]">
            <div className="flex items-center gap-2.5 px-3 py-2 bg-[var(--navy-800)] rounded-xl border border-[var(--border)]">
              <Search size={16} className="text-[var(--text-muted)]" />
              <input
                autoFocus
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Filter Premier League teams..."
                className="flex-1 bg-transparent text-sm font-medium text-white placeholder-[var(--text-muted)] outline-none"
              />
            </div>
          </div>

          {/* Options */}
          <div className="max-h-64 overflow-y-auto p-1">
            {isLoading ? (
              <div className="flex justify-center py-8">
                <Spinner size="sm" />
              </div>
            ) : filtered.length === 0 ? (
              <p className="text-center text-[var(--text-muted)] text-sm py-6">No matching teams found</p>
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
                    'w-full flex items-center gap-3 px-3.5 py-2.5 text-left rounded-xl transition-all duration-150',
                    team.id === value
                      ? 'bg-gradient-to-r from-[rgba(41,121,255,0.2)] to-[rgba(124,58,237,0.2)] text-white font-bold border border-[#2979ff]/40'
                      : 'hover:bg-[var(--glass-hover)] text-[var(--text-secondary)] hover:text-white'
                  )}
                >
                  <div className="w-8 h-8 rounded-lg bg-[var(--navy-700)] border border-[var(--border)] flex items-center justify-center text-xs font-bold text-white shrink-0">
                    {team.short_name || team.name.slice(0, 3).toUpperCase()}
                  </div>
                  <span className="text-sm font-semibold">{team.name}</span>
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
