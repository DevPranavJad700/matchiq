/**
 * API service layer — all HTTP calls go through here.
 * Uses the Vite proxy (/api → localhost:8000) in dev.
 * In production, set VITE_API_URL env var.
 */

import type {
  DatasetProvenance,
  Health,
  League,
  LeagueAnalytics,
  Match,
  ModelInfo,
  PaginatedMatches,
  Prediction,
  RecentPrediction,
  Team,
  TeamForm,
  TeamStatistics,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ─── Health & System ──────────────────────────────────────────────────────────

export const api = {
  getHealth: () => fetchJSON<Health>('/health'),
  getModelInfo: () => fetchJSON<ModelInfo>('/model/info'),
  getProvenance: () => fetchJSON<DatasetProvenance>('/system/provenance'),

  // ─── Teams ──────────────────────────────────────────────────────────────────
  getTeams: (leagueId?: number) =>
    fetchJSON<Team[]>(`/teams${leagueId ? `?league_id=${leagueId}` : ''}`),

  getTeam: (id: number) => fetchJSON<Team>(`/teams/${id}`),

  getTeamForm: (id: number, limit = 5) =>
    fetchJSON<TeamForm>(`/teams/${id}/form?limit=${limit}`),

  getTeamStatistics: (id: number) =>
    fetchJSON<TeamStatistics>(`/teams/${id}/statistics`),

  // ─── Matches ─────────────────────────────────────────────────────────────────
  getMatches: (params?: {
    league_id?: number;
    season_id?: number;
    team_id?: number;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.league_id) query.set('league_id', String(params.league_id));
    if (params?.season_id) query.set('season_id', String(params.season_id));
    if (params?.team_id) query.set('team_id', String(params.team_id));
    if (params?.page) query.set('page', String(params.page));
    if (params?.page_size) query.set('page_size', String(params.page_size));
    return fetchJSON<PaginatedMatches>(`/matches?${query}`);
  },

  getMatch: (id: number) => fetchJSON<Match>(`/matches/${id}`),

  getMatchH2H: (id: number) =>
    fetchJSON<{ id: number; date: string; home_team: string; away_team: string; home_score: number; away_score: number; result: string }[]>(
      `/matches/${id}/head-to-head`
    ),

  // ─── Leagues ─────────────────────────────────────────────────────────────────
  getLeagues: () => fetchJSON<League[]>('/leagues'),
  getLeague: (id: number) => fetchJSON<League>(`/leagues/${id}`),
  getLeagueSeasons: (id: number) =>
    fetchJSON<{ id: number; year: string; league_id: number }[]>(`/leagues/${id}/seasons`),
  getLeagueAnalytics: (id: number, season?: string) =>
    fetchJSON<LeagueAnalytics>(`/analytics/league/${id}${season ? `?season=${encodeURIComponent(season)}` : ''}`),

  // ─── Predictions ─────────────────────────────────────────────────────────────
  predict: (homeTeamId: number, awayTeamId: number) =>
    fetchJSON<Prediction>('/predict', {
      method: 'POST',
      body: JSON.stringify({ home_team_id: homeTeamId, away_team_id: awayTeamId }),
    }),

  getRecentPredictions: () => fetchJSON<RecentPrediction[]>('/predict/recent'),
  getPrediction: (id: number) => fetchJSON<Prediction>(`/predict/${id}`),
};

export default api;
