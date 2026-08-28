"""Repository for match database operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.orm_models import Match, TeamMatchStatistic


class MatchRepository:
    """Handles all database queries related to matches."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(
        self,
        league_id: int | None = None,
        season_id: int | None = None,
        team_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Match], int]:
        stmt = (
            select(Match)
            .options(joinedload(Match.home_team), joinedload(Match.away_team))
            .order_by(Match.match_date.desc())
        )
        count_stmt = select(Match)

        if league_id is not None:
            stmt = stmt.where(Match.league_id == league_id)
            count_stmt = count_stmt.where(Match.league_id == league_id)
        if season_id is not None:
            stmt = stmt.where(Match.season_id == season_id)
            count_stmt = count_stmt.where(Match.season_id == season_id)
        if team_id is not None:
            cond = (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = len(list(self.db.execute(count_stmt).scalars().all()))
        matches = list(self.db.execute(stmt.offset(offset).limit(limit)).unique().scalars().all())
        return matches, total

    def get_by_id(self, match_id: int) -> Match | None:
        stmt = (
            select(Match)
            .options(
                joinedload(Match.home_team),
                joinedload(Match.away_team),
                joinedload(Match.statistics),
                joinedload(Match.predictions),
            )
            .where(Match.id == match_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_head_to_head(
        self, team_a_id: int, team_b_id: int, limit: int = 10
    ) -> list[Match]:
        """Get recent H2H matches between two teams."""
        stmt = (
            select(Match)
            .options(joinedload(Match.home_team), joinedload(Match.away_team))
            .where(
                (
                    (Match.home_team_id == team_a_id) & (Match.away_team_id == team_b_id)
                )
                | (
                    (Match.home_team_id == team_b_id) & (Match.away_team_id == team_a_id)
                ),
                Match.result.isnot(None),
            )
            .order_by(Match.match_date.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).unique().scalars().all())
