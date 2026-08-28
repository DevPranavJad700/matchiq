"""Demo data seeder for MatchIQ.

Generates a realistic synthetic Premier League-like dataset covering
3 seasons (2021-22, 2022-23, 2023-24) with 20 teams, realistic
match statistics, and standings.

This data is clearly labeled as SAMPLE/DEMO data and is NOT real
football results. It provides enough data (~1140 matches per season)
to demonstrate the full MatchIQ system including ML training.

Usage:
    python scripts/seed_demo_data.py [--reset]

Options:
    --reset    Drop all existing data before seeding
"""

import argparse
import logging
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ─── Configuration ─────────────────────────────────────────────────────────────

random.seed(42)
np.random.seed(42)

LEAGUE_NAME = "Premier League (Demo)"
COUNTRY = "England"
SEASONS = ["2021-22", "2022-23", "2023-24"]

# 20 Premier League-style teams with realistic strength ratings (0-1)
# Higher strength → higher attack, lower goals conceded
TEAMS = [
    {"name": "Arsenal FC", "short_name": "ARS", "strength": 0.86},
    {"name": "Aston Villa", "short_name": "AVL", "strength": 0.73},
    {"name": "AFC Bournemouth", "short_name": "BOU", "strength": 0.60},
    {"name": "Brentford FC", "short_name": "BRE", "strength": 0.65},
    {"name": "Brighton & Hove Albion", "short_name": "BHA", "strength": 0.70},
    {"name": "Chelsea FC", "short_name": "CHE", "strength": 0.81},
    {"name": "Coventry City", "short_name": "COV", "strength": 0.50},
    {"name": "Crystal Palace", "short_name": "CRY", "strength": 0.58},
    {"name": "Everton FC", "short_name": "EVE", "strength": 0.57},
    {"name": "Fulham FC", "short_name": "FUL", "strength": 0.62},
    {"name": "Hull City", "short_name": "HUL", "strength": 0.54},
    {"name": "Ipswich Town", "short_name": "IPS", "strength": 0.52},
    {"name": "Leeds United", "short_name": "LEE", "strength": 0.55},
    {"name": "Liverpool FC", "short_name": "LIV", "strength": 0.88},
    {"name": "Manchester City", "short_name": "MCI", "strength": 0.92},
    {"name": "Manchester United", "short_name": "MUN", "strength": 0.78},
    {"name": "Newcastle United", "short_name": "NEW", "strength": 0.76},
    {"name": "Nottingham Forest", "short_name": "NFO", "strength": 0.56},
    {"name": "Sunderland AFC", "short_name": "SUN", "strength": 0.53},
    {"name": "Tottenham Hotspur", "short_name": "TOT", "strength": 0.75},
]


def simulate_match(
    home_strength: float, away_strength: float
) -> dict:
    """Simulate a match result using Poisson distribution based on team strengths.

    Home advantage is modeled as a 0.25 boost to home expected goals.
    """
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

    # Derive correlated stats from goals and strength
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


def generate_season_schedule(
    teams: list[dict], season_start: datetime
) -> list[dict]:
    """Generate a full round-robin schedule for a season."""
    n = len(teams)
    matches = []
    matchday = 0

    for i in range(n):
        for j in range(n):
            if i != j:
                matchday += 1
                # Spread matches across ~38 gameweeks
                gw = ((matchday - 1) // (n // 2)) + 1
                days_offset = (gw - 1) * 7 + random.randint(0, 5)
                match_date = season_start + timedelta(days=days_offset)

                matches.append({
                    "home_team_idx": i,
                    "away_team_idx": j,
                    "match_date": match_date,
                    "matchday": gw,
                })

    return matches


def seed_to_db(reset: bool = False) -> None:
    """Seed demo data directly into the PostgreSQL database."""
    from app.db.session import SessionLocal, engine
    from app.models.orm_models import (
        Base,
        League,
        Match,
        ModelVersion,
        Season,
        Standing,
        Team,
        TeamMatchStatistic,
    )
    from sqlalchemy import select, text

    db = SessionLocal()

    if reset:
        logger.info("Dropping all tables and recreating...")
        Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)
    logger.info("Tables created/verified")

    # Check if already seeded
    existing = db.execute(select(League)).scalar_one_or_none()
    if existing and not reset:
        logger.info("Data already exists. Use --reset to re-seed.")
        db.close()
        return

    # ── League ────────────────────────────────────────────
    league = League(name=LEAGUE_NAME, short_name="PL-DEMO", country=COUNTRY)
    db.add(league)
    db.flush()
    logger.info(f"Created league: {league.name} (id={league.id})")

    # ── Teams ─────────────────────────────────────────────
    team_objs = []
    for t in TEAMS:
        team = Team(name=t["name"], short_name=t["short_name"], country=COUNTRY, league_id=league.id)
        db.add(team)
        team_objs.append(team)
    db.flush()
    logger.info(f"Created {len(team_objs)} teams")

    # Build CSV records for ML training (saved alongside DB seeding)
    csv_rows = []

    # ── Seasons ────────────────────────────────────────────
    season_starts = {
        "2021-22": datetime(2021, 8, 14, tzinfo=timezone.utc),
        "2022-23": datetime(2022, 8, 6, tzinfo=timezone.utc),
        "2023-24": datetime(2023, 8, 12, tzinfo=timezone.utc),
    }

    for season_year in SEASONS:
        season_start = season_starts[season_year]
        season = Season(league_id=league.id, year=season_year)
        db.add(season)
        db.flush()

        logger.info(f"Seeding season {season_year}...")

        # Generate schedule
        schedule = generate_season_schedule(TEAMS, season_start)

        # Track standings
        standings_tracker = {
            t.id: {
                "position": 0, "played": 0, "won": 0, "drawn": 0, "lost": 0,
                "goals_for": 0, "goals_against": 0, "goal_difference": 0, "points": 0
            }
            for t in team_objs
        }

        # Create matches
        for sched in schedule:
            ht_idx = sched["home_team_idx"]
            at_idx = sched["away_team_idx"]
            ht = team_objs[ht_idx]
            at = team_objs[at_idx]

            sim = simulate_match(TEAMS[ht_idx]["strength"], TEAMS[at_idx]["strength"])

            match = Match(
                season_id=season.id,
                league_id=league.id,
                home_team_id=ht.id,
                away_team_id=at.id,
                match_date=sched["match_date"],
                home_score=sim["home_goals"],
                away_score=sim["away_goals"],
                result=sim["result"],
                matchday=sched["matchday"],
            )
            db.add(match)
            db.flush()

            # Stats — home
            db.add(TeamMatchStatistic(
                match_id=match.id, team_id=ht.id, is_home=True,
                goals=sim["home_goals"], goals_conceded=sim["away_goals"],
                shots=sim["home_shots"], shots_on_target=sim["home_sot"],
                possession=sim["home_possession"], xg=sim["home_xg"],
                corners=sim["home_corners"], fouls=sim["home_fouls"],
                yellow_cards=sim["home_yellows"], red_cards=sim["home_reds"],
            ))
            # Stats — away
            db.add(TeamMatchStatistic(
                match_id=match.id, team_id=at.id, is_home=False,
                goals=sim["away_goals"], goals_conceded=sim["home_goals"],
                shots=sim["away_shots"], shots_on_target=sim["away_sot"],
                possession=sim["away_possession"], xg=sim["away_xg"],
                corners=sim["away_corners"], fouls=sim["away_fouls"],
                yellow_cards=sim["away_yellows"], red_cards=sim["away_reds"],
            ))

            # Update standing tracker
            for team_id, is_home, gf, ga, result_code in [
                (ht.id, True, sim["home_goals"], sim["away_goals"], sim["result"]),
                (at.id, False, sim["away_goals"], sim["home_goals"], sim["result"]),
            ]:
                st = standings_tracker[team_id]
                st["played"] += 1
                st["goals_for"] += gf
                st["goals_against"] += ga
                st["goal_difference"] = st["goals_for"] - st["goals_against"]
                if (is_home and result_code == "H") or (not is_home and result_code == "A"):
                    st["won"] += 1
                    st["points"] += 3
                elif result_code == "D":
                    st["drawn"] += 1
                    st["points"] += 1
                else:
                    st["lost"] += 1

            # CSV row
            csv_rows.append({
                "match_id": match.id,
                "match_date": match.match_date.isoformat(),
                "season": season_year,
                "home_team_id": ht.id,
                "away_team_id": at.id,
                "result": sim["result"],
                "home_goals": sim["home_goals"],
                "away_goals": sim["away_goals"],
                "home_shots": sim["home_shots"],
                "away_shots": sim["away_shots"],
                "home_sot": sim["home_sot"],
                "away_sot": sim["away_sot"],
                "home_xg": sim["home_xg"],
                "away_xg": sim["away_xg"],
            })

        db.flush()

        # Compute and store final standings
        sorted_teams = sorted(
            standings_tracker.items(),
            key=lambda x: (-x[1]["points"], -x[1]["goal_difference"], -x[1]["goals_for"])
        )
        for position, (team_id, stats) in enumerate(sorted_teams, start=1):
            stats["position"] = position
            db.add(Standing(
                season_id=season.id,
                team_id=team_id,
                **stats,
            ))

        db.flush()
        logger.info(f"  Season {season_year}: {len(schedule)} matches seeded")

    db.commit()
    logger.info("✓ Database seeded successfully!")

    # Save processed CSV for ML training
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    csv_df = pd.DataFrame(csv_rows)
    csv_df["match_date"] = pd.to_datetime(csv_df["match_date"])
    csv_df.to_csv(processed_dir / "matches_processed.csv", index=False)
    logger.info(f"✓ CSV saved to {processed_dir / 'matches_processed.csv'} ({len(csv_df)} rows)")

    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed MatchIQ with demo data")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables")
    args = parser.parse_args()

    seed_to_db(reset=args.reset)
