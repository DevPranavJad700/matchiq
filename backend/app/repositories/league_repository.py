"""Repository for leagues and predictions."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.orm_models import League, ModelVersion, Prediction, Season, Standing


class LeagueRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> list[League]:
        return list(self.db.execute(select(League)).scalars().all())

    def get_by_id(self, league_id: int) -> League | None:
        return self.db.execute(
            select(League).where(League.id == league_id)
        ).scalar_one_or_none()

    def get_seasons(self, league_id: int) -> list[Season]:
        """Get all seasons for a league ordered by most recent first."""
        return list(self.db.execute(
            select(Season)
            .where(Season.league_id == league_id)
            .order_by(Season.id.desc())
        ).scalars().all())

    def get_standings(
        self,
        league_id: int,
        season_id: int | None = None,
        season_year: str | None = None,
    ) -> list[Standing]:
        """Get standings ordered by position for a league and season."""
        if season_year:
            matched_season = self.db.execute(
                select(Season).where(Season.league_id == league_id, Season.year == season_year)
            ).scalar_one_or_none()
            if matched_season:
                season_id = matched_season.id

        # Get latest season if not specified
        if season_id is None:
            latest_season = self.db.execute(
                select(Season)
                .where(Season.league_id == league_id)
                .order_by(Season.id.desc())
                .limit(1)
            ).scalar_one_or_none()
            if latest_season is None:
                return []
            season_id = latest_season.id

        stmt = (
            select(Standing)
            .options(joinedload(Standing.team), joinedload(Standing.season))
            .where(Standing.season_id == season_id)
            .order_by(Standing.position)
        )
        return list(self.db.execute(stmt).unique().scalars().all())


class PredictionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, prediction: Prediction) -> Prediction:
        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)
        return prediction

    def get_by_id(self, prediction_id: int) -> Prediction | None:
        stmt = (
            select(Prediction)
            .options(
                joinedload(Prediction.home_team),
                joinedload(Prediction.away_team),
                joinedload(Prediction.model_version),
            )
            .where(Prediction.id == prediction_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_recent(self, limit: int = 10) -> list[Prediction]:
        stmt = (
            select(Prediction)
            .options(
                joinedload(Prediction.home_team),
                joinedload(Prediction.away_team),
            )
            .order_by(Prediction.created_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    def get_active_model_version(self) -> ModelVersion | None:
        return self.db.execute(
            select(ModelVersion).where(ModelVersion.is_active == True)  # noqa: E712
        ).scalar_one_or_none()
