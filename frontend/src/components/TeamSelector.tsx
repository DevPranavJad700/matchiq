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
          'w-full flex items-center justify-between px-3.5 py-3 rounded-lg border transition-colors',
          'bg-[#171B1F] text-left',
          open
            ? 'border-[#54C878] ring-1 ring-[#54C878]'
            : 'border-[var(--border)] hover:border-[var(--border-strong)]'
        )}
      >
        {selected ? (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-[#111417] border border-[var(--border-strong)] flex items-center justify-center text-xs font-bold text-[#F4F5F2]">
              {selected.short_name || selected.name.slice(0, 3).toUpperCase()}
            </div>
            <span className="font-semibold text-[#F4F5F2] text-sm">{selected.name}</span>
          </div>
        ) : (
          <span className="text-[#5C636A] font-medium text-sm">
            {isLoading ? 'Loading Premier League teams...' : 'Select a team...'}
          </span>
        )}
        <ChevronDown
          size={16}
          className={clsx(
            'text-[#5C636A] transition-transform duration-200',
            open && 'rotate-180 text-[#54C878]'
          )}
        />
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute z-50 w-full mt-1.5 rounded-lg border border-[var(--border-strong)] bg-[#111417] shadow-xl overflow-hidden animate-fade-in">
          {/* Search */}
          <div className="p-2 border-b border-[var(--border)]">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-[#171B1F] rounded-md border border-[var(--border)]">
              <Search size={14} className="text-[#5C636A]" />
              <input
                autoFocus
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search teams..."
                className="flex-1 bg-transparent text-xs font-medium text-[#F4F5F2] placeholder-[#5C636A] outline-none"
              />
            </div>
          </div>

          {/* Options */}
          <div className="max-h-60 overflow-y-auto p-1">
            {isLoading ? (
              <div className="flex justify-center py-6">
                <Spinner size="sm" />
              </div>
            ) : filtered.length === 0 ? (
              <p className="text-center text-[#5C636A] text-xs py-4">No matching teams found</p>
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
                    'w-full flex items-center gap-2.5 px-3 py-2 text-left rounded-md transition-colors',
                    team.id === value
                      ? 'bg-[#171B1F] text-[#F4F5F2] font-semibold border-l-2 border-[#54C878]'
                      : 'hover:bg-[#1E2329] text-[#9DA4AA] hover:text-[#F4F5F2]'
                  )}
                >
                  <div className="w-7 h-7 rounded bg-[#171B1F] border border-[var(--border)] flex items-center justify-center text-xs font-bold text-[#F4F5F2] shrink-0">
                    {team.short_name || team.name.slice(0, 3).toUpperCase()}
                  </div>
                  <span className="text-xs font-medium">{team.name}</span>
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
