// MatchIQ TypeScript Types

export interface League {
  id: number;
  name: string;
  short_name: string | null;
  country: string;
  created_at: string;
}

export interface Season {
  id: number;
  league_id: number;
  year: string;
}

export interface Team {
  id: number;
  name: string;
  short_name: string | null;
  country: string | null;
  league_id: number | null;
  created_at: string;
}

export interface TeamSummary {
  id: number;
  name: string;
  short_name: string | null;
}

export interface FormResult {
  match_id: number;
  date: string;
  opponent: string;
  home_or_away: 'H' | 'A';
  goals_scored: number | null;
  goals_conceded: number | null;
  result: 'W' | 'D' | 'L';
}

export interface TeamForm {
  team: TeamSummary;
  recent_results: FormResult[];
  points_last_5: number;
  wins_last_5: number;
  draws_last_5: number;
  losses_last_5: number;
  goal_difference_last_5: number;
}

export interface TeamStatistics {
  team: TeamSummary;
  season_year: string | null;
  position: number | null;
  points: number | null;
  played: number | null;
  won: number | null;
  drawn: number | null;
  lost: number | null;
  goals_for: number | null;
  goals_against: number | null;
  goal_difference: number | null;
  avg_goals_scored: number | null;
  avg_goals_conceded: number | null;
  avg_shots: number | null;
  avg_shots_on_target: number | null;
  avg_possession: number | null;
  avg_xg: number | null;
  home_win_rate: number | null;
  away_win_rate: number | null;
}

export interface MatchStat {
  team_id: number;
  is_home: boolean;
  goals: number | null;
  goals_conceded: number | null;
  shots: number | null;
  shots_on_target: number | null;
  possession: number | null;
  xg: number | null;
  corners: number | null;
  fouls: number | null;
  yellow_cards: number | null;
  red_cards: number | null;
}

export interface Match {
  id: number;
  season_id: number;
  league_id: number;
  home_team: TeamSummary;
  away_team: TeamSummary;
  match_date: string;
  home_score: number | null;
  away_score: number | null;
  result: 'H' | 'D' | 'A' | null;
  matchday: number | null;
  statistics: MatchStat[];
}

export interface MatchListItem {
  id: number;
  home_team: TeamSummary;
  away_team: TeamSummary;
  match_date: string;
  home_score: number | null;
  away_score: number | null;
  result: 'H' | 'D' | 'A' | null;
}

export interface PaginatedMatches {
  total: number;
  page: number;
  page_size: number;
  items: MatchListItem[];
}

export interface Probabilities {
  home_win: number;
  draw: number;
  away_win: number;
}

export interface ExplanationFactor {
  feature: string;
  value: number;
  impact: number;
  description: string;
}

export interface Prediction {
  id: number;
  home_team: TeamSummary;
  away_team: TeamSummary;
  probabilities: Probabilities;
  predicted_result: 'HOME_WIN' | 'DRAW' | 'AWAY_WIN';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  model_version: string | null;
  explanation: ExplanationFactor[];
  created_at: string;
}

export interface RecentPrediction {
  id: number;
  home_team: TeamSummary;
  away_team: TeamSummary;
  home_win_probability: number;
  draw_probability: number;
  away_win_probability: number;
  predicted_result: string;
  confidence: string;
  created_at: string;
}

export interface ModelInfo {
  name: string;
  version_tag: string;
  algorithm: string;
  training_date: string | null;
  accuracy: number | null;
  f1_score: number | null;
  log_loss: number | null;
  features: string[];
  is_active: boolean;
}

export interface Health {
  status: string;
  version: string;
  db_connected: boolean;
  model_loaded: boolean;
}

export interface LeagueTableRow {
  position: number;
  team: TeamSummary;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
}

export interface LeagueAnalytics {
  league: League;
  season: string;
  table: LeagueTableRow[];
  top_scorers_teams: { team: string; avg_goals: number }[];
  best_defences_teams: { team: string; avg_conceded: number }[];
}
