"""MatchIQ 2026-27 Premier League Season Simulation Script.

Executes all 380 match predictions using the trained production ML model
(ml/models/best_model.joblib), runs a 10,000-run Monte Carlo simulation,
and seeds the 2026-27 Season, 380 Projected Matches, and Simulated Standings into the database.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

# Add backend and root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import pandas as pd
from sqlalchemy import select

from app.db.session import SessionLocal
from app.ml.model_loader import get_feature_names, get_model, load_model
from app.models.orm_models import League, Match, Prediction, Season, Standing, Team, TeamMatchStatistic
from app.services.prediction_service import PredictionService


def main() -> None:
    print("=" * 70)
    print("MATCHIQ 2026-27 PREMIER LEAGUE FULL SEASON ML SIMULATION & SEEDING")
    print("=" * 70)

    # 1. Load active ML Model and features
    load_model()
    model = get_model()
    features = get_feature_names()
    print(f"Loaded ML Model Architecture: {type(model).__name__}")
    print(f"Model Feature Dimensions:    {len(features)} features")

    # 2. Database Session & 20 Confirmed Clubs for 2026-27
    db = SessionLocal()
    target_names = [
        "Arsenal FC",
        "Manchester City",
        "Manchester United",
        "Aston Villa",
        "Liverpool FC",
        "AFC Bournemouth",
        "Sunderland AFC",
        "Brighton & Hove Albion",
        "Brentford FC",
        "Chelsea FC",
        "Fulham FC",
        "Newcastle United",
        "Everton FC",
        "Leeds United",
        "Crystal Palace",
        "Nottingham Forest",
        "Tottenham Hotspur",
        "Hull City",
        "Coventry City",
        "Ipswich Town",
    ]

    # Find the Premier League (don't hardcode id — the actual id varies per database)
    league = db.execute(
        select(League).where(League.name == "Premier League", League.country == "England")
    ).scalar_one_or_none()
    if not league:
        league = League(name="Premier League", short_name="PL", country="England")
        db.add(league)
        db.flush()

    # Ensure Coventry City exists if promoted for 2026-27
    cov = db.execute(select(Team).where(Team.name.ilike("%Coventry%"))).scalars().first()
    if not cov:
        cov = Team(name="Coventry City", short_name="COV", country="England", league_id=1)
        db.add(cov)
        db.flush()

    teams = []
    for name in target_names:
        t = db.execute(select(Team).where(Team.name.ilike(f"%{name}%"))).scalars().first()
        if t:
            teams.append(t)
        else:
            raise ValueError(f"Team {name} not found in database!")

    print(f"\nVerified {len(teams)} Premier League Clubs for 2026-27 Season:")
    for i, t in enumerate(teams, 1):
        print(f"   {i:2d}. {t.name:<25} (ID: {t.id})")

    # 3. Load Real 2026-27 Fixtures CSV
    csv_file = ROOT_DIR / "data" / "fixtures_2026_27.csv"
    if not csv_file.exists():
        raise FileNotFoundError(f"Fixture calendar not found at {csv_file}")

    print(f"\n--- Loading Real 2026-27 Schedule from {csv_file.name} ---")
    fixtures_df = pd.read_csv(csv_file)
    print(f"Loaded {len(fixtures_df)} scheduled fixtures across {fixtures_df['Matchday'].nunique()} matchdays.")

    NAME_MAP = {
        "Arsenal": "Arsenal FC",
        "Arsenal FC": "Arsenal FC",
        "Manchester City": "Manchester City",
        "Manchester United": "Manchester United",
        "Aston Villa": "Aston Villa",
        "Liverpool": "Liverpool FC",
        "Liverpool FC": "Liverpool FC",
        "AFC Bournemouth": "AFC Bournemouth",
        "Bournemouth": "AFC Bournemouth",
        "Sunderland": "Sunderland AFC",
        "Sunderland AFC": "Sunderland AFC",
        "Brighton & Hove Albion": "Brighton & Hove Albion",
        "Brighton": "Brighton & Hove Albion",
        "Brentford": "Brentford FC",
        "Brentford FC": "Brentford FC",
        "Chelsea": "Chelsea FC",
        "Chelsea FC": "Chelsea FC",
        "Fulham": "Fulham FC",
        "Fulham FC": "Fulham FC",
        "Newcastle United": "Newcastle United",
        "Newcastle": "Newcastle United",
        "Everton": "Everton FC",
        "Everton FC": "Everton FC",
        "Leeds United": "Leeds United",
        "Leeds": "Leeds United",
        "Crystal Palace": "Crystal Palace",
        "Nottingham Forest": "Nottingham Forest",
        "Tottenham Hotspur": "Tottenham Hotspur",
        "Tottenham": "Tottenham Hotspur",
        "Hull City": "Hull City",
        "Hull": "Hull City",
        "Coventry City": "Coventry City",
        "Coventry": "Coventry City",
        "Ipswich Town": "Ipswich Town",
        "Ipswich": "Ipswich Town",
    }

    team_by_name = {t.name: t for t in teams}

    # 4. Execute ML Predictions on Real Fixtures
    print("\n--- Running Live ML Inference for all 380 Scheduled Fixtures ---")
    svc = PredictionService(db)
    matches = []

    for match_no, (_, row) in enumerate(fixtures_df.iterrows(), 1):
        raw_home = str(row["Home Team"]).strip()
        raw_away = str(row["Away Team"]).strip()
        home_canonical = NAME_MAP.get(raw_home, raw_home)
        away_canonical = NAME_MAP.get(raw_away, raw_away)

        home_t = team_by_name.get(home_canonical)
        away_t = team_by_name.get(away_canonical)

        if not home_t:
            raise ValueError(f"Home team '{raw_home}' ({home_canonical}) not found in database teams!")
        if not away_t:
            raise ValueError(f"Away team '{raw_away}' ({away_canonical}) not found in database teams!")

        matchday = int(row["Matchday"])
        date_str = str(row["Date"]).strip()
        time_str = str(row.get("Kickoff (UK)", "15:00")).strip()
        if not time_str or time_str == "nan":
            time_str = "15:00"

        try:
            hour, minute = map(int, time_str.split(":"))
            dt_base = datetime.fromisoformat(date_str)
            match_datetime = datetime(dt_base.year, dt_base.month, dt_base.day, hour, minute, tzinfo=timezone.utc)
        except Exception:
            dt_base = datetime.fromisoformat(date_str)
            match_datetime = datetime(dt_base.year, dt_base.month, dt_base.day, 15, 0, tzinfo=timezone.utc)

        pred = svc.predict(home_t.id, away_t.id)
        p_h = pred.probabilities.home_win
        p_d = pred.probabilities.draw
        p_a = pred.probabilities.away_win

        # Most likely exact scoreline from Dixon-Coles
        top_score = pred.top_scorelines[0].score if pred.top_scorelines else "1-0"
        try:
            hg, ag = map(int, top_score.split("-"))
        except Exception:
            hg, ag = (1, 0) if pred.predicted_result == "HOME_WIN" else ((0, 1) if pred.predicted_result == "AWAY_WIN" else (1, 1))

        matches.append({
            "match_no": match_no,
            "matchday": matchday,
            "match_datetime": match_datetime,
            "home_team_id": home_t.id,
            "away_team_id": away_t.id,
            "home_team": home_t.name,
            "away_team": away_t.name,
            "home_win_pct": f"{p_h * 100:.1f}%",
            "draw_pct": f"{p_d * 100:.1f}%",
            "away_win_pct": f"{p_a * 100:.1f}%",
            "home_win_prob": round(p_h, 4),
            "draw_prob": round(p_d, 4),
            "away_win_prob": round(p_a, 4),
            "home_goals": hg,
            "away_goals": ag,
            "predicted_outcome": "Home Win" if pred.predicted_result == "HOME_WIN" else ("Away Win" if pred.predicted_result == "AWAY_WIN" else "Draw"),
            "result_code": "H" if pred.predicted_result == "HOME_WIN" else ("A" if pred.predicted_result == "AWAY_WIN" else "D"),
            "confidence": pred.confidence,
            "top_driver_1": pred.explanation[0].description if len(pred.explanation) > 0 else "N/A",
            "top_driver_2": pred.explanation[1].description if len(pred.explanation) > 1 else "N/A",
        })

    matches_df = pd.DataFrame(matches)
    os.makedirs("reports", exist_ok=True)
    matches_csv = Path("reports/premier_league_2026_27_predictions.csv").resolve()
    try:
        matches_df.to_csv(matches_csv, index=False)
        print(f"Successfully generated and saved {len(matches)} fixture predictions to:")
        print(f"   {matches_csv}")
    except PermissionError:
        alt_path = Path("reports/premier_league_2026_27_predictions_sim.csv").resolve()
        matches_df.to_csv(alt_path, index=False)
        print(f"File locked, saved predictions to alternate file: {alt_path}")

    # 5. Monte Carlo Season Table Simulation (10,000 runs)
    print("\n--- Running 10,000 Monte Carlo Season Simulations from Model Probabilities ---")
    N_SIMS = 10000
    np.random.seed(42)

    team_names = [t.name for t in teams]
    sim_w = {t: np.zeros(N_SIMS) for t in team_names}
    sim_d = {t: np.zeros(N_SIMS) for t in team_names}
    sim_l = {t: np.zeros(N_SIMS) for t in team_names}
    sim_gf = {t: np.zeros(N_SIMS) for t in team_names}
    sim_ga = {t: np.zeros(N_SIMS) for t in team_names}
    sim_pts = {t: np.zeros(N_SIMS) for t in team_names}

    for _, row in matches_df.iterrows():
        h = row["home_team"]
        a = row["away_team"]
        probs = np.array([row["home_win_prob"], row["draw_prob"], row["away_win_prob"]])
        probs = probs / probs.sum()

        outcomes = np.random.choice([0, 1, 2], size=N_SIMS, p=probs)
        base_h_lambda = 0.8 + 1.5 * probs[0] + 0.3 * probs[1]
        base_a_lambda = 0.5 + 1.4 * probs[2] + 0.3 * probs[1]

        h_goals = np.random.poisson(base_h_lambda, size=N_SIMS)
        a_goals = np.random.poisson(base_a_lambda, size=N_SIMS)

        for i in range(N_SIMS):
            if outcomes[i] == 0:
                if h_goals[i] <= a_goals[i]:
                    h_goals[i] = a_goals[i] + 1
                sim_w[h][i] += 1
                sim_l[a][i] += 1
                sim_pts[h][i] += 3
            elif outcomes[i] == 1:
                a_goals[i] = h_goals[i]
                sim_d[h][i] += 1
                sim_d[a][i] += 1
                sim_pts[h][i] += 1
                sim_pts[a][i] += 1
            else:
                if a_goals[i] <= h_goals[i]:
                    a_goals[i] = h_goals[i] + 1
                sim_w[a][i] += 1
                sim_l[h][i] += 1
                sim_pts[a][i] += 3

            sim_gf[h][i] += h_goals[i]
            sim_ga[h][i] += a_goals[i]
            sim_gf[a][i] += a_goals[i]
            sim_ga[a][i] += h_goals[i]

    # Aggregate standings table
    final_rows = []
    for t in teams:
        tname = t.name
        w = int(round(np.mean(sim_w[tname])))
        d = int(round(np.mean(sim_d[tname])))
        losses = 38 - w - d
        gf = int(round(np.mean(sim_gf[tname])))
        ga = int(round(np.mean(sim_ga[tname])))
        gd = gf - ga
        pts = w * 3 + d
        form_p = [w / 38, d / 38, losses / 38]
        last5 = "".join(np.random.choice(["W", "D", "L"], size=5, p=form_p))

        final_rows.append({
            "team_id": t.id,
            "Club": tname,
            "MP": 38,
            "W": w,
            "D": d,
            "L": losses,
            "GF": gf,
            "GA": ga,
            "GD": gd,
            "Pts": pts,
            "Last 5": last5,
        })

    standings_df = pd.DataFrame(final_rows).sort_values(by=["Pts", "GD", "GF"], ascending=False).reset_index(drop=True)
    standings_df.index = standings_df.index + 1
    standings_df.index.name = "Pos"

    standings_csv = Path("reports/premier_league_2026_27_predicted_standings.csv").resolve()
    try:
        standings_df.to_csv(standings_csv)
        print("Successfully generated and saved Standings Table to:")
        print(f"   {standings_csv}\n")
    except PermissionError:
        alt_path = Path("reports/premier_league_2026_27_predicted_standings_sim.csv").resolve()
        standings_df.to_csv(alt_path)
        print(f"File locked, saved Standings Table to: {alt_path}\n")

    print(standings_df[["Club", "MP", "W", "D", "L", "GF", "GA", "GD", "Pts", "Last 5"]].to_string())

    # 6. Seed 2026-27 Season into Database
    print("\n--- Seeding 2026-27 Real Scheduled Season & Standings into Database ---")
    season_2627 = db.execute(select(Season).where(Season.year == "2026-27")).scalar_one_or_none()
    if not season_2627:
        season_2627 = Season(league_id=league.id, year="2026-27")
        db.add(season_2627)
        db.flush()

    # Clear prior 2026-27 matches, predictions, statistics, and standings
    db.query(Standing).where(Standing.season_id == season_2627.id).delete()
    prior_matches = db.execute(select(Match).where(Match.season_id == season_2627.id)).scalars().all()
    prior_match_ids = [m.id for m in prior_matches]
    if prior_match_ids:
        db.query(Prediction).filter(Prediction.match_id.in_(prior_match_ids)).delete(synchronize_session=False)
        db.query(TeamMatchStatistic).filter(TeamMatchStatistic.match_id.in_(prior_match_ids)).delete(synchronize_session=False)
    db.query(Match).where(Match.season_id == season_2627.id).delete()
    db.flush()

    # Insert 2026-27 Standings
    for pos, row in standings_df.reset_index().iterrows():
        db.add(Standing(
            season_id=season_2627.id,
            team_id=int(row["team_id"]),
            position=int(row["Pos"]),
            played=int(row["MP"]),
            won=int(row["W"]),
            drawn=int(row["D"]),
            lost=int(row["L"]),
            goals_for=int(row["GF"]),
            goals_against=int(row["GA"]),
            goal_difference=int(row["GD"]),
            points=int(row["Pts"]),
        ))

    # Insert 380 Real Scheduled Projected Matches
    for _, row in matches_df.iterrows():
        h_id = int(row["home_team_id"])
        a_id = int(row["away_team_id"])
        matchday = int(row["matchday"])
        m_date = row["match_datetime"]

        match = Match(
            season_id=season_2627.id,
            league_id=league.id,
            home_team_id=h_id,
            away_team_id=a_id,
            match_date=m_date,
            home_score=int(row["home_goals"]),
            away_score=int(row["away_goals"]),
            result=str(row["result_code"]),
            matchday=matchday,
        )
        db.add(match)
        db.flush()

        db.add(TeamMatchStatistic(
            match_id=match.id,
            team_id=h_id,
            is_home=True,
            goals=int(row["home_goals"]),
            goals_conceded=int(row["away_goals"]),
            shots=12,
            shots_on_target=5,
            xg=1.5,
        ))
        db.add(TeamMatchStatistic(
            match_id=match.id,
            team_id=a_id,
            is_home=False,
            goals=int(row["away_goals"]),
            goals_conceded=int(row["home_goals"]),
            shots=9,
            shots_on_target=3,
            xg=1.1,
        ))

    db.commit()
    db.close()
    print("[OK] Successfully seeded 2026-27 season (380 real scheduled matches + 20 standings) into database!")


if __name__ == "__main__":
    main()

