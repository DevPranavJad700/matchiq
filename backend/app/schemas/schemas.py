"""Pydantic schemas for API request/response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ─── League Schemas ────────────────────────────────────────────────────────────

class LeagueBase(BaseModel):
    name: str
    short_name: str | None = None
    country: str


class LeagueOut(LeagueBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ─── Season Schemas ────────────────────────────────────────────────────────────

class SeasonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    league_id: int
    year: str


# ─── Team Schemas ──────────────────────────────────────────────────────────────

class TeamBase(BaseModel):
    name: str
    short_name: str | None = None
    country: str | None = None
    league_id: int | None = None


class TeamOut(TeamBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class TeamSummary(BaseModel):
    """Lightweight team reference used in nested responses."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    short_name: str | None = None


class FormResult(BaseModel):
    """A single match result in a team's form sequence."""
    match_id: int
    date: datetime
    opponent: str
    home_or_away: str  # H or A
    goals_scored: int | None
    goals_conceded: int | None
    result: str  # W, D, L


class TeamFormOut(BaseModel):
    team: TeamSummary
    recent_results: list[FormResult]
    points_last_5: int
    wins_last_5: int
    draws_last_5: int
    losses_last_5: int
    goal_difference_last_5: int


class TeamStatisticsOut(BaseModel):
    team: TeamSummary
    season_year: str | None
    position: int | None
    points: int | None
    played: int | None
    won: int | None
    drawn: int | None
    lost: int | None
    goals_for: int | None
    goals_against: int | None
    goal_difference: int | None
    avg_goals_scored: float | None
    avg_goals_conceded: float | None
    avg_shots: float | None
    avg_shots_on_target: float | None
    avg_possession: float | None
    avg_xg: float | None
    home_win_rate: float | None
    away_win_rate: float | None


# ─── Match Schemas ─────────────────────────────────────────────────────────────

class MatchStatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    team_id: int
    is_home: bool
    goals: int | None
    goals_conceded: int | None
    shots: int | None
    shots_on_target: int | None
    possession: float | None
    xg: float | None
    corners: int | None
    fouls: int | None
    yellow_cards: int | None
    red_cards: int | None


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    season_id: int
    league_id: int
    home_team: TeamSummary
    away_team: TeamSummary
    match_date: datetime
    home_score: int | None
    away_score: int | None
    result: str | None
    matchday: int | None
    statistics: list[MatchStatOut] = []


class MatchListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    home_team: TeamSummary
    away_team: TeamSummary
    match_date: datetime
    home_score: int | None
    away_score: int | None
    result: str | None


# ─── Prediction Schemas ────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    home_team_id: int = Field(..., description="Database ID of the home team")
    away_team_id: int = Field(..., description="Database ID of the away team")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"home_team_id": 1, "away_team_id": 2}
        }
    )


class ExplanationFactor(BaseModel):
    feature: str
    value: float
    impact: float
    description: str


class ProbabilitiesOut(BaseModel):
    home_win: float
    draw: float
    away_win: float


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    home_team: TeamSummary
    away_team: TeamSummary
    probabilities: ProbabilitiesOut
    predicted_result: str  # HOME_WIN / DRAW / AWAY_WIN
    confidence: str  # HIGH / MEDIUM / LOW
    model_version: str | None
    explanation: list[ExplanationFactor]
    created_at: datetime


# ─── Model Info Schemas ────────────────────────────────────────────────────────

class ModelInfoOut(BaseModel):
    name: str
    version_tag: str
    algorithm: str
    training_date: datetime | None
    accuracy: float | None
    f1_score: float | None
    log_loss: float | None
    features: list[str]
    is_active: bool


# ─── Analytics Schemas ─────────────────────────────────────────────────────────

class LeagueTableRow(BaseModel):
    position: int
    team: TeamSummary
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int


class LeagueAnalyticsOut(BaseModel):
    league: LeagueOut
    season: str
    table: list[LeagueTableRow]
    top_scorers_teams: list[dict]  # team name + avg goals
    best_defences_teams: list[dict]


# ─── Health Schemas ────────────────────────────────────────────────────────────

class HealthOut(BaseModel):
    status: str
    version: str
    db_connected: bool
    model_loaded: bool
    data_mode: str = "real"


# ─── Provenance Schemas ────────────────────────────────────────────────────────

class MatchSummaryDetail(BaseModel):
    date: str
    fixture: str
    result: str


class ProvenanceOut(BaseModel):
    dataset_name: str
    source_urls: dict[str, str]
    retrieved_at: str
    sha256: str
    total_matches: int
    total_teams: int
    teams: list[str]
    seasons: list[str]
    season_match_counts: dict[str, int]
    date_range: dict[str, str]
    first_match: MatchSummaryDetail
    last_match: MatchSummaryDetail
    is_authentic: bool
    data_mode: str
    xg_methodology: str


# ─── Pagination ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list
