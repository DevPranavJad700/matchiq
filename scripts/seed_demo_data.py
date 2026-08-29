"""Demo data seeder for MatchIQ [SIMULATED DEMO DATA].

Generates a synthetic Premier League simulation dataset covering 3 seasons
with 20 teams, valid round-robin matchday scheduling (10 matches per matchday,
1 match per team per matchday), and realistic simulated statistics.

NOTICE: This generator produces SIMULATED / SYNTHETIC data for demo purposes.
For authentic Premier League data, run: python scripts/fetch_real_data.py

Usage:
    python scripts/seed_demo_data.py [--reset]

Options:
    --reset    Drop all existing data before seeding
"""

import argparse
import logging
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ─── Configuration ─────────────────────────────────────────────────────────────

random.seed(42)
np.random.seed(42)

LEAGUE_NAME = "Premier League (Simulated Demo)"
COUNTRY = "England"
SEASONS = ["2021-22", "2022-23", "2023-24"]

TEAMS = [
    {"name": "Arsenal FC", "short_name": "ARS", "strength": 0.86},
    {"name": "Aston Villa", "short_name": "AVL", "strength": 0.73},
    {"name": "AFC Bournemouth", "short_name": "BOU", "strength": 0.60},
    {"name": "Brentford FC", "short_name": "BRE", "strength": 0.65},
    {"name": "Brighton & Hove Albion", "short_name": "BHA", "strength": 0.70},
    {"name": "Chelsea FC", "short_name": "CHE", "strength": 0.81},
    {"name": "Crystal Palace", "short_name": "CRY", "strength": 0.58},
    {"name": "Everton FC", "short_name": "EVE", "strength": 0.57},
    {"name": "Fulham FC", "short_name": "FUL", "strength": 0.62},
    {"name": "Leeds United", "short_name": "LEE", "strength": 0.55},
    {"name": "Leicester City", "short_name": "LEI", "strength": 0.60},
    {"name": "Liverpool FC", "short_name": "LIV", "strength": 0.88},
    {"name": "Luton Town", "short_name": "LUT", "strength": 0.45},
    {"name": "Manchester City", "short_name": "MCI", "strength": 0.92},
    {"name": "Manchester United", "short_name": "MUN", "strength": 0.78},
    {"name": "Newcastle United", "short_name": "NEW", "strength": 0.76},
    {"name": "Nottingham Forest", "short_name": "NFO", "strength": 0.56},
    {"name": "Southampton FC", "short_name": "SOU", "strength": 0.50},
    {"name": "Tottenham Hotspur", "short_name": "TOT", "strength": 0.75},
    {"name": "Wolves", "short_name": "WOL", "strength": 0.57},
]


def simulate_match(home_strength: float, away_strength: float) -> dict:
    """Simulate a match result using Poisson distribution based on team strengths."""
    HOME_ADVANTAGE = 0.25

    home_xg = max(0.5, home_strength * 2.5 + HOME_ADVANTAGE - away_strength * 1.2)
    away_xg = max(0.3, away_strength * 2.2 - home_strength * 1.0)

    home_goals = int(np.random.poisson(home_xg))
    away_goals = int(np.random.poisson(away_xg))

    if home_goals > away_goals:
        result = "H"
    elif home_goals < away_goals:
        result = "A"
    else:
        result = "D"

    home_shots = max(3, int(np.random.normal(home_xg * 6, 3)))
    away_shots = max(2, int(np.random.normal(away_xg * 6, 3)))

    home_sot = min(home_shots, max(1, int(np.random.normal(home_xg * 2.5, 2))))
    away_sot = min(away_shots, max(0, int(np.random.normal(away_xg * 2.5, 2))))

    home_possession = round(
        min(75, max(30, np.random.normal(50 + (home_strength - away_strength) * 25, 8))), 1
    )
    away_possession = round(100 - home_possession, 1)

    return {
        "result": result,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "home_xg": round(float(home_xg), 2),
        "away_xg": round(float(away_xg), 2),
        "home_shots": home_shots,
        "away_shots": away_shots,
        "home_sot": home_sot,
        "away_sot": away_sot,
        "home_possession": home_possession,
        "away_possession": away_possession,
        "home_corners": max(0, int(np.random.normal(5, 2))),
        "away_corners": max(0, int(np.random.normal(4, 2))),
        "home_fouls": max(5, int(np.random.normal(12, 3))),
        "away_fouls": max(5, int(np.random.normal(13, 3))),
        "home_yellows": max(0, int(np.random.normal(1.5, 1))),
        "away_yellows": max(0, int(np.random.normal(1.8, 1))),
        "home_reds": 1 if random.random() < 0.03 else 0,
        "away_reds": 1 if random.random() < 0.03 else 0,
    }


def generate_valid_round_robin_schedule(teams: list[dict], season_start: datetime) -> list[dict]:
    """Generate a realistic round-robin schedule using circle method.

    Guarantees:
    - Exactly 38 matchdays.
    - Exactly 10 matches per matchday.
    - Each team plays exactly ONE match per matchday.
    - No multi-match same-day collisions for any team.
    """
    n = len(teams)
    team_indices = list(range(n))
    first_half_rounds = []

    # Circle algorithm for round robin
    indices = team_indices[:]
    for round_num in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            t1 = indices[i]
            t2 = indices[n - 1 - i]
            # Alternate home/away based on round
            if round_num % 2 == 0:
                round_matches.append((t1, t2))
            else:
                round_matches.append((t2, t1))
        first_half_rounds.append(round_matches)
        # Rotate all but the first element
        indices = [indices[0]] + [indices[-1]] + indices[1:-1]

    # Second half: reverse home and away
    second_half_rounds = []
    for r in first_half_rounds:
        second_half_rounds.append([(t2, t1) for (t1, t2) in r])

    all_rounds = first_half_rounds + second_half_rounds

    matches = []
    for gw, round_matches in enumerate(all_rounds, start=1):
        # Matchday date: 7 days apart, kickoff slots around Saturday/Sunday
        gw_base_date = season_start + timedelta(days=(gw - 1) * 7)
        for match_in_gw, (ht_idx, at_idx) in enumerate(round_matches):
            # Realistic slot: Sat 12:30 (0), Sat 15:00 (1..6), Sat 17:30 (7), Sun 14:00 (8), Sun 16:30 (9)
            if match_in_gw == 0:
                match_dt = gw_base_date.replace(hour=12, minute=30)
            elif match_in_gw < 7:
                match_dt = gw_base_date.replace(hour=15, minute=0)
            elif match_in_gw == 7:
                match_dt = gw_base_date.replace(hour=17, minute=30)
            elif match_in_gw == 8:
                match_dt = (gw_base_date + timedelta(days=1)).replace(hour=14, minute=0)
            else:
                match_dt = (gw_base_date + timedelta(days=1)).replace(hour=16, minute=30)

            matches.append({
                "home_team_idx": ht_idx,
                "away_team_idx": at_idx,
                "match_date": match_dt,
                "matchday": gw,
            })

    return matches


def seed_to_db(reset: bool = False) -> None:
    """Populate database with simulated demo data."""
    from app.db.base import Base
    from app.db.session import SessionLocal, engine
    from app.models.orm_models import (
        League, Match, Season, Standing, Team, TeamMatchStatistic, Prediction
    )
    from sqlalchemy import select

    logger.warning("=" * 60)
    logger.warning("[NOTICE] SEEDING SYNTHETIC DEMO DATA")
    logger.warning("This generator creates simulated data for offline/test environments.")
    logger.warning("=" * 60)

    if reset:
        logger.info("Dropping all existing database tables...")
        db = SessionLocal()
        db.query(Prediction).delete()
        db.query(TeamMatchStatistic).delete()
        db.query(Standing).delete()
        db.query(Match).delete()
        db.query(Team).delete()
        db.query(Season).delete()
        db.query(League).delete()
        db.commit()
        db.close()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. League
    league = db.execute(select(League).where(League.name == LEAGUE_NAME)).scalar_one_or_none()
    if not league:
        league = League(name=LEAGUE_NAME, short_name="PL-DEMO", country=COUNTRY)
        db.add(league)
        db.flush()

    # 2. Teams
    team_objs = []
    for t_data in TEAMS:
        t = db.execute(select(Team).where(Team.name == t_data["name"])).scalar_one_or_none()
        if not t:
            t = Team(
                name=t_data["name"],
                short_name=t_data["short_name"],
                country=COUNTRY,
                league_id=league.id,
            )
            db.add(t)
            db.flush()
        team_objs.append(t)

    # 3. Seasons & Matches
    season_starts = {
        "2021-22": datetime(2021, 8, 14, tzinfo=timezone.utc),
        "2022-23": datetime(2022, 8, 6, tzinfo=timezone.utc),
        "2023-24": datetime(2023, 8, 12, tzinfo=timezone.utc),
    }

    all_match_rows = []
    total_matches_seeded = 0

    for season_name in SEASONS:
        season = db.execute(
            select(Season).where(Season.league_id == league.id, Season.year == season_name)
        ).scalar_one_or_none()
        if not season:
            season = Season(league_id=league.id, year=season_name)
            db.add(season)
            db.flush()

        logger.info(f"Generating valid round-robin schedule for season {season_name}...")
        schedule = generate_valid_round_robin_schedule(TEAMS, season_starts[season_name])

        table_tracker = {
            t.id: {
                "played": 0, "won": 0, "drawn": 0, "lost": 0,
                "goals_for": 0, "goals_against": 0, "points": 0,
            }
            for t in team_objs
        }

        for m_info in schedule:
            ht = team_objs[m_info["home_team_idx"]]
            at = team_objs[m_info["away_team_idx"]]
            ht_strength = TEAMS[m_info["home_team_idx"]]["strength"]
            at_strength = TEAMS[m_info["away_team_idx"]]["strength"]

            sim = simulate_match(ht_strength, at_strength)

            match = Match(
                season_id=season.id,
                league_id=league.id,
                home_team_id=ht.id,
                away_team_id=at.id,
                match_date=m_info["match_date"],
                home_score=sim["home_goals"],
                away_score=sim["away_goals"],
                result=sim["result"],
                matchday=m_info["matchday"],
            )
            db.add(match)
            db.flush()

            # Stats
            db.add(TeamMatchStatistic(
                match_id=match.id, team_id=ht.id, is_home=True,
                goals=sim["home_goals"], goals_conceded=sim["away_goals"],
                shots=sim["home_shots"], shots_on_target=sim["home_sot"],
                possession=sim["home_possession"], xg=sim["home_xg"],
                corners=sim["home_corners"], fouls=sim["home_fouls"],
                yellow_cards=sim["home_yellows"], red_cards=sim["home_reds"],
            ))
            db.add(TeamMatchStatistic(
                match_id=match.id, team_id=at.id, is_home=False,
                goals=sim["away_goals"], goals_conceded=sim["home_goals"],
                shots=sim["away_shots"], shots_on_target=sim["away_sot"],
                possession=sim["away_possession"], xg=sim["away_xg"],
                corners=sim["away_corners"], fouls=sim["away_fouls"],
                yellow_cards=sim["away_yellows"], red_cards=sim["away_reds"],
            ))

            # Update standings
            hg, ag, res = sim["home_goals"], sim["away_goals"], sim["result"]
            st_h, st_a = table_tracker[ht.id], table_tracker[at.id]
            st_h["played"] += 1; st_h["goals_for"] += hg; st_h["goals_against"] += ag
            st_a["played"] += 1; st_a["goals_for"] += ag; st_a["goals_against"] += hg

            if res == "H":
                st_h["won"] += 1; st_h["points"] += 3; st_a["lost"] += 1
            elif res == "A":
                st_a["won"] += 1; st_a["points"] += 3; st_h["lost"] += 1
            else:
                st_h["drawn"] += 1; st_h["points"] += 1; st_a["drawn"] += 1; st_a["points"] += 1

            total_matches_seeded += 1

        # Commit final standings
        sorted_standings = sorted(
            table_tracker.items(),
            key=lambda x: (-x[1]["points"], -(x[1]["goals_for"] - x[1]["goals_against"]), -x[1]["goals_for"])
        )
        for pos, (tid, stats) in enumerate(sorted_standings, start=1):
            db.add(Standing(
                season_id=season.id,
                team_id=tid,
                position=pos,
                played=stats["played"],
                won=stats["won"],
                drawn=stats["drawn"],
                lost=stats["lost"],
                goals_for=stats["goals_for"],
                goals_against=stats["goals_against"],
                goal_difference=stats["goals_for"] - stats["goals_against"],
                points=stats["points"],
            ))

    db.commit()
    db.close()
    logger.info(f"✓ Seeded {total_matches_seeded} valid simulated matches into database.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed database with simulated demo data")
    parser.add_argument("--reset", action="store_true", help="Reset all data before seeding")
    args = parser.parse_args()

    seed_to_db(reset=args.reset)
