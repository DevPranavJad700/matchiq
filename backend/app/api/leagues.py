"""Leagues and analytics API routers."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.league_repository import LeagueRepository
from app.schemas.schemas import LeagueOut, LeagueTableRow, TeamSummary

router = APIRouter(prefix="/leagues", tags=["leagues"])
analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[LeagueOut])
def list_leagues(db: Session = Depends(get_db)):
    """List all available leagues."""
    repo = LeagueRepository(db)
    return repo.get_all()


@router.get("/{league_id}", response_model=LeagueOut)
def get_league(league_id: int, db: Session = Depends(get_db)):
    """Get a specific league by ID."""
    repo = LeagueRepository(db)
    league = repo.get_by_id(league_id)
    if league is None:
        raise HTTPException(status_code=404, detail=f"League {league_id} not found")
    return league


@router.get("/{league_id}/seasons")
def list_league_seasons(league_id: int, db: Session = Depends(get_db)):
    """List all available seasons for a league."""
    repo = LeagueRepository(db)
    seasons = repo.get_seasons(league_id)
    return [{"id": s.id, "year": s.year, "league_id": s.league_id} for s in seasons]


@analytics_router.get("/league/{league_id}")
def get_league_analytics(
    league_id: int,
    season_id: int | None = Query(None),
    season: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get league analytics including standings table, top scorers, best defences."""
    repo = LeagueRepository(db)
    league = repo.get_by_id(league_id)
    if league is None:
        raise HTTPException(status_code=404, detail=f"League {league_id} not found")

    all_seasons = repo.get_seasons(league_id)
    available_seasons = [s.year for s in all_seasons]

    standings = repo.get_standings(league_id, season_id=season_id, season_year=season)

    table = [
        LeagueTableRow(
            position=s.position,
            team=TeamSummary(id=s.team.id, name=s.team.name, short_name=s.team.short_name),
            played=s.played,
            won=s.won,
            drawn=s.drawn,
            lost=s.lost,
            goals_for=s.goals_for,
            goals_against=s.goals_against,
            goal_difference=s.goal_difference,
            points=s.points,
        )
        for s in standings
    ]

    # Top scoring teams (avg goals for)
    top_scorers = sorted(
        [{"team": s.team.name, "avg_goals": round(s.goals_for / max(s.played, 1), 2)} for s in standings],
        key=lambda x: x["avg_goals"],
        reverse=True,
    )[:5]

    # Best defences (lowest avg conceded)
    best_defences = sorted(
        [{"team": s.team.name, "avg_conceded": round(s.goals_against / max(s.played, 1), 2)} for s in standings],
        key=lambda x: x["avg_conceded"],
    )[:5]

    season_year = standings[0].season.year if standings else (season or "N/A")

    return {
        "league": LeagueOut(
            id=league.id,
            name=league.name,
            short_name=league.short_name,
            country=league.country,
            created_at=league.created_at,
        ),
        "season": season_year,
        "available_seasons": available_seasons,
        "table": [r.model_dump() for r in table],
        "top_scorers_teams": top_scorers,
        "best_defences_teams": best_defences,
    }
