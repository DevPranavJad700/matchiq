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
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <span className="text-[#54C878] text-xs font-bold uppercase tracking-wider">MatchPredictor</span>
        <h1 className="text-3xl font-extrabold text-[#F4F5F2] tracking-tight mt-1">
          Select Matchup
        </h1>
        <p className="text-[#9DA4AA] mt-1 text-sm">
          Select home and away Premier League teams to compute win probabilities and SHAP feature drivers.
        </p>
      </div>

      {/* Team selection */}
      <div className="glass-card p-6 border border-[var(--border)]">
        <div className="grid md:grid-cols-[1fr_auto_1fr] gap-4 items-end">
          <TeamSelector
            id="home-team-selector"
            label="Home Team"
            value={homeTeamId}
            onChange={setHomeTeamId}
            excludeId={awayTeamId}
          />

          <div className="flex flex-col items-center justify-center pb-0.5">
            <button
              type="button"
              onClick={handleSwap}
              disabled={!homeTeamId && !awayTeamId}
              title="Swap Teams"
              className="p-2.5 rounded-md bg-[#171B1F] border border-[var(--border)] text-[#9DA4AA] hover:text-[#F4F5F2] transition-colors disabled:opacity-40"
            >
              <RefreshCw size={16} />
            </button>
          </div>

          <TeamSelector
            id="away-team-selector"
            label="Away Team"
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
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-8 py-3 btn-primary text-sm shadow-sm disabled:opacity-40"
          >
            {mutation.isPending ? (
              <>
                <Spinner size="sm" />
                Evaluating Matchup...
              </>
            ) : (
              <>
                <Zap size={16} />
                Predict Match
              </>
            )}
          </button>

          {result && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-4 py-3 rounded-md text-xs font-semibold text-[#9DA4AA] hover:text-[#F4F5F2] bg-[#171B1F] border border-[var(--border)] transition-colors"
            >
              <RefreshCw size={14} />
              Reset Selection
            </button>
          )}
        </div>

        {/* Validation hint */}
        {homeTeamId && awayTeamId && homeTeamId === awayTeamId && (
          <p className="mt-3 text-[#EF4444] text-xs font-medium flex items-center gap-1.5 bg-[#EF4444]/10 p-2.5 rounded-md border border-[#EF4444]/20">
            <AlertCircle size={14} />
            Please select two different Premier League teams.
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
        <div className="grid md:grid-cols-2 gap-6 animate-slide-up">
          {/* Prediction card */}
          <div className="space-y-4">
            <SectionHeader title="Match Outcome Verdict" subtitle="Computed probabilities based on historical data" />
            <PredictionCard prediction={result} />
          </div>

          {/* SHAP explanation */}
          <div className="space-y-4">
            <SectionHeader
              title={`Why the model leans ${result.predicted_result === 'HOME_WIN' ? result.home_team.name : result.predicted_result === 'AWAY_WIN' ? result.away_team.name : 'Draw'}`}
              subtitle="Feature importance drivers"
            />
            <div className="glass-card p-5 border border-[var(--border)]">
              <ShapExplanationChart factors={result.explanation} />
              {result.explanation.length === 0 && (
                <p className="text-[#5C636A] text-xs text-center py-4">
                  Run ML model training to generate SHAP explanation factors.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Instruction state (no selection) */}
      {!result && !mutation.isPending && (
        <div className="glass-card p-10 text-center">
          <h3 className="text-[#F4F5F2] font-semibold text-lg mb-1">No prediction generated yet</h3>
          <p className="text-[#9DA4AA] text-sm max-w-sm mx-auto">
            Choose two Premier League teams above to analyze match outcome probabilities and SHAP key factors.
          </p>
        </div>
      )}
    </div>
  );
}
