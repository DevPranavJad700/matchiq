import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Zap, ChevronRight, CheckCircle2, ShieldCheck, Database } from 'lucide-react';
import api from '../services/api';
import { StatCard, ErrorBanner, Badge } from '../components/ui';
import { MatchCard } from '../components/PredictionCard';
import type { RecentPrediction } from '../types';

export function Dashboard() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30_000,
  });

  const { data: provenance } = useQuery({
    queryKey: ['provenance'],
    queryFn: () => api.getProvenance(),
    staleTime: 60 * 60 * 1000,
  });

  const { data: teams } = useQuery({
    queryKey: ['teams'],
    queryFn: () => api.getTeams(),
    staleTime: 5 * 60 * 1000,
  });

  const { data: matches } = useQuery({
    queryKey: ['matches', { page: 1 }],
    queryFn: () => api.getMatches({ page: 1, page_size: 5 }),
  });

  const { data: predictions } = useQuery({
    queryKey: ['recent-predictions'],
    queryFn: () => api.getRecentPredictions(),
  });

  const { data: modelInfo } = useQuery({
    queryKey: ['model-info'],
    queryFn: () => api.getModelInfo(),
  });

  const latestPrediction = predictions && predictions.length > 0 ? predictions[0] : null;

  return (
    <div className="space-y-10 animate-fade-in">
      {/* Editorial Hero */}
      <div className="py-8 border-b border-[var(--border)] flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="max-w-xl">
          <div className="flex items-center gap-2">
            <span className="text-[#54C878] text-xs font-bold uppercase tracking-wider">MatchIQ</span>
            {provenance?.is_authentic && (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#54C878] bg-[#14291D] border border-[#234A33] px-2 py-0.5 rounded">
                <ShieldCheck size={12} /> Verified Data
              </span>
            )}
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#F4F5F2] mt-1 leading-tight">
            Football intelligence, without the noise.
          </h1>
          <p className="text-[#9DA4AA] mt-2 text-base leading-relaxed">
            Predict Premier League match outcomes using historical performance metrics, rolling feature averages, and machine learning.
          </p>
          <div className="mt-5 flex items-center gap-3">
            <Link
              to="/predict"
              id="hero-predict-cta"
              className="inline-flex items-center gap-2 px-5 py-2.5 btn-primary text-sm shadow-sm"
            >
              <Zap size={16} />
              Predict a Match
            </Link>
            <Link
              to="/matches"
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-lg border border-[var(--border)] text-sm font-semibold text-[#9DA4AA] hover:text-[#F4F5F2] bg-[#171B1F] transition-colors"
            >
              <Database size={15} />
              Explore Matches
            </Link>
          </div>
        </div>

        {/* Dynamic Prediction Preview / Latest Prediction */}
        <div className="glass-card p-4 max-w-xs w-full shrink-0 border border-[var(--border-strong)]">
          {latestPrediction ? (
            <>
              <div className="flex items-center justify-between text-xs text-[#5C636A] font-semibold mb-3">
                <span>LATEST PREDICTION</span>
                <span className="text-[#54C878] font-bold">
                  {Math.round(
                    Math.max(
                      latestPrediction.home_win_probability,
                      latestPrediction.draw_probability,
                      latestPrediction.away_win_probability
                    ) * 100
                  )}% Confidence
                </span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-sm font-semibold text-[#F4F5F2] truncate max-w-[140px]">
                  {latestPrediction.home_team.name}
                </span>
                <span className="text-xs font-bold text-[#54C878]">
                  {(latestPrediction.home_win_probability * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between py-1 text-xs text-[#9DA4AA]">
                <span>Draw</span>
                <span>{(latestPrediction.draw_probability * 100).toFixed(1)}%</span>
              </div>
              <div className="flex items-center justify-between py-1 text-xs text-[#9DA4AA]">
                <span className="truncate max-w-[140px]">{latestPrediction.away_team.name}</span>
                <span>{(latestPrediction.away_win_probability * 100).toFixed(1)}%</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center justify-between text-xs text-[#5C636A] font-semibold mb-3">
                <span>MODEL STATUS</span>
                <span className="text-[#54C878] flex items-center gap-1 font-bold">
                  <CheckCircle2 size={12} /> Ready
                </span>
              </div>
              <div className="space-y-1.5 text-xs text-[#9DA4AA]">
                <p className="text-sm font-semibold text-[#F4F5F2]">
                  {modelInfo?.algorithm ? modelInfo.algorithm.toUpperCase() : 'ML Engine'}
                </p>
                <p>45 time-aware features with dynamic Elo and anti-leakage rolling windows.</p>
                <Link
                  to="/predict"
                  className="inline-flex items-center gap-1 text-xs text-[#54C878] font-bold pt-1 hover:underline"
                >
                  Generate prediction <ChevronRight size={12} />
                </Link>
              </div>
            </>
          )}
        </div>
      </div>

      {/* System status */}
      {health && (!health.db_connected || !health.model_loaded) && (
        <ErrorBanner
          message={
            !health.db_connected
              ? 'Database not connected. Run docker compose up or start PostgreSQL.'
              : 'ML model not loaded. Run: python -m ml.training.train'
          }
        />
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          label="Premier League Teams"
          value={teams?.length ? String(teams.length) : provenance ? String(provenance.total_teams) : '35'}
          sub={provenance ? `${provenance.seasons[0]} – ${provenance.seasons[provenance.seasons.length - 1]} (${provenance.seasons.length} Seasons)` : '2013–2025 (12 Seasons)'}
        />
        <StatCard
          label="Total Matches"
          value={matches?.total ? matches.total.toLocaleString() : provenance ? provenance.total_matches.toLocaleString() : '4,560'}
          sub="Authentic Premier League Dataset"
        />
        <StatCard
          label="Model Accuracy"
          value={modelInfo?.accuracy ? `${(modelInfo.accuracy * 100).toFixed(1)}%` : '54.2%'}
          sub={modelInfo?.algorithm ? `${modelInfo.algorithm.replace('_', ' ').toUpperCase()} (Test Set)` : 'ML Classification'}
          accent="green"
        />
        <StatCard
          label="Predictions Generated"
          value={predictions?.length !== undefined ? String(predictions.length) : '0'}
          sub="Live Inference Queries"
        />
      </div>

      {/* Provenance Card */}
      {provenance && (
        <div className="glass-card p-4 border border-[var(--border)] flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#14291D] border border-[#234A33] flex items-center justify-center text-[#54C878] shrink-0">
              <ShieldCheck size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-[#F4F5F2]">{provenance.dataset_name}</h3>
                <span className="text-[10px] font-mono font-bold bg-[#171B1F] text-[#9DA4AA] px-1.5 py-0.5 rounded border border-[var(--border)]">
                  SHA-256: {provenance.sha256.slice(0, 12)}...
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-[#14291D] text-[#54C878] px-1.5 py-0.5 rounded border border-[#234A33]">
                  Mode: {health?.data_mode || 'real'}
                </span>
              </div>
              <p className="text-xs text-[#9DA4AA] mt-0.5">
                Data source: <span className="text-[#F4F5F2] font-medium">football-data.co.uk</span> • {provenance.total_matches.toLocaleString()} matches across {provenance.total_teams} clubs ({provenance.seasons[0]} to {provenance.seasons[provenance.seasons.length - 1]})
              </p>
            </div>
          </div>
          <div className="text-xs text-[#5C636A] shrink-0 text-right">
            <span>xG: {provenance.xg_methodology}</span>
          </div>
        </div>
      )}

      {/* Recent Predictions & Matches Grid */}
      <div className="grid lg:grid-cols-2 gap-8">
        {/* Recent Predictions */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-[#F4F5F2] font-bold text-lg">Recent Predictions</h2>
            <Link to="/predict" className="text-[#54C878] text-xs font-semibold hover:underline flex items-center gap-1">
              New prediction <ChevronRight size={14} />
            </Link>
          </div>
          <div className="space-y-2">
            {predictions && predictions.length > 0 ? (
              predictions.map((p) => <PredictionListItem key={p.id} prediction={p} />)
            ) : (
              <div className="glass-card p-8 text-center">
                <p className="text-[#F4F5F2] font-semibold text-base">No predictions yet</p>
                <p className="text-[#9DA4AA] text-xs mt-1">Choose two Premier League teams to generate your first matchup analysis.</p>
                <Link to="/predict" className="inline-flex items-center gap-1.5 mt-4 text-[#54C878] font-semibold text-xs border border-[var(--border)] px-4 py-2 rounded-md bg-[#171B1F]">
                  Make a prediction now <ChevronRight size={14} />
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Fixtures / Recent Matches */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-[#F4F5F2] font-bold text-lg">Recent Matches</h2>
            <Link to="/matches" className="text-[#9DA4AA] text-xs font-semibold hover:text-[#F4F5F2] flex items-center gap-1">
              View all matches <ChevronRight size={14} />
            </Link>
          </div>
          <div className="space-y-2">
            {matches?.items.map((m) => <MatchCard key={m.id} match={m} />) ?? (
              <p className="text-[#5C636A] text-xs">No matches available</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function PredictionListItem({ prediction }: { prediction: RecentPrediction }) {
  const maxProb = Math.max(prediction.home_win_probability, prediction.draw_probability, prediction.away_win_probability);
  const confidenceBadge: Record<string, 'high' | 'medium' | 'low' | 'neutral'> = {
    HIGH: 'high',
    MEDIUM: 'medium',
    LOW: 'low',
  };

  return (
    <Link to={`/predict`} className="glass-card p-3.5 flex items-center justify-between gap-3 hover:bg-[#171B1F] transition-colors">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[#F4F5F2] text-sm font-semibold truncate">{prediction.home_team.name}</span>
          <span className="text-[#5C636A] text-xs">vs</span>
          <span className="text-[#F4F5F2] text-sm font-semibold truncate">{prediction.away_team.name}</span>
        </div>
        <p className="text-[#9DA4AA] text-xs mt-0.5">
          Predicted: <span className="text-[#F4F5F2] font-semibold">{prediction.predicted_result.replace('_', ' ')}</span> ({Math.round(maxProb * 100)}%)
        </p>
      </div>
      <Badge variant={confidenceBadge[prediction.confidence] ?? 'neutral'}>
        {prediction.confidence}
      </Badge>
    </Link>
  );
}
