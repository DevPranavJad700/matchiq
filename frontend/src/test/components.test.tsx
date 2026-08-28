import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StatCard, Badge, FormDot, ErrorBanner, EmptyState } from '../components/ui';
import { PredictionCard, ShapExplanationChart } from '../components/PredictionCard';
import type { Prediction, ExplanationFactor } from '../types';

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
}

// ─── UI Primitives Tests ─────────────────────────────────────────────────────

describe('UI Primitives', () => {
  it('renders StatCard with label and value', () => {
    render(<StatCard label="Total Goals" value="42" sub="Avg 2.5/match" accent="green" />);
    expect(screen.getByText('Total Goals')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('Avg 2.5/match')).toBeInTheDocument();
  });

  it('renders Badge with correct variant class', () => {
    render(<Badge variant="win">WIN</Badge>);
    const badge = screen.getByText('WIN');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge-win');
  });

  it('renders FormDot with W, D, L results', () => {
    render(
      <div>
        <FormDot result="W" />
        <FormDot result="D" />
        <FormDot result="L" />
      </div>
    );
    expect(screen.getByText('W')).toBeInTheDocument();
    expect(screen.getByText('D')).toBeInTheDocument();
    expect(screen.getByText('L')).toBeInTheDocument();
  });

  it('renders ErrorBanner with message and handles retry', () => {
    const onRetry = vi.fn();
    render(<ErrorBanner message="Network connection failed" onRetry={onRetry} />);
    expect(screen.getByText('Network connection failed')).toBeInTheDocument();
    
    const retryBtn = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('renders EmptyState with title and message', () => {
    render(<EmptyState title="No Teams Found" message="Please seed the database" />);
    expect(screen.getByText('No Teams Found')).toBeInTheDocument();
    expect(screen.getByText('Please seed the database')).toBeInTheDocument();
  });
});

// ─── PredictionCard Tests ────────────────────────────────────────────────────

describe('PredictionCard Component', () => {
  const samplePrediction: Prediction = {
    id: 1,
    home_team: { id: 1, name: 'Arsenal FC', short_name: 'ARS' },
    away_team: { id: 2, name: 'Chelsea FC', short_name: 'CHE' },
    probabilities: { home_win: 0.55, draw: 0.25, away_win: 0.20 },
    predicted_result: 'HOME_WIN',
    confidence: 'MEDIUM',
    model_version: 'random_forest-v20260828',
    explanation: [
      { feature: 'form_diff', value: 3.0, impact: 0.15, description: 'Home form advantage of 3.00 pts' },
      { feature: 'home_avg_goals_scored', value: 2.1, impact: 0.10, description: 'Home team scores 2.10 goals/match' }
    ],
    created_at: '2026-08-28T20:00:00Z'
  };

  it('renders team names, confidence badge, and probabilities', () => {
    const Wrapper = createWrapper();
    render(<PredictionCard prediction={samplePrediction} />, { wrapper: Wrapper });

    expect(screen.getAllByText('Arsenal FC')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Chelsea FC')[0]).toBeInTheDocument();
    expect(screen.getByText('MEDIUM confidence')).toBeInTheDocument();
    expect(screen.getByText('55%')).toBeInTheDocument();
    expect(screen.getByText('25%')).toBeInTheDocument();
    expect(screen.getByText('20%')).toBeInTheDocument();
    expect(screen.getByText('Home Win — 55%')).toBeInTheDocument();
  });

  it('renders SHAP explanation chart correctly', () => {
    const factors: ExplanationFactor[] = [
      { feature: 'form_diff', value: 3.0, impact: 0.15, description: 'Home form advantage' },
      { feature: 'away_avg_goals_conceded', value: 1.8, impact: -0.08, description: 'Away defence' }
    ];

    render(<ShapExplanationChart factors={factors} />);
    expect(screen.getByText('Form Diff')).toBeInTheDocument();
    expect(screen.getByText('+0.150')).toBeInTheDocument();
    expect(screen.getByText('Away Avg Goals Conceded')).toBeInTheDocument();
    expect(screen.getByText('-0.080')).toBeInTheDocument();
  });
});
