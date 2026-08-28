import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';
import api from '../services/api';
import { PageLoader, ErrorBanner } from '../components/ui';

export function MatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const matchId = parseInt(id ?? '0');

  const { data: match, isLoading, error } = useQuery({
    queryKey: ['match', matchId],
    queryFn: () => api.getMatch(matchId),
    enabled: !!matchId,
  });

  const { data: h2h } = useQuery({
    queryKey: ['match-h2h', matchId],
    queryFn: () => api.getMatchH2H(matchId),
    enabled: !!matchId,
  });

  if (isLoading) return <PageLoader />;
  if (error || !match) return <ErrorBanner message="Match not found" />;

  const homeStats = match.statistics.find((s) => s.is_home);
  const awayStats = match.statistics.find((s) => !s.is_home);
  const played = match.result !== null;
  const resultText = match.result === 'H' ? `${match.home_team.name} Win` : match.result === 'A' ? `${match.away_team.name} Win` : 'Draw';

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link to="/matches" className="flex items-center gap-1 text-[var(--text-muted)] hover:text-white text-sm transition-colors">
        <ArrowLeft size={14} /> Back to Matches
      </Link>

      {/* Score card */}
      <div className="glass-card p-8 text-center">
        <p className="text-[var(--text-muted)] text-sm mb-4">
          {new Date(match.match_date).toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          {match.matchday && ` · Matchday ${match.matchday}`}
        </p>
        <div className="flex items-center justify-center gap-8">
          <Link to={`/teams/${match.home_team.id}`} className="flex flex-col items-center gap-2 group">
            <div className="w-16 h-16 rounded-2xl bg-[var(--navy-700)] flex items-center justify-center font-bold text-white text-xl group-hover:bg-[#2979ff]/20 transition-colors">
              {match.home_team.short_name || match.home_team.name.slice(0, 3).toUpperCase()}
            </div>
            <span className="text-white font-semibold text-sm">{match.home_team.name}</span>
            <span className="text-[var(--text-muted)] text-xs">Home</span>
          </Link>

          <div className="flex flex-col items-center gap-2">
            {played ? (
              <span className="text-4xl font-black text-white stat-number">
                {match.home_score} — {match.away_score}
              </span>
            ) : (
              <span className="text-2xl font-bold text-[var(--text-muted)]">VS</span>
            )}
            {played && <span className="text-[#ffc107] text-sm font-medium">{resultText}</span>}
          </div>

          <Link to={`/teams/${match.away_team.id}`} className="flex flex-col items-center gap-2 group">
            <div className="w-16 h-16 rounded-2xl bg-[var(--navy-700)] flex items-center justify-center font-bold text-white text-xl group-hover:bg-[#ff4444]/20 transition-colors">
              {match.away_team.short_name || match.away_team.name.slice(0, 3).toUpperCase()}
            </div>
            <span className="text-white font-semibold text-sm">{match.away_team.name}</span>
            <span className="text-[var(--text-muted)] text-xs">Away</span>
          </Link>
        </div>
      </div>

      {/* Stats comparison */}
      {homeStats && awayStats && (
        <div className="glass-card p-6">
          <h2 className="text-white font-bold text-lg mb-5">Match Statistics</h2>
          <div className="space-y-4">
            {[
              { label: 'Shots', home: homeStats.shots, away: awayStats.shots },
              { label: 'Shots on Target', home: homeStats.shots_on_target, away: awayStats.shots_on_target },
              { label: 'Possession (%)', home: homeStats.possession, away: awayStats.possession },
              { label: 'xG', home: homeStats.xg, away: awayStats.xg, decimals: 2 },
              { label: 'Corners', home: homeStats.corners, away: awayStats.corners },
              { label: 'Fouls', home: homeStats.fouls, away: awayStats.fouls },
              { label: 'Yellow Cards', home: homeStats.yellow_cards, away: awayStats.yellow_cards },
            ].map(({ label, home, away, decimals }) => {
              if (home == null && away == null) return null;
              const h = Number(home ?? 0);
              const a = Number(away ?? 0);
              const total = h + a || 1;
              const homePct = (h / total) * 100;
              const awayPct = (a / total) * 100;

              return (
                <div key={label}>
                  <div className="flex items-center justify-between text-sm mb-1.5">
                    <span className="font-medium text-[#2979ff] stat-number">{decimals ? h.toFixed(decimals) : h}</span>
                    <span className="text-[var(--text-muted)] text-xs">{label}</span>
                    <span className="font-medium text-[#ff4444] stat-number">{decimals ? a.toFixed(decimals) : a}</span>
                  </div>
                  <div className="flex h-2 rounded-full overflow-hidden bg-[var(--navy-700)]">
                    <div className="h-full bg-[#2979ff] transition-all" style={{ width: `${homePct}%` }} />
                    <div className="h-full bg-[#ff4444] transition-all" style={{ width: `${awayPct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* H2H */}
      {h2h && h2h.length > 0 && (
        <div className="glass-card p-5">
          <h2 className="text-white font-bold text-lg mb-4">Head-to-Head History</h2>
          <div className="space-y-2">
            {h2h.map((m) => (
              <div key={m.id} className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-[var(--glass-hover)]">
                <span className="text-[var(--text-secondary)] text-sm flex-1">{m.home_team}</span>
                <span className="font-bold text-white stat-number mx-3">{m.home_score} – {m.away_score}</span>
                <span className="text-[var(--text-secondary)] text-sm flex-1 text-right">{m.away_team}</span>
                <span className="text-[var(--text-muted)] text-xs ml-4 w-20 text-right">
                  {new Date(m.date).toLocaleDateString('en-GB', { month: 'short', year: '2-digit' })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
