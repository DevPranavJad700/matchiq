"""Regression tests for training-serving feature parity."""

from datetime import datetime, timezone
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.orm_models import League, Match, Season, Team, TeamMatchStatistic
from app.services.feature_builder import FeatureBuilderService, FEATURE_NAMES
from ml.features.feature_engineering import FEATURE_NAMES as ML_FEATURE_NAMES, compute_features


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed basic data
    league = League(name="Premier League", short_name="PL", country="England")
    session.add(league)
    session.flush()

    season = Season(league_id=league.id, year="2023-24")
    session.add(season)
    session.flush()

    t1 = Team(name="Arsenal FC", short_name="ARS", league_id=league.id)
    t2 = Team(name="Chelsea FC", short_name="CHE", league_id=league.id)
    session.add_all([t1, t2])
    session.flush()

    # Create past match
    match1 = Match(
        season_id=season.id,
        league_id=league.id,
        home_team_id=t1.id,
        away_team_id=t2.id,
        match_date=datetime(2023, 9, 1, tzinfo=timezone.utc),
        home_score=2,
        away_score=1,
        result="H",
        matchday=1,
    )
    session.add(match1)
    session.flush()

    stat1 = TeamMatchStatistic(
        match_id=match1.id, team_id=t1.id, is_home=True,
        goals=2, goals_conceded=1, shots=14, shots_on_target=6, possession=55.0, xg=1.8
    )
    stat2 = TeamMatchStatistic(
        match_id=match1.id, team_id=t2.id, is_home=False,
        goals=1, goals_conceded=2, shots=9, shots_on_target=3, possession=45.0, xg=0.9
    )
    session.add_all([stat1, stat2])
    session.commit()

    yield session

    session.close()


def test_feature_names_match():
    """Ensure training and serving feature name lists are identical."""
    assert FEATURE_NAMES == ML_FEATURE_NAMES
    assert len(FEATURE_NAMES) == 39


def test_feature_builder_parity(db_session):
    """Test that FeatureBuilderService produces a valid 1x39 feature vector matching training schema."""
    service = FeatureBuilderService(db_session)
    vector = service.build_features_for_prediction(
        home_team_id=1,
        away_team_id=2,
        as_of=datetime(2023, 9, 10, tzinfo=timezone.utc),
    )

    assert isinstance(vector, np.ndarray)
    assert vector.shape == (1, 39)
    assert not np.isnan(vector).any()


def test_exact_feature_value_parity(db_session):
    """Test that serving FeatureBuilderService and batch compute_features generate identical feature values."""
    service = FeatureBuilderService(db_session)

    # 1. Serving feature vector
    as_of_date = datetime(2023, 9, 10, tzinfo=timezone.utc)
    serving_vector = service.build_features_for_prediction(
        home_team_id=1,
        away_team_id=2,
        as_of=as_of_date,
    )[0]

    # 2. Batch feature vector from raw match data
    raw_df = pd.DataFrame([
        {
            "match_id": 1,
            "match_date": datetime(2023, 9, 1, tzinfo=timezone.utc),
            "home_team_id": 1,
            "away_team_id": 2,
            "result": "H",
            "home_goals": 2,
            "away_goals": 1,
            "home_shots": 14,
            "away_shots": 9,
            "home_sot": 6,
            "away_sot": 3,
            "home_xg": 1.8,
            "away_xg": 0.9,
            "target": 0,
        },
        {
            "match_id": 2,
            "match_date": as_of_date,
            "home_team_id": 1,
            "away_team_id": 2,
            "result": None,
            "home_goals": None,
            "away_goals": None,
            "home_shots": None,
            "away_shots": None,
            "home_sot": None,
            "away_sot": None,
            "home_xg": None,
            "away_xg": None,
            "target": None,
        }
    ])

    batch_df = compute_features(raw_df)
    batch_vector = batch_df[batch_df["match_id"] == 2][FEATURE_NAMES].values[0].astype(np.float64)

    # Assert exact numerical equivalence across all 39 features
    np.testing.assert_allclose(serving_vector, batch_vector, rtol=1e-3, atol=1e-3)
