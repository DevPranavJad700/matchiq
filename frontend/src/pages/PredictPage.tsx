import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Zap, AlertCircle, RefreshCw } from 'lucide-react';
import api from '../services/api';
import type { Prediction } from '../types';
import { TeamSelector } from '../components/TeamSelector';
import { PredictionCard, ShapExplanationChart } from '../components/PredictionCard';
import { ErrorBanner, SectionHeader, Spinner } from '../components/ui';

export function PredictPage() {
  const [homeTeamId, setHomeTeamId] = useState<number | null>(null);
  const [awayTeamId, setAwayTeamId] = useState<number | null>(null);
  const [result, setResult] = useState<Prediction | null>(null);

  const mutation = useMutation({
    mutationFn: () => api.predict(homeTeamId!, awayTeamId!),
    onSuccess: (data) => setResult(data),
  });

  const canPredict = homeTeamId !== null && awayTeamId !== null && homeTeamId !== awayTeamId;

  const handlePredict = () => {
    if (!canPredict) return;
    mutation.mutate();
  };

  const handleSwap = () => {
    const temp = homeTeamId;
    setHomeTeamId(awayTeamId);
    setAwayTeamId(temp);
    setResult(null);
  };

  const handleReset = () => {
    setResult(null);
    mutation.reset();
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[rgba(41,121,255,0.12)] border border-[rgba(41,121,255,0.3)] mb-3">
          <Zap size={14} className="text-[#60a5fa]" />
          <span className="text-xs font-bold text-[#60a5fa] uppercase tracking-wider">Inference Engine</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Match <span className="gradient-text">Predictor</span>
        </h1>
        <p className="text-[var(--text-secondary)] mt-2 text-base font-medium">
          Select two Premier League teams to generate live AI match outcome probabilities and SHAP feature explanations.
        </p>
      </div>

      {/* Team selection */}
      <div className="glass-card p-6 sm:p-8 shadow-2xl border border-[#2979ff]/25 relative">
        <div className="grid md:grid-cols-[1fr_auto_1fr] gap-6 items-end">
          <TeamSelector
            id="home-team-selector"
            label="🏠 Home Team"
            value={homeTeamId}
            onChange={setHomeTeamId}
            excludeId={awayTeamId}
          />

          <div className="flex flex-col items-center justify-center pb-1">
            <button
              type="button"
              onClick={handleSwap}
              disabled={!homeTeamId && !awayTeamId}
              title="Swap Teams"
              className="w-12 h-12 rounded-2xl bg-[var(--navy-800)] border border-[var(--border)] flex items-center justify-center text-white hover:text-[#60a5fa] hover:border-[#2979ff]/50 hover:scale-110 active:rotate-180 transition-all duration-300 shadow-md disabled:opacity-40 disabled:hover:scale-100"
            >
              <RefreshCw size={18} />
            </button>
          </div>

          <TeamSelector
            id="away-team-selector"
            label="✈️ Away Team"
            value={awayTeamId}
            onChange={setAwayTeamId}
            excludeId={homeTeamId}
          />
        </div>

        {/* Predict button */}
        <div className="mt-8 flex items-center gap-4">
          <button
            id="predict-button"
            onClick={handlePredict}
            disabled={!canPredict || mutation.isPending}
            className="flex-1 sm:flex-none flex items-center justify-center gap-3 px-10 py-4 rounded-2xl font-black text-white text-base transition-all duration-300
              bg-gradient-to-r from-[#2979ff] to-[#7c3aed] hover:from-[#5c9cff] hover:to-[#9061f9]
              disabled:opacity-40 disabled:cursor-not-allowed
              shadow-[0_0_24px_rgba(41,121,255,0.4)] hover:shadow-[0_0_40px_rgba(124,58,237,0.6)]
              transform hover:-translate-y-0.5 active:scale-95 group"
          >
            {mutation.isPending ? (
              <>
                <Spinner size="sm" />
                Calculating Match Odds...
              </>
            ) : (
              <>
                <Zap size={20} className="group-hover:rotate-12 transition-transform" />
                Run AI Match Prediction
              </>
            )}
          </button>

          {result && (
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-5 py-4 rounded-2xl font-bold text-sm text-[var(--text-secondary)] hover:text-white transition-all bg-[var(--navy-800)] border border-[var(--border)] hover:border-[#2979ff]/40 shadow-md"
            >
              <RefreshCw size={16} />
              Reset Selection
            </button>
          )}
        </div>

        {/* Validation hint */}
        {homeTeamId && awayTeamId && homeTeamId === awayTeamId && (
          <p className="mt-3 text-[#ff4444] text-sm font-semibold flex items-center gap-2 bg-[#ff4444]/10 p-3 rounded-xl border border-[#ff4444]/30">
            <AlertCircle size={16} />
            Please select two different Premier League teams for prediction.
          </p>
        )}
      </div>

      {/* Error */}
      {mutation.isError && (
        <ErrorBanner
          message={mutation.error instanceof Error ? mutation.error.message : 'Prediction failed'}
          onRetry={() => mutation.mutate()}
        />
      )}

      {/* Result */}
      {result && (
        <div className="grid lg:grid-cols-2 gap-8 animate-scale-in">
          {/* Prediction card */}
          <div className="space-y-6">
            <SectionHeader title="Match Outcome Verdict" subtitle="Calculated probabilities based on 39 anti-leakage rolling features" />
            <PredictionCard prediction={result} />

            {/* Quick stats */}
            <div className="glass-card p-5 grid grid-cols-3 gap-4 border border-[var(--border)]">
              {[
                { label: `${result.home_team.name} Win`, value: `${Math.round(result.probabilities.home_win * 100)}%`, color: '#2979ff' },
                { label: 'Draw Probability', value: `${Math.round(result.probabilities.draw * 100)}%`, color: '#ffc107' },
                { label: `${result.away_team.name} Win`, value: `${Math.round(result.probabilities.away_win * 100)}%`, color: '#ff4444' },
              ].map((item) => (
                <div key={item.label} className="text-center p-3 rounded-xl bg-[var(--navy-800)] border border-[var(--border)]">
                  <p className="text-3xl font-black stat-number tracking-tight" style={{ color: item.color }}>{item.value}</p>
                  <p className="text-[var(--text-secondary)] text-xs font-bold mt-1 leading-tight">{item.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* SHAP explanation */}
          <div className="space-y-6">
            <SectionHeader
              title="Explainable AI (SHAP)"
              subtitle="Feature importance drivers contributing to this prediction"
            />
            <div className="glass-card p-6 border border-[var(--border)] shadow-xl">
              <ShapExplanationChart factors={result.explanation} />
              {result.explanation.length === 0 && (
                <p className="text-[var(--text-muted)] text-sm text-center py-6 font-medium">
                  Run ML model training (`python -m ml.training.train`) to generate SHAP explanation factors.
                </p>
              )}
            </div>

            {/* Model metadata */}
            <div className="glass-card p-5 flex items-center justify-between border border-[var(--border)]">
              <div>
                <p className="text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider">Inference Model</p>
                <p className="text-white text-sm font-bold mt-0.5">{result.model_version || 'XGBoost v1.2'}</p>
              </div>
              <div className="text-right">
                <p className="text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider">Confidence Class</p>
                <span className="text-[#00e676] text-sm font-black mt-0.5 inline-block px-2.5 py-0.5 rounded-full bg-[#00e676]/10 border border-[#00e676]/30">
                  {result.confidence} CONFIDENCE
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instruction state (no selection) */}
      {!result && !mutation.isPending && (
        <div className="glass-card p-12 text-center border-dashed">
          <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-[#2979ff]/20 to-[#7c3aed]/20 text-[#60a5fa] flex items-center justify-center mx-auto mb-4 animate-float shadow-xl border border-[#2979ff]/30">
            <Zap size={40} />
          </div>
          <h3 className="text-white font-black text-2xl mb-2">Select Two Premier League Teams</h3>
          <p className="text-[var(--text-secondary)] text-base font-medium max-w-md mx-auto leading-relaxed">
            Choose a home and away team in the selector above to analyze match outcome probabilities with feature-level SHAP explanation bars.
          </p>
        </div>
      )}
    </div>
  );
}
