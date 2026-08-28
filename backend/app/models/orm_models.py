"""SQLAlchemy ORM models for MatchIQ database schema."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_name: Mapped[str] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    teams: Mapped[list["Team"]] = relationship("Team", back_populates="league")
    seasons: Mapped[list["Season"]] = relationship("Season", back_populates="league")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="league")

    __table_args__ = (UniqueConstraint("name", "country", name="uq_league_name_country"),)


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    league_id: Mapped[int] = mapped_column(Integer, ForeignKey("leagues.id"), nullable=False)
    year: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g. "2023-24"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    league: Mapped["League"] = relationship("League", back_populates="seasons")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="season")
    standings: Mapped[list["Standing"]] = relationship("Standing", back_populates="season")

    __table_args__ = (UniqueConstraint("league_id", "year", name="uq_season_league_year"),)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_name: Mapped[str] = mapped_column(String(10), nullable=True)
    country: Mapped[str] = mapped_column(String(50), nullable=True)
    league_id: Mapped[int] = mapped_column(Integer, ForeignKey("leagues.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    league: Mapped["League"] = relationship("League", back_populates="teams")
    home_matches: Mapped[list["Match"]] = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches: Mapped[list["Match"]] = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    statistics: Mapped[list["TeamMatchStatistic"]] = relationship("TeamMatchStatistic", back_populates="team")
    standings: Mapped[list["Standing"]] = relationship("Standing", back_populates="team")

    __table_args__ = (UniqueConstraint("name", "league_id", name="uq_team_name_league"),)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    season_id: Mapped[int] = mapped_column(Integer, ForeignKey("seasons.id"), nullable=False)
    league_id: Mapped[int] = mapped_column(Integer, ForeignKey("leagues.id"), nullable=False)
    home_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    match_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # result: H = home win, D = draw, A = away win, null = not played
    result: Mapped[str | None] = mapped_column(String(1), nullable=True)
    matchday: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    season: Mapped["Season"] = relationship("Season", back_populates="matches")
    league: Mapped["League"] = relationship("League", back_populates="matches")
    home_team: Mapped["Team"] = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team: Mapped["Team"] = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    statistics: Mapped[list["TeamMatchStatistic"]] = relationship("TeamMatchStatistic", back_populates="match")
    predictions: Mapped[list["Prediction"]] = relationship("Prediction", back_populates="match")

    __table_args__ = (
        UniqueConstraint("season_id", "home_team_id", "away_team_id", name="uq_match_season_teams"),
        Index("ix_matches_match_date", "match_date"),
        Index("ix_matches_home_team", "home_team_id"),
        Index("ix_matches_away_team", "away_team_id"),
    )


class TeamMatchStatistic(Base):
    __tablename__ = "team_match_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    is_home: Mapped[bool] = mapped_column(Boolean, nullable=False)

    goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals_conceded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots_on_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    possession: Mapped[float | None] = mapped_column(Float, nullable=True)
    xg: Mapped[float | None] = mapped_column(Float, nullable=True)
    corners: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fouls: Mapped[int | None] = mapped_column(Integer, nullable=True)
    yellow_cards: Mapped[int | None] = mapped_column(Integer, nullable=True)
    red_cards: Mapped[int | None] = mapped_column(Integer, nullable=True)

    match: Mapped["Match"] = relationship("Match", back_populates="statistics")
    team: Mapped["Team"] = relationship("Team", back_populates="statistics")

    __table_args__ = (
        UniqueConstraint("match_id", "team_id", name="uq_team_match_stat"),
        Index("ix_team_match_stats_team", "team_id"),
    )


class Standing(Base):
    __tablename__ = "standings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    season_id: Mapped[int] = mapped_column(Integer, ForeignKey("seasons.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    played: Mapped[int] = mapped_column(Integer, default=0)
    won: Mapped[int] = mapped_column(Integer, default=0)
    drawn: Mapped[int] = mapped_column(Integer, default=0)
    lost: Mapped[int] = mapped_column(Integer, default=0)
    goals_for: Mapped[int] = mapped_column(Integer, default=0)
    goals_against: Mapped[int] = mapped_column(Integer, default=0)
    goal_difference: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    season: Mapped["Season"] = relationship("Season", back_populates="standings")
    team: Mapped["Team"] = relationship("Team", back_populates="standings")

    __table_args__ = (UniqueConstraint("season_id", "team_id", name="uq_standing_season_team"),)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version_tag: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    training_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    f1_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    log_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    features_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    predictions: Mapped[list["Prediction"]] = relationship("Prediction", back_populates="model_version")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("matches.id"), nullable=True)
    home_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    model_version_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("model_versions.id"), nullable=True)

    home_win_probability: Mapped[float] = mapped_column(Float, nullable=False)
    draw_probability: Mapped[float] = mapped_column(Float, nullable=False)
    away_win_probability: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_result: Mapped[str] = mapped_column(String(10), nullable=False)  # HOME_WIN / DRAW / AWAY_WIN
    confidence: Mapped[str | None] = mapped_column(String(10), nullable=True)  # HIGH / MEDIUM / LOW
    explanation_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    match: Mapped["Match | None"] = relationship("Match", back_populates="predictions")
    model_version: Mapped["ModelVersion | None"] = relationship("ModelVersion", back_populates="predictions")
    home_team: Mapped["Team"] = relationship("Team", foreign_keys=[home_team_id])
    away_team: Mapped["Team"] = relationship("Team", foreign_keys=[away_team_id])

    __table_args__ = (Index("ix_predictions_created_at", "created_at"),)
