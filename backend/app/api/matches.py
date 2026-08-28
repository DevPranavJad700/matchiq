"""Matches API router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.match_repository import MatchRepository
from app.schemas.schemas import MatchListOut, MatchOut, MatchStatOut

router = APIRouter(prefix="/matches", tags=["matches"])
logger = logging.getLogger(__name__)


@router.get("", response_model=dict)
def list_matches(
    league_id: int | None = Query(None),
    season_id: int | None = Query(None),
    team_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List matches with pagination and optional filters."""
    repo = MatchRepository(db)
    offset = (page - 1) * page_size
    matches, total = repo.get_all(
        league_id=league_id,
        season_id=season_id,
        team_id=team_id,
        limit=page_size,
        offset=offset,
    )
    items = []
    for m in matches:
        items.append(MatchListOut(
            id=m.id,
            home_team=m.home_team,
            away_team=m.away_team,
            match_date=m.match_date,
            home_score=m.home_score,
            away_score=m.away_score,
            result=m.result,
        ))

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [i.model_dump() for i in items],
    }


@router.get("/{match_id}", response_model=MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db)):
    """Get match details including statistics and predictions."""
    repo = MatchRepository(db)
    match = repo.get_by_id(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

    stats = [
        MatchStatOut(
            team_id=s.team_id,
            is_home=s.is_home,
            goals=s.goals,
            goals_conceded=s.goals_conceded,
            shots=s.shots,
            shots_on_target=s.shots_on_target,
            possession=s.possession,
            xg=s.xg,
            corners=s.corners,
            fouls=s.fouls,
            yellow_cards=s.yellow_cards,
            red_cards=s.red_cards,
        )
        for s in match.statistics
    ]

    return MatchOut(
        id=match.id,
        season_id=match.season_id,
        league_id=match.league_id,
        home_team=match.home_team,
        away_team=match.away_team,
        match_date=match.match_date,
        home_score=match.home_score,
        away_score=match.away_score,
        result=match.result,
        matchday=match.matchday,
        statistics=stats,
    )


@router.get("/{match_id}/head-to-head")
def get_h2h(match_id: int, db: Session = Depends(get_db)):
    """Get historical H2H results between the two teams in a match."""
    match_repo = MatchRepository(db)
    match = match_repo.get_by_id(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

    h2h = match_repo.get_head_to_head(match.home_team_id, match.away_team_id)
    return [
        {
            "id": m.id,
            "date": m.match_date,
            "home_team": m.home_team.name,
            "away_team": m.away_team.name,
            "home_score": m.home_score,
            "away_score": m.away_score,
            "result": m.result,
        }
        for m in h2h
    ]
