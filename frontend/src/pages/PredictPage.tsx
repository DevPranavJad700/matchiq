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

  const handleReset = () => {
    setResult(null);
    mutation.reset();
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black text-white">
          Match <span className="text-[#2979ff]">Predictor</span>
        </h1>
        <p className="text-[var(--text-secondary)] mt-2">
          Select two teams to get an AI-powered match outcome prediction with SHAP explanations
        </p>
      </div>

      {/* Team selection */}
      <div className="glass-card p-6">
        <div className="grid md:grid-cols-[1fr_auto_1fr] gap-4 items-end">
          <TeamSelector
            id="home-team-selector"
            label="🏠 Home Team"
            value={homeTeamId}
            onChange={setHomeTeamId}
            excludeId={awayTeamId}
          />

          <div className="flex flex-col items-center justify-center pb-1">
            <div className="w-10 h-10 rounded-full bg-[var(--navy-700)] border border-[var(--border)] flex items-center justify-center">
              <span className="text-[var(--text-muted)] text-sm font-bold">VS</span>
            </div>
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
        <div className="mt-6 flex items-center gap-3">
          <button
            id="predict-button"
            onClick={handlePredict}
            disabled={!canPredict || mutation.isPending}
            className="flex items-center gap-2 px-8 py-3 rounded-xl font-semibold text-white transition-all
              bg-[#2979ff] hover:bg-[#5c9cff] disabled:opacity-40 disabled:cursor-not-allowed
              shadow-[0_0_20px_rgba(41,121,255,0.3)] hover:shadow-[0_0_32px_rgba(41,121,255,0.5)]"
          >
            {mutation.isPending ? (
              <>
                <Spinner size="sm" />
                Predicting...
              </>
            ) : (
              <>
                <Zap size={18} />
                Predict Match
              </>
            )}
          </button>

          {result && (
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-3 rounded-xl font-medium text-[var(--text-secondary)] hover:text-white transition-colors border border-[var(--border)] hover:border-[var(--navy-500)]"
            >
              <RefreshCw size={15} />
              New Prediction
            </button>
          )}
        </div>

        {/* Validation hint */}
        {homeTeamId && awayTeamId && homeTeamId === awayTeamId && (
          <p className="mt-2 text-[#ff4444] text-sm flex items-center gap-1">
            <AlertCircle size={14} />
            Home and away teams must be different
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
        <div className="grid lg:grid-cols-2 gap-6 animate-[fadeIn_0.3s_ease]">
          {/* Prediction card */}
          <div className="space-y-4">
            <SectionHeader title="Prediction Result" />
            <PredictionCard prediction={result} />

            {/* Quick stats */}
            <div className="glass-card p-4 grid grid-cols-3 gap-3">
              {[
                { label: `${result.home_team.name} Win`, value: `${Math.round(result.probabilities.home_win * 100)}%`, color: '#2979ff' },
                { label: 'Draw', value: `${Math.round(result.probabilities.draw * 100)}%`, color: '#ffc107' },
                { label: `${result.away_team.name} Win`, value: `${Math.round(result.probabilities.away_win * 100)}%`, color: '#ff4444' },
              ].map((item) => (
                <div key={item.label} className="text-center">
                  <p className="text-2xl font-black stat-number" style={{ color: item.color }}>{item.value}</p>
                  <p className="text-[var(--text-muted)] text-xs mt-0.5 leading-tight">{item.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* SHAP explanation */}
          <div>
            <SectionHeader
              title="Key Factors"
              subtitle="SHAP feature importance — how each factor influenced this prediction"
            />
            <div className="glass-card p-5">
              <ShapExplanationChart factors={result.explanation} />
              {result.explanation.length === 0 && (
                <p className="text-[var(--text-muted)] text-sm text-center py-4">
                  Train the model to see SHAP explanations
                </p>
              )}
            </div>

            {/* Model metadata */}
            <div className="glass-card p-4 mt-4 flex items-center justify-between">
              <div>
                <p className="text-[var(--text-muted)] text-xs uppercase tracking-wider">Model Version</p>
                <p className="text-white text-sm font-medium mt-0.5">{result.model_version || 'Unknown'}</p>
              </div>
              <div className="text-right">
                <p className="text-[var(--text-muted)] text-xs uppercase tracking-wider">Confidence</p>
                <p className="text-white text-sm font-medium mt-0.5">{result.confidence}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instruction state (no selection) */}
      {!result && !mutation.isPending && (
        <div className="glass-card p-12 text-center">
          <div className="text-6xl mb-4">⚽</div>
          <h3 className="text-white font-bold text-xl mb-2">Select Two Teams to Predict</h3>
          <p className="text-[var(--text-secondary)] text-sm max-w-md mx-auto">
            Choose a home team and an away team above, then click "Predict Match" to get an
            AI-powered outcome prediction with SHAP feature explanations.
          </p>
        </div>
      )}
    </div>
  );
}
