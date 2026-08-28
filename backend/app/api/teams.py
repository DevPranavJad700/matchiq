"""Teams API router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.team_repository import TeamRepository
from app.schemas.schemas import (
    FormResult,
    TeamFormOut,
    TeamOut,
    TeamStatisticsOut,
    TeamSummary,
)

router = APIRouter(prefix="/teams", tags=["teams"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[TeamOut])
def list_teams(
    league_id: int | None = Query(None, description="Filter by league ID"),
    db: Session = Depends(get_db),
):
    """List all teams, optionally filtered by league."""
    repo = TeamRepository(db)
    return repo.get_all(league_id=league_id)


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Get a specific team by ID."""
    repo = TeamRepository(db)
    team = repo.get_by_id(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    return team


@router.get("/{team_id}/form", response_model=TeamFormOut)
def get_team_form(
    team_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Get a team's recent form (last N matches)."""
    repo = TeamRepository(db)
    team = repo.get_by_id(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

    recent = repo.get_recent_matches(team_id, limit=limit)
    results: list[FormResult] = []
    pts = wins = draws = losses = gf = ga = 0

    for m in recent:
        is_home = m.home_team_id == team_id
        opponent = m.away_team if is_home else m.home_team
        stat = next((s for s in m.statistics if s.team_id == team_id), None)

        goals_scored = stat.goals if stat else None
        goals_conceded = stat.goals_conceded if stat else None

        if m.result == "H" and is_home:
            r, pts = "W", pts + 3
            wins += 1
        elif m.result == "A" and not is_home:
            r, pts = "W", pts + 3
            wins += 1
        elif m.result == "D":
            r, pts = "D", pts + 1
            draws += 1
        else:
            r = "L"
            losses += 1

        gf += goals_scored or 0
        ga += goals_conceded or 0

        results.append(FormResult(
            match_id=m.id,
            date=m.match_date,
            opponent=opponent.name,
            home_or_away="H" if is_home else "A",
            goals_scored=goals_scored,
            goals_conceded=goals_conceded,
            result=r,
        ))

    return TeamFormOut(
        team=TeamSummary(id=team.id, name=team.name, short_name=team.short_name),
        recent_results=results,
        points_last_5=pts,
        wins_last_5=wins,
        draws_last_5=draws,
        losses_last_5=losses,
        goal_difference_last_5=gf - ga,
    )


@router.get("/{team_id}/statistics", response_model=TeamStatisticsOut)
def get_team_statistics(team_id: int, db: Session = Depends(get_db)):
    """Get aggregate statistics for a team."""
    repo = TeamRepository(db)
    team = repo.get_by_id(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

    standing = repo.get_latest_standing(team_id)
    agg = repo.get_aggregate_statistics(team_id)
    rates = repo.get_home_away_win_rates(team_id)

    return TeamStatisticsOut(
        team=TeamSummary(id=team.id, name=team.name, short_name=team.short_name),
        season_year=standing.season.year if standing else None,
        position=standing.position if standing else None,
        points=standing.points if standing else None,
        played=standing.played if standing else None,
        won=standing.won if standing else None,
        drawn=standing.drawn if standing else None,
        lost=standing.lost if standing else None,
        goals_for=standing.goals_for if standing else None,
        goals_against=standing.goals_against if standing else None,
        goal_difference=standing.goal_difference if standing else None,
        **agg,
        **rates,
    )
