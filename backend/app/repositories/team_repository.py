"""Repository for team database operations."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.orm_models import (
    Match,
    Season,
    Standing,
    Team,
    TeamMatchStatistic,
)


class TeamRepository:
    """Handles all database queries related to teams."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self, league_id: int | None = None) -> list[Team]:
        stmt = select(Team).options(joinedload(Team.league))
        if league_id is not None:
            stmt = stmt.where(Team.league_id == league_id)
        return list(self.db.execute(stmt).unique().scalars().all())

    def get_by_id(self, team_id: int) -> Team | None:
        stmt = select(Team).options(joinedload(Team.league)).where(Team.id == team_id)
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_recent_matches(self, team_id: int, limit: int = 10) -> list[Match]:
        """Get recent completed matches for a team, ordered by date descending."""
        stmt = (
            select(Match)
            .options(
                joinedload(Match.home_team),
                joinedload(Match.away_team),
                joinedload(Match.statistics),
            )
            .where(
                ((Match.home_team_id == team_id) | (Match.away_team_id == team_id)),
                Match.result.isnot(None),
            )
            .order_by(Match.match_date.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    def get_latest_standing(self, team_id: int) -> Standing | None:
        """Get the most recent standing entry for a team."""
        stmt = (
            select(Standing)
            .options(joinedload(Standing.season))
            .where(Standing.team_id == team_id)
            .order_by(Standing.updated_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_aggregate_statistics(self, team_id: int, season_id: int | None = None) -> dict:
        """Compute aggregate statistics across matches."""
        stmt = (
            select(
                func.avg(TeamMatchStatistic.goals).label("avg_goals"),
                func.avg(TeamMatchStatistic.goals_conceded).label("avg_conceded"),
                func.avg(TeamMatchStatistic.shots).label("avg_shots"),
                func.avg(TeamMatchStatistic.shots_on_target).label("avg_sot"),
                func.avg(TeamMatchStatistic.possession).label("avg_poss"),
                func.avg(TeamMatchStatistic.xg).label("avg_xg"),
            )
            .join(Match, TeamMatchStatistic.match_id == Match.id)
            .where(
                TeamMatchStatistic.team_id == team_id,
                Match.result.isnot(None),
            )
        )
        if season_id is not None:
            stmt = stmt.where(Match.season_id == season_id)

        row = self.db.execute(stmt).one()
        return {
            "avg_goals_scored": round(row.avg_goals or 0, 2),
            "avg_goals_conceded": round(row.avg_conceded or 0, 2),
            "avg_shots": round(row.avg_shots or 0, 2),
            "avg_shots_on_target": round(row.avg_sot or 0, 2),
            "avg_possession": round(row.avg_poss or 0, 2),
            "avg_xg": round(row.avg_xg or 0, 2) if row.avg_xg else None,
        }

    def get_home_away_win_rates(self, team_id: int) -> dict:
        """Calculate home and away win rates."""
        home_matches = list(self.db.execute(
            select(Match).where(Match.home_team_id == team_id, Match.result.isnot(None))
        ).scalars().all())
        away_matches = list(self.db.execute(
            select(Match).where(Match.away_team_id == team_id, Match.result.isnot(None))
        ).scalars().all())

        home_wins = sum(1 for m in home_matches if m.result == "H")
        away_wins = sum(1 for m in away_matches if m.result == "A")

        home_wr = round(home_wins / len(home_matches), 3) if home_matches else 0.0
        away_wr = round(away_wins / len(away_matches), 3) if away_matches else 0.0

        return {"home_win_rate": home_wr, "away_win_rate": away_wr}
