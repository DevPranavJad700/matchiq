"""Integration tests verifying model and feature parity on authentic Premier League fixtures."""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure paths
test_dir = Path(__file__).resolve().parent
backend_dir = test_dir.parent
project_root = backend_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.base import Base
from app.models.orm_models import League, Match, Season, Team, TeamMatchStatistic
from app.services.feature_builder import FeatureBuilderService, FEATURE_NAMES
from ml.features.feature_engineering import FEATURE_NAMES as ML_FEATURE_NAMES, compute_features

CSV_PATH = project_root / "data" / "processed" / "matches_processed.csv"


@pytest.fixture
def real_fixtures_db():
    """Create in-memory SQLite DB populated with first 50 authentic Premier League matches."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    league = League(name="Premier League", short_name="PL", country="England")
    session.add(league)
    session.flush()

    season = Season(league_id=league.id, year="2018-19")
    session.add(season)
    session.flush()

    # Load authentic matches CSV
    df = pd.read_csv(CSV_PATH).head(50)

    # Use exact unique team IDs from df
    unique_teams = {}
    for _, row in df.iterrows():
        unique_teams[int(row["home_team_id"])] = row["home_team_name"]
        unique_teams[int(row["away_team_id"])] = row["away_team_name"]

    team_map = {}
    for tid, tname in unique_teams.items():
        t = Team(id=tid, name=tname, short_name=tname[:3].upper(), league_id=league.id, country="England")
        session.add(t)
        team_map[tname] = t
    session.flush()

    for _, row in df.iterrows():
        match_date = pd.to_datetime(row["match_date"]).to_pydatetime()
        if match_date.tzinfo is None:
            match_date = match_date.replace(tzinfo=timezone.utc)

        m = Match(
            id=int(row["match_id"]),
            season_id=season.id,
            league_id=league.id,
            home_team_id=int(row["home_team_id"]),
            away_team_id=int(row["away_team_id"]),
            match_date=match_date,
            home_score=int(row["home_goals"]),
            away_score=int(row["away_goals"]),
            result=str(row["result"]),
            matchday=1,
        )
        session.add(m)
        session.flush()

        session.add(TeamMatchStatistic(
            match_id=m.id, team_id=int(row["home_team_id"]), is_home=True,
            goals=int(row["home_goals"]), goals_conceded=int(row["away_goals"]),
            shots=int(row["home_shots"]), shots_on_target=int(row["home_sot"]),
            xg=float(row["home_xg"]),
        ))
        session.add(TeamMatchStatistic(
            match_id=m.id, team_id=int(row["away_team_id"]), is_home=False,
            goals=int(row["away_goals"]), goals_conceded=int(row["home_goals"]),
            shots=int(row["away_shots"]), shots_on_target=int(row["away_sot"]),
            xg=float(row["away_xg"]),
        ))

    session.commit()
    yield session, df, team_map
    session.close()


def test_historical_fixtures_integrity(real_fixtures_db):
    """Ensure dataset contains authentic opening matches for historical seasons."""
    _, df, _ = real_fixtures_db
    full_df = pd.read_csv(CSV_PATH)

    assert len(full_df) == 4940

    # 2013-14 opening match: Arsenal vs Aston Villa on 2013-08-17
    first = full_df.iloc[0]
    assert first["home_team_name"] == "Arsenal FC"
    assert first["away_team_name"] == "Aston Villa"
    assert first["home_goals"] == 1
    assert first["away_goals"] == 3
    assert "2013-08-17" in str(first["match_date"])

    # 2021-22 opening match: Brentford vs Arsenal on 2021-08-13
    brentford_match = full_df[
        (full_df["home_team_name"] == "Brentford FC") & (full_df["away_team_name"] == "Arsenal FC")
    ].iloc[0]
    assert brentford_match["home_goals"] == 2
    assert brentford_match["away_goals"] == 0
    assert "2021-08-13" in str(brentford_match["match_date"])


def test_standings_features_have_dynamic_variance(real_fixtures_db):
    """Ensure league position and points are dynamic and not constant 10.0 across all matches."""
    _, df, _ = real_fixtures_db
    features_df = compute_features(df)

    # After matchday 1, positions should have variance
    positions = features_df["home_league_position"].values
    points = features_df["home_points"].values

    assert len(np.unique(positions)) > 1, "League positions must vary across matches"
    assert np.max(points) > 0, "Accumulated points must be non-zero after matches are played"


def test_real_fixture_training_serving_parity(real_fixtures_db):
    """Ensure feature vector built by FeatureBuilderService matches batch compute_features for matching match_id."""
    session, df, team_map = real_fixtures_db
    service = FeatureBuilderService(session)

    # Pick match #30 from dataset
    target_match = df.iloc[30]
    ht_id = int(target_match["home_team_id"])
    at_id = int(target_match["away_team_id"])
    as_of = pd.to_datetime(target_match["match_date"]).to_pydatetime()
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)

    # 1. Serving feature vector
    serving_vec = service.build_features_for_prediction(
        home_team_id=ht_id,
        away_team_id=at_id,
        as_of=as_of,
    )[0]

    # 2. Batch feature vector for matching match_id
    batch_features = compute_features(df)
    batch_row = batch_features[batch_features["match_id"] == target_match["match_id"]]
    batch_vec = batch_row[FEATURE_NAMES].values.astype(np.float64)[0]

    # Verify matching shape and no NaNs
    assert serving_vec.shape == (45,)
    assert not np.isnan(serving_vec).any()
    assert not np.isnan(batch_vec).any()

    # Numerical parity
    np.testing.assert_allclose(serving_vec, batch_vec, rtol=1e-3, atol=1e-3)
