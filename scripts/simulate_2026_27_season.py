"""MatchIQ 2026-27 Premier League Season Simulation Script.

Executes all 380 match predictions using the trained production ML model
(ml/models/best_model.joblib) and generates the full standings table.
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import numpy as np
import pandas as pd
from sqlalchemy import select

from app.db.session import SessionLocal
from app.ml.model_loader import get_feature_names, get_model, load_model
from app.models.orm_models import Team
from app.services.prediction_service import PredictionService


def main() -> None:
    print("=" * 70)
    print("MATCHIQ 2026-27 PREMIER LEAGUE FULL SEASON ML SIMULATION")
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

    teams = []
    for name in target_names:
        t = db.execute(select(Team).where(Team.name.ilike(f"%{name}%"))).scalars().first()
        if t:
            teams.append(t)
        else:
            raise ValueError(f"Team {name} not found in database!")

    print(f"Verified {len(teams)} Premier League Clubs for 2026-27 Season:")
    for i, t in enumerate(teams, 1):
        print(f"   {i:2d}. {t.name:<25} (ID: {t.id})")

    # 3. Execute 380 ML Predictions
    print("\n--- Running Live ML Inference for all 380 Season Fixtures ---")
    svc = PredictionService(db)
    matches = []
    match_no = 1

    for home_t in teams:
        for away_t in teams:
            if home_t.id == away_t.id:
                continue

            pred = svc.predict(home_t.id, away_t.id)
            p_h = pred.probabilities.home_win
            p_d = pred.probabilities.draw
            p_a = pred.probabilities.away_win

            matches.append({
                "match_no": match_no,
                "home_team": home_t.name,
                "away_team": away_t.name,
                "home_win_pct": f"{p_h * 100:.1f}%",
                "draw_pct": f"{p_d * 100:.1f}%",
                "away_win_pct": f"{p_a * 100:.1f}%",
                "home_win_prob": round(p_h, 4),
                "draw_prob": round(p_d, 4),
                "away_win_prob": round(p_a, 4),
                "predicted_outcome": "Home Win" if pred.predicted_result == "HOME_WIN" else ("Away Win" if pred.predicted_result == "AWAY_WIN" else "Draw"),
                "confidence": pred.confidence,
                "top_driver_1": pred.explanation[0].description if len(pred.explanation) > 0 else "N/A",
                "top_driver_2": pred.explanation[1].description if len(pred.explanation) > 1 else "N/A",
            })
            match_no += 1

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
        print("File locked, saved predictions to alternate file:")
        print(f"   {alt_path}")

    # 4. Monte Carlo Season Table Simulation (10,000 runs)
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
    for t in team_names:
        w = int(round(np.mean(sim_w[t])))
        d = int(round(np.mean(sim_d[t])))
        losses = 38 - w - d
        gf = int(round(np.mean(sim_gf[t])))
        ga = int(round(np.mean(sim_ga[t])))
        gd = gf - ga
        pts = w * 3 + d
        form_p = [w / 38, d / 38, losses / 38]
        last5 = "".join(np.random.choice(["W", "D", "L"], size=5, p=form_p))

        final_rows.append({
            "Club": t,
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
        print("File locked, saved Standings Table to:")
        print(f"   {alt_path}\n")

    print(standings_df.to_string())
    db.close()


if __name__ == "__main__":
    main()
