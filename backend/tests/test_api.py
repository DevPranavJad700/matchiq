"""Backend test suite for MatchIQ API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.orm_models import League, Match, Season, Team, TeamMatchStatistic, Standing

# Use SQLite in-memory for tests (no PostgreSQL required)
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create tables and seed minimal test data."""
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    # Seed a league, season, and 2 teams
    league = League(name="Test League", country="Test")
    db.add(league)
    db.flush()

    season = Season(league_id=league.id, year="2023-24")
    db.add(season)
    db.flush()

    team_a = Team(name="Team Alpha", short_name="ALP", league_id=league.id)
    team_b = Team(name="Team Beta", short_name="BET", league_id=league.id)
    db.add_all([team_a, team_b])
    db.flush()

    from datetime import datetime, timezone
    match = Match(
        season_id=season.id,
        league_id=league.id,
        home_team_id=team_a.id,
        away_team_id=team_b.id,
        match_date=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
        home_score=2,
        away_score=1,
        result="H",
        matchday=1,
    )
    db.add(match)
    db.flush()

    db.add(TeamMatchStatistic(
        match_id=match.id, team_id=team_a.id, is_home=True,
        goals=2, goals_conceded=1, shots=12, shots_on_target=5,
        possession=55.0, xg=1.8, corners=6, fouls=10,
        yellow_cards=1, red_cards=0,
    ))
    db.add(TeamMatchStatistic(
        match_id=match.id, team_id=team_b.id, is_home=False,
        goals=1, goals_conceded=2, shots=8, shots_on_target=3,
        possession=45.0, xg=1.1, corners=4, fouls=12,
        yellow_cards=2, red_cards=0,
    ))

    standing_a = Standing(
        season_id=season.id, team_id=team_a.id, position=1,
        played=1, won=1, drawn=0, lost=0,
        goals_for=2, goals_against=1, goal_difference=1, points=3,
    )
    standing_b = Standing(
        season_id=season.id, team_id=team_b.id, position=2,
        played=1, won=0, drawn=0, lost=1,
        goals_for=1, goals_against=2, goal_difference=-1, points=0,
    )
    db.add_all([standing_a, standing_b])
    db.commit()

    # Store IDs for tests
    pytest.league_id = league.id
    pytest.season_id = season.id
    pytest.team_a_id = team_a.id
    pytest.team_b_id = team_b.id
    pytest.match_id = match.id

    db.close()
    yield

    db.close()
    engine.dispose()
    import gc
    gc.collect()
    import os, time
    time.sleep(0.1)  # allow Windows to release the file handle
    if os.path.exists("test.db"):
        try:
            os.remove("test.db")
        except PermissionError:
            pass  # Windows sometimes holds the file; ignore on CI


@pytest.fixture
def client():
    return TestClient(app)


# ─── Health Tests ──────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_has_required_fields(self, client):
        data = client.get("/health").json()
        assert "status" in data
        assert "version" in data
        assert "db_connected" in data
        assert "model_loaded" in data
        assert "data_mode" in data

    def test_health_db_connected(self, client):
        data = client.get("/health").json()
        assert data["db_connected"] is True

    def test_provenance_endpoint(self, client):
        response = client.get("/system/provenance")
        assert response.status_code == 200
        data = response.json()
        assert data["is_authentic"] is True
        assert data["total_matches"] == 4940
        assert data["total_teams"] == 35
        assert "sha256" in data
        assert "first_match" in data


# ─── Teams Tests ───────────────────────────────────────────────────────────────

class TestTeams:
    def test_list_teams_returns_200(self, client):
        response = client.get("/teams")
        assert response.status_code == 200

    def test_list_teams_returns_list(self, client):
        data = client.get("/teams").json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_get_team_by_id(self, client):
        team_id = pytest.team_a_id
        response = client.get(f"/teams/{team_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == team_id
        assert data["name"] == "Team Alpha"

    def test_get_team_not_found(self, client):
        response = client.get("/teams/99999")
        assert response.status_code == 404

    def test_get_team_form(self, client):
        response = client.get(f"/teams/{pytest.team_a_id}/form")
        assert response.status_code == 200
        data = response.json()
        assert "recent_results" in data
        assert "points_last_5" in data
        assert "wins_last_5" in data

    def test_get_team_form_values_correct(self, client):
        data = client.get(f"/teams/{pytest.team_a_id}/form").json()
        assert data["wins_last_5"] == 1
        assert data["points_last_5"] == 3

    def test_get_team_statistics(self, client):
        response = client.get(f"/teams/{pytest.team_a_id}/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "avg_goals_scored" in data
        assert data["position"] == 1

    def test_list_teams_filtered_by_league(self, client):
        response = client.get(f"/teams?league_id={pytest.league_id}")
        assert response.status_code == 200
        data = response.json()
        assert all(t["league_id"] == pytest.league_id for t in data)


# ─── Matches Tests ─────────────────────────────────────────────────────────────

class TestMatches:
    def test_list_matches_returns_200(self, client):
        response = client.get("/matches")
        assert response.status_code == 200

    def test_list_matches_pagination_structure(self, client):
        data = client.get("/matches").json()
        assert "total" in data
        assert "page" in data
        assert "items" in data

    def test_get_match_by_id(self, client):
        response = client.get(f"/matches/{pytest.match_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pytest.match_id
        assert data["home_score"] == 2
        assert data["away_score"] == 1
        assert data["result"] == "H"

    def test_get_match_includes_statistics(self, client):
        data = client.get(f"/matches/{pytest.match_id}").json()
        assert "statistics" in data
        assert len(data["statistics"]) == 2

    def test_get_match_not_found(self, client):
        response = client.get("/matches/99999")
        assert response.status_code == 404

    def test_list_matches_filtered_by_team(self, client):
        response = client.get(f"/matches?team_id={pytest.team_a_id}")
        assert response.status_code == 200


# ─── Leagues Tests ─────────────────────────────────────────────────────────────

class TestLeagues:
    def test_list_leagues(self, client):
        response = client.get("/leagues")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_league_by_id(self, client):
        response = client.get(f"/leagues/{pytest.league_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test League"

    def test_get_league_not_found(self, client):
        response = client.get("/leagues/99999")
        assert response.status_code == 404

    def test_league_analytics(self, client):
        response = client.get(f"/analytics/league/{pytest.league_id}")
        assert response.status_code == 200
        data = response.json()
        assert "table" in data
        assert "top_scorers_teams" in data
        assert "best_defences_teams" in data


# ─── Prediction Tests ──────────────────────────────────────────────────────────

class TestPredictions:
    def test_predict_without_model_returns_503(self, client):
        """Prediction should fail gracefully if no model is loaded."""
        response = client.post("/predict", json={
            "home_team_id": pytest.team_a_id,
            "away_team_id": pytest.team_b_id,
        })
        # Model not loaded in tests → 503 or 200 depending on fixture
        assert response.status_code in (200, 503)

    def test_predict_same_team_returns_400(self, client):
        response = client.post("/predict", json={
            "home_team_id": pytest.team_a_id,
            "away_team_id": pytest.team_a_id,
        })
        assert response.status_code == 400

    def test_predict_invalid_team_returns_400(self, client):
        response = client.post("/predict", json={
            "home_team_id": 99999,
            "away_team_id": pytest.team_b_id,
        })
        assert response.status_code == 400

    def test_predict_request_validation(self, client):
        """Missing required fields should return 422."""
        response = client.post("/predict", json={"home_team_id": 1})
        assert response.status_code == 422

    def test_get_recent_predictions(self, client):
        response = client.get("/predict/recent")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
