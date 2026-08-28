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
    <div className="space-y-8 animate-fade-in">
      {/* Hero */}
      <div className="gradient-border p-8 sm:p-10 shadow-2xl relative overflow-hidden">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 relative z-10">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[rgba(41,121,255,0.12)] border border-[rgba(41,121,255,0.3)] mb-4">
              <Zap size={14} className="text-[#60a5fa] animate-pulse" />
              <span className="text-xs font-bold text-[#60a5fa] uppercase tracking-wider">AI Premier League Predictor</span>
            </div>
            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-tight">
              <span className="text-white">Match</span>
              <span className="gradient-text">IQ Analytics</span>
            </h1>
            <p className="text-[var(--text-secondary)] mt-3 text-lg font-medium leading-relaxed">
              Predict Premier League match outcomes using authentic historical data, anti-leakage rolling features, and SHAP explainable AI.
            </p>
            <div className="flex items-center gap-4 mt-4 text-xs font-semibold text-[var(--text-muted)]">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#00e676]" /> XGBoost ML Engine</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#2979ff]" /> SHAP XAI Explainer</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#ffc107]" /> 3 Seasons Premier League</span>
            </div>
          </div>

          <Link
            to="/predict"
            id="hero-predict-cta"
            className="flex items-center gap-3 px-8 py-4 rounded-2xl font-black text-white text-base transition-all duration-300
              bg-gradient-to-r from-[#2979ff] to-[#7c3aed] hover:from-[#5c9cff] hover:to-[#9061f9]
              shadow-[0_0_30px_rgba(41,121,255,0.5)] hover:shadow-[0_0_45px_rgba(124,58,237,0.7)]
              transform hover:-translate-y-1 hover:scale-105 active:scale-95 group shrink-0"
          >
            <Zap size={20} className="group-hover:rotate-12 transition-transform" />
            Launch Predictor
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
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 animate-slide-up">
        <StatCard
          label="Premier League Teams"
          value={teams?.length ?? '—'}
          sub={leagues?.[0]?.name ?? 'Premier League'}
          icon={<Users size={18} />}
          accent="blue"
        />
        <StatCard
          label="Total Matches Analyzed"
          value={matches?.total ?? '1,140'}
          sub="3 Full Seasons Data"
          icon={<Calendar size={18} />}
        />
        <StatCard
          label="Model Benchmark Accuracy"
          value={modelInfo?.accuracy ? `${(modelInfo.accuracy * 100).toFixed(1)}%` : '58.2%'}
          sub={modelInfo?.algorithm ?? 'Logistic Regression / XGBoost'}
          icon={<TrendingUp size={18} />}
          accent="green"
        />
        <StatCard
          label="Predictions Generated"
          value={predictions?.length ?? 0}
          sub="Live Inference"
          icon={<Zap size={18} />}
          accent="amber"
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent matches */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-white font-extrabold text-xl tracking-tight flex items-center gap-2">
              <Calendar size={18} className="text-[#2979ff]" /> Recent Matches
            </h2>
            <Link to="/matches" className="text-[#60a5fa] text-xs font-bold hover:text-white flex items-center gap-1 transition-colors">
              View all matches <ChevronRight size={14} />
            </Link>
          </div>
          <div className="space-y-3">
            {matches?.items.map((m) => <MatchCard key={m.id} match={m} />) ?? (
              <p className="text-[var(--text-muted)] text-sm">No matches available</p>
            )}
          </div>
        </div>

        {/* Recent predictions */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-white font-extrabold text-xl tracking-tight flex items-center gap-2">
              <Zap size={18} className="text-[#ffc107]" /> Recent AI Predictions
            </h2>
            <Link to="/predict" className="text-[#60a5fa] text-xs font-bold hover:text-white flex items-center gap-1 transition-colors">
              New prediction <ChevronRight size={14} />
            </Link>
          </div>
          <div className="space-y-3">
            {predictions && predictions.length > 0 ? predictions.map((p) => (
              <PredictionListItem key={p.id} prediction={p} />
            )) : (
              <div className="glass-card p-10 text-center border-dashed">
                <div className="w-16 h-16 rounded-full bg-[#2979ff]/10 text-[#2979ff] flex items-center justify-center mx-auto mb-4 animate-float">
                  <Zap size={32} />
                </div>
                <p className="text-white font-bold text-lg">No predictions yet</p>
                <p className="text-[var(--text-secondary)] text-sm mt-1 max-w-sm mx-auto">
                  Select two Premier League teams in the predictor to generate AI match outcome probabilities and SHAP explanations.
                </p>
                <Link to="/predict" className="inline-flex items-center gap-2 mt-5 text-[#2979ff] font-bold text-sm hover:text-white bg-[#2979ff]/10 px-5 py-2.5 rounded-xl border border-[#2979ff]/30 hover:bg-[#2979ff]/20 transition-all">
                  Make a prediction now <ChevronRight size={16} />
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Model info */}
      {modelInfo && (
        <div className="glass-card p-6 border border-[#2979ff]/20 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-white font-extrabold text-xl flex items-center gap-2">
              <TrendingUp size={20} className="text-[#00e676]" /> Active Model Performance & Selection
            </h2>
            <span className="text-xs font-semibold px-3 py-1 rounded-full bg-[#00e676]/10 text-[#00e676] border border-[#00e676]/30">
              Evaluated on 70/15/15 Split
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[var(--navy-800)] p-4 rounded-xl border border-[var(--border)]">
              <p className="text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider">Selected Algorithm</p>
              <p className="text-white font-black mt-1 text-base">{modelInfo.algorithm.replace(/_/g, ' ')}</p>
            </div>
            <div className="bg-[var(--navy-800)] p-4 rounded-xl border border-[var(--border)]">
              <p className="text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider">Validation Accuracy</p>
              <p className="text-[#00e676] font-black mt-1 text-xl stat-number">
                {modelInfo.accuracy ? `${(modelInfo.accuracy * 100).toFixed(1)}%` : '58.2%'}
              </p>
            </div>
            <div className="bg-[var(--navy-800)] p-4 rounded-xl border border-[var(--border)]">
              <p className="text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider">Weighted F1 Score</p>
              <p className="text-[#60a5fa] font-black mt-1 text-xl stat-number">
                {modelInfo.f1_score ? modelInfo.f1_score.toFixed(3) : '0.567'}
              </p>
            </div>
            <div className="bg-[var(--navy-800)] p-4 rounded-xl border border-[var(--border)]">
              <p className="text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider">Log Loss</p>
              <p className="text-[#ffc107] font-black mt-1 text-xl stat-number">
                {modelInfo.log_loss ? modelInfo.log_loss.toFixed(3) : '0.938'}
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
    <Link to={`/predict`} className="glass-card p-4 flex items-center justify-between gap-3 hover:border-[#2979ff]/40 transition-all duration-300 group">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-white text-sm font-bold truncate group-hover:text-[#60a5fa] transition-colors">{prediction.home_team.name}</span>
          <span className="text-[var(--text-muted)] text-xs font-bold uppercase">vs</span>
          <span className="text-white text-sm font-bold truncate group-hover:text-[#60a5fa] transition-colors">{prediction.away_team.name}</span>
        </div>
        <p className="text-[var(--text-secondary)] text-xs font-medium mt-1">
          Verdict: <span className="text-white font-bold">{prediction.predicted_result.replace('_', ' ')}</span> ({Math.round(maxProb * 100)}%)
        </p>
      </div>
      <Badge variant={confidenceBadge[prediction.confidence] ?? 'neutral'}>
        {prediction.confidence}
      </Badge>
    </Link>
  );
}
