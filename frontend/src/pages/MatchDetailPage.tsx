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
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <Link to="/matches" className="flex items-center gap-1 text-[#9DA4AA] hover:text-[#F4F5F2] text-xs transition-colors">
        <ArrowLeft size={12} /> Back to Matches
      </Link>

      {/* Score card */}
      <div className="glass-card p-6 text-center border border-[var(--border)]">
        <p className="text-[#5C636A] text-xs font-medium mb-4">
          {new Date(match.match_date).toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          {match.matchday && ` · Matchday ${match.matchday}`}
        </p>
        <div className="flex items-center justify-center gap-8">
          <Link to={`/teams/${match.home_team.id}`} className="flex flex-col items-center gap-2 group">
            <div className="w-14 h-14 rounded-lg bg-[#171B1F] border border-[var(--border-strong)] flex items-center justify-center font-bold text-[#F4F5F2] text-base group-hover:border-[#54C878] transition-colors">
              {match.home_team.short_name || match.home_team.name.slice(0, 3).toUpperCase()}
            </div>
            <span className="text-[#F4F5F2] font-semibold text-sm">{match.home_team.name}</span>
            <span className="text-[#5C636A] text-xs">Home</span>
          </Link>

          <div className="flex flex-col items-center gap-1">
            {played ? (
              <span className="text-3xl font-extrabold text-[#F4F5F2] stat-number">
                {match.home_score} — {match.away_score}
              </span>
            ) : (
              <span className="text-xl font-bold text-[#5C636A]">VS</span>
            )}
            {played && <span className="text-[#F59E0B] text-xs font-semibold">{resultText}</span>}
          </div>

          <Link to={`/teams/${match.away_team.id}`} className="flex flex-col items-center gap-2 group">
            <div className="w-14 h-14 rounded-lg bg-[#171B1F] border border-[var(--border-strong)] flex items-center justify-center font-bold text-[#F4F5F2] text-base group-hover:border-[#54C878] transition-colors">
              {match.away_team.short_name || match.away_team.name.slice(0, 3).toUpperCase()}
            </div>
            <span className="text-[#F4F5F2] font-semibold text-sm">{match.away_team.name}</span>
            <span className="text-[#5C636A] text-xs">Away</span>
          </Link>
        </div>
      </div>

      {/* Stats comparison */}
      {homeStats && awayStats && (
        <div className="glass-card p-5 border border-[var(--border)]">
          <h2 className="text-[#F4F5F2] font-bold text-base mb-4">Match Statistics</h2>
          <div className="space-y-3">
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
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-[#54C878] stat-number">{decimals ? h.toFixed(decimals) : h}</span>
                    <span className="text-[#9DA4AA] font-medium">{label}</span>
                    <span className="font-semibold text-[#3B82F6] stat-number">{decimals ? a.toFixed(decimals) : a}</span>
                  </div>
                  <div className="flex h-1.5 rounded-full overflow-hidden bg-[#171B1F]">
                    <div className="h-full bg-[#54C878] transition-all" style={{ width: `${homePct}%` }} />
                    <div className="h-full bg-[#3B82F6] transition-all" style={{ width: `${awayPct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* H2H */}
      {h2h && h2h.length > 0 && (
        <div className="glass-card p-5 border border-[var(--border)]">
          <h2 className="text-[#F4F5F2] font-bold text-base mb-3">Head-to-Head History</h2>
          <div className="space-y-1">
            {h2h.map((m) => (
              <div key={m.id} className="flex items-center justify-between py-1.5 px-2.5 rounded-md hover:bg-[#171B1F] text-xs">
                <span className="text-[#9DA4AA] flex-1 truncate">{m.home_team}</span>
                <span className="font-bold text-[#F4F5F2] stat-number mx-2">{m.home_score} – {m.away_score}</span>
                <span className="text-[#9DA4AA] flex-1 text-right truncate">{m.away_team}</span>
                <span className="text-[#5C636A] ml-3 w-16 text-right">
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
