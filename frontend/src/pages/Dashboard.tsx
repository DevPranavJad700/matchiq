import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Zap, Users, Calendar, TrendingUp, ChevronRight } from 'lucide-react';
import api from '../services/api';
import { StatCard, ErrorBanner, PageLoader, Badge } from '../components/ui';
import { MatchCard } from '../components/PredictionCard';
import type { RecentPrediction } from '../types';

export function Dashboard() {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30_000,
  });

  const { data: teams } = useQuery({
    queryKey: ['teams'],
    queryFn: () => api.getTeams(),
    staleTime: 5 * 60 * 1000,
  });

  const { data: leagues } = useQuery({
    queryKey: ['leagues'],
    queryFn: () => api.getLeagues(),
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

  if (healthLoading) return <PageLoader />;

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="gradient-border p-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-black tracking-tight">
              <span className="text-white">Match</span>
              <span className="gradient-text">IQ</span>
            </h1>
            <p className="text-[var(--text-secondary)] mt-2 text-lg">
              Predict football match outcomes using historical team performance & ML
            </p>
            <p className="text-[var(--text-muted)] text-sm mt-1">
              Powered by XGBoost · SHAP explanations · 3 seasons of Premier League data
            </p>
          </div>
          <Link
            to="/predict"
            id="hero-predict-cta"
            className="flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-white transition-all
              bg-[#2979ff] hover:bg-[#5c9cff] shadow-[0_0_24px_rgba(41,121,255,0.4)] hover:shadow-[0_0_36px_rgba(41,121,255,0.6)]
              pulse-glow"
          >
            <Zap size={18} />
            Predict a Match
          </Link>
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

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Teams"
          value={teams?.length ?? '—'}
          sub={leagues?.[0]?.name}
          icon={<Users size={16} />}
          accent="blue"
        />
        <StatCard
          label="Total Matches"
          value={matches?.total ?? '—'}
          sub="Completed matches"
          icon={<Calendar size={16} />}
        />
        <StatCard
          label="Model Accuracy"
          value={modelInfo?.accuracy ? `${(modelInfo.accuracy * 100).toFixed(1)}%` : '—'}
          sub={modelInfo?.algorithm ?? 'Not trained'}
          icon={<TrendingUp size={16} />}
          accent="green"
        />
        <StatCard
          label="Predictions Made"
          value={predictions?.length ?? 0}
          sub="All time"
          icon={<Zap size={16} />}
          accent="amber"
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent matches */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-white font-bold text-lg">Recent Matches</h2>
            <Link to="/matches" className="text-[#2979ff] text-sm hover:text-white flex items-center gap-1 transition-colors">
              View all <ChevronRight size={14} />
            </Link>
          </div>
          <div className="space-y-2">
            {matches?.items.map((m) => <MatchCard key={m.id} match={m} />) ?? (
              <p className="text-[var(--text-muted)] text-sm">No matches available</p>
            )}
          </div>
        </div>

        {/* Recent predictions */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-white font-bold text-lg">Recent Predictions</h2>
            <Link to="/predict" className="text-[#2979ff] text-sm hover:text-white flex items-center gap-1 transition-colors">
              New prediction <ChevronRight size={14} />
            </Link>
          </div>
          <div className="space-y-2">
            {predictions && predictions.length > 0 ? predictions.map((p) => (
              <PredictionListItem key={p.id} prediction={p} />
            )) : (
              <div className="glass-card p-8 text-center">
                <p className="text-4xl mb-3">🔮</p>
                <p className="text-[var(--text-secondary)] font-medium">No predictions yet</p>
                <p className="text-[var(--text-muted)] text-sm mt-1">
                  Head to the predictor to make your first prediction
                </p>
                <Link to="/predict" className="inline-block mt-4 text-[#2979ff] text-sm hover:underline">
                  Make a prediction →
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Model info */}
      {modelInfo && (
        <div className="glass-card p-6">
          <h2 className="text-white font-bold text-lg mb-4">Model Information</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-[var(--text-muted)] text-xs uppercase tracking-wider">Algorithm</p>
              <p className="text-white font-semibold mt-1">{modelInfo.algorithm.replace(/_/g, ' ')}</p>
            </div>
            <div>
              <p className="text-[var(--text-muted)] text-xs uppercase tracking-wider">Accuracy</p>
              <p className="text-[#00e676] font-bold mt-1 text-lg stat-number">
                {modelInfo.accuracy ? `${(modelInfo.accuracy * 100).toFixed(1)}%` : '—'}
              </p>
            </div>
            <div>
              <p className="text-[var(--text-muted)] text-xs uppercase tracking-wider">F1 Score</p>
              <p className="text-[#2979ff] font-bold mt-1 text-lg stat-number">
                {modelInfo.f1_score ? modelInfo.f1_score.toFixed(3) : '—'}
              </p>
            </div>
            <div>
              <p className="text-[var(--text-muted)] text-xs uppercase tracking-wider">Log Loss</p>
              <p className="text-[#ffc107] font-bold mt-1 text-lg stat-number">
                {modelInfo.log_loss ? modelInfo.log_loss.toFixed(3) : '—'}
              </p>
            </div>
          </div>
        </div>
      )}
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
    <Link to={`/predict`} className="glass-card p-4 flex items-center gap-3 hover:border-[var(--navy-500)] transition-all">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-white text-sm font-medium truncate">{prediction.home_team.name}</span>
          <span className="text-[var(--text-muted)] text-xs">vs</span>
          <span className="text-white text-sm font-medium truncate">{prediction.away_team.name}</span>
        </div>
        <p className="text-[var(--text-muted)] text-xs mt-1">
          {prediction.predicted_result.replace('_', ' ')} · {Math.round(maxProb * 100)}%
        </p>
      </div>
      <Badge variant={confidenceBadge[prediction.confidence] ?? 'neutral'}>
        {prediction.confidence}
      </Badge>
    </Link>
  );
}
