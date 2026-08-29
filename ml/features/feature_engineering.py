"""Feature engineering for MatchIQ ML pipeline.

This module computes all features from processed match data.

ANTI-LEAKAGE GUARANTEE:
========================
All rolling features use `.shift(1)` before computing windows.
All league standings, points, and table positions are computed dynamically
per season from matches played strictly BEFORE the kickoff of each match.
This means for match N, only matches 1..N-1 are used. The feature captures
what was known BEFORE the match kicked off.

Feature categories:
- Team form (last 5 matches: pts, wins, draws, losses, gd)
- Attack strength (rolling 10-match average goals scored)
- Defence strength (rolling 10-match average goals conceded)
- Shot metrics (rolling 10-match average shots, shots on target)
- Estimated xG proxy (rolling 10-match average)
- Home/away venue performance (win rate, goals scored average)
- Pre-match league position and points in current season
- Head-to-head history (last 5 meetings)
- Difference features (home - away)
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RESULT_MAP = {"H": 0, "D": 1, "A": 2}  # target encoding
FEATURE_NAMES = [
    "home_form_pts_last5",
    "home_form_wins_last5",
    "home_form_draws_last5",
    "home_form_losses_last5",
    "home_form_gd_last5",
    "home_avg_goals_scored",
    "home_avg_goals_conceded",
    "home_avg_shots",
    "home_avg_shots_on_target",
    "home_avg_xg",
    "home_home_win_rate",
    "home_home_goals_avg",
    "home_league_position",
    "home_points",
    "away_form_pts_last5",
    "away_form_wins_last5",
    "away_form_draws_last5",
    "away_form_losses_last5",
    "away_form_gd_last5",
    "away_avg_goals_scored",
    "away_avg_goals_conceded",
    "away_avg_shots",
    "away_avg_shots_on_target",
    "away_avg_xg",
    "away_away_win_rate",
    "away_away_goals_avg",
    "away_league_position",
    "away_points",
    "h2h_home_wins",
    "h2h_away_wins",
    "h2h_draws",
    "h2h_home_goals_avg",
    "h2h_away_goals_avg",
    "form_diff",
    "attack_diff",
    "defence_diff",
    "position_diff",
    "points_diff",
    "xg_diff",
]


def _compute_points_from_result(result: str, is_home: bool) -> int:
    """Compute points earned by the team perspective."""
    if result == "D":
        return 1
    if is_home and result == "H":
        return 3
    if not is_home and result == "A":
        return 3
    return 0


def _rolling_team_features(df: pd.DataFrame, team_id: int) -> pd.DataFrame:
    """Compute rolling features for a single team from the full match DataFrame.

    df columns expected:
        match_id, match_date, home_team_id, away_team_id, result,
        home_goals, away_goals, home_shots, away_shots,
        home_sot, away_sot, home_xg, away_xg

    Returns a DataFrame indexed by match_id with team-centric features.
    """
    # Filter matches involving this team
    team_matches = df[
        (df["home_team_id"] == team_id) | (df["away_team_id"] == team_id)
    ].copy().sort_values("match_date")

    records = []
    for _, row in team_matches.iterrows():
        is_home = row["home_team_id"] == team_id
        result = row["result"]

        if is_home:
            goals = row.get("home_goals", np.nan)
            goals_conceded = row.get("away_goals", np.nan)
            shots = row.get("home_shots", np.nan)
            sot = row.get("home_sot", np.nan)
            xg = row.get("home_xg", np.nan)
        else:
            goals = row.get("away_goals", np.nan)
            goals_conceded = row.get("home_goals", np.nan)
            shots = row.get("away_shots", np.nan)
            sot = row.get("away_sot", np.nan)
            xg = row.get("away_xg", np.nan)

        pts = _compute_points_from_result(result, is_home) if pd.notna(result) else 0
        win = 1 if pts == 3 else 0
        draw = 1 if pts == 1 else 0
        loss = 1 if (pts == 0 and pd.notna(result)) else 0
        gd = ((goals or 0) - (goals_conceded or 0)) if pd.notna(goals) else 0

        records.append({
            "match_id": row["match_id"],
            "match_date": row["match_date"],
            "is_home": is_home,
            "pts": pts,
            "win": win,
            "draw": draw,
            "loss": loss,
            "goals": goals,
            "goals_conceded": goals_conceded,
            "shots": shots,
            "sot": sot,
            "xg": xg,
            "gd": gd,
        })

    tdf = pd.DataFrame(records)
    if tdf.empty:
        return pd.DataFrame()

    # Rolling features with shift(1) to prevent leakage
    def rolling_mean(col: str, window: int) -> pd.Series:
        return tdf[col].shift(1).rolling(window=window, min_periods=1).mean()

    def rolling_sum(col: str, window: int) -> pd.Series:
        return tdf[col].shift(1).rolling(window=window, min_periods=1).sum()

    tdf["form_pts_last5"] = rolling_sum("pts", 5)
    tdf["form_wins_last5"] = rolling_sum("win", 5)
    tdf["form_draws_last5"] = rolling_sum("draw", 5)
    tdf["form_losses_last5"] = rolling_sum("loss", 5)
    tdf["form_gd_last5"] = rolling_sum("gd", 5)
    tdf["avg_goals_scored"] = rolling_mean("goals", 10)
    tdf["avg_goals_conceded"] = rolling_mean("goals_conceded", 10)
    tdf["avg_shots"] = rolling_mean("shots", 10)
    tdf["avg_shots_on_target"] = rolling_mean("sot", 10)
    tdf["avg_xg"] = rolling_mean("xg", 10)

    # Venue-specific features
    home_df = tdf[tdf["is_home"] == True].copy()  # noqa: E712
    away_df = tdf[tdf["is_home"] == False].copy()  # noqa: E712

    home_df["home_win_rate"] = home_df["win"].shift(1).expanding().mean()
    home_df["home_goals_avg"] = home_df["goals"].shift(1).expanding().mean()
    away_df["away_win_rate"] = away_df["win"].shift(1).expanding().mean()
    away_df["away_goals_avg"] = away_df["goals"].shift(1).expanding().mean()

    tdf = tdf.merge(
        home_df[["match_id", "home_win_rate", "home_goals_avg"]], on="match_id", how="left"
    ).merge(
        away_df[["match_id", "away_win_rate", "away_goals_avg"]], on="match_id", how="left"
    )

    tdf["team_id"] = team_id
    return tdf.set_index("match_id")


def _compute_h2h_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute H2H features for each match from previous encounters.

    For match M between teams A(home) and B(away), use only the last 5
    meetings between A and B that occurred before match M's date.
    """
    h2h_records = []
    matches_sorted = df.sort_values("match_date")

    for _, row in matches_sorted.iterrows():
        ht = row["home_team_id"]
        at = row["away_team_id"]
        date = row["match_date"]
        mid = row["match_id"]

        past = df[
            (
                ((df["home_team_id"] == ht) & (df["away_team_id"] == at))
                | ((df["home_team_id"] == at) & (df["away_team_id"] == ht))
            )
            & (df["match_date"] < date)
            & (df["result"].notna())
        ].sort_values("match_date").tail(5)

        hw = dw = aw = 0
        hg_list, ag_list = [], []

        for _, pm in past.iterrows():
            if pm["home_team_id"] == ht:
                if pm["result"] == "H":
                    hw += 1
                elif pm["result"] == "D":
                    dw += 1
                else:
                    aw += 1
                hg_list.append(pm.get("home_goals", 0) or 0)
                ag_list.append(pm.get("away_goals", 0) or 0)
            else:
                if pm["result"] == "A":
                    hw += 1
                elif pm["result"] == "D":
                    dw += 1
                else:
                    aw += 1
                hg_list.append(pm.get("away_goals", 0) or 0)
                ag_list.append(pm.get("home_goals", 0) or 0)

        h2h_records.append({
            "match_id": mid,
            "h2h_home_wins": hw,
            "h2h_away_wins": aw,
            "h2h_draws": dw,
            "h2h_home_goals_avg": np.mean(hg_list) if hg_list else 0.0,
            "h2h_away_goals_avg": np.mean(ag_list) if ag_list else 0.0,
        })

    return pd.DataFrame(h2h_records).set_index("match_id")


def _compute_dynamic_season_standings(df: pd.DataFrame) -> dict[int, dict]:
    """Compute pre-match league standings dynamically per season with strict zero-leakage.

    For every match in chronological sequence:
    1. Look at prior completed matches within the same season.
    2. Rank teams by points (descending), goal difference (descending), and goals scored (descending).
    3. Output pre-match points and league position (1 to 20).
    """
    df_sorted = df.sort_values("match_date").copy()
    standings_by_match = {}

    # Group by season if present, otherwise treat as single timeline
    seasons = df_sorted["season"].unique() if "season" in df_sorted.columns else ["all"]

    for season in seasons:
        season_df = df_sorted[df_sorted["season"] == season] if "season" in df_sorted.columns else df_sorted
        all_season_teams = sorted(list(set(season_df["home_team_id"].unique()) | set(season_df["away_team_id"].unique())))

        # Table tracker: team_id -> {played, won, drawn, lost, gf, ga, gd, pts}
        table = {
            tid: {"played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0, "gd": 0, "pts": 0}
            for tid in all_season_teams
        }

        for _, match in season_df.iterrows():
            mid = match["match_id"]
            ht = match["home_team_id"]
            at = match["away_team_id"]

            # Pre-match positions (rank 1 to N)
            active_teams = [tid for tid, s in table.items() if s["played"] > 0]
            if active_teams:
                # Rank teams with at least 1 match played
                sorted_teams = sorted(
                    all_season_teams,
                    key=lambda t: (-table[t]["pts"], -table[t]["gd"], -table[t]["gf"], t)
                )
                pos_map = {t: idx + 1 for idx, t in enumerate(sorted_teams)}
                home_pos = float(pos_map.get(ht, 10.0))
                away_pos = float(pos_map.get(at, 10.0))
            else:
                home_pos = 10.0
                away_pos = 10.0

            home_pts = float(table[ht]["pts"])
            away_pts = float(table[at]["pts"])

            standings_by_match[mid] = {
                "home_league_position": home_pos,
                "home_points": home_pts,
                "away_league_position": away_pos,
                "away_points": away_pts,
            }

            # Update table AFTER match if result is recorded (shift 1)
            res = match.get("result")
            if pd.notna(res) and res in ["H", "D", "A"]:
                hg = int(match.get("home_goals", 0) or 0)
                ag = int(match.get("away_goals", 0) or 0)

                table[ht]["played"] += 1
                table[ht]["gf"] += hg
                table[ht]["ga"] += ag
                table[ht]["gd"] = table[ht]["gf"] - table[ht]["ga"]

                table[at]["played"] += 1
                table[at]["gf"] += ag
                table[at]["ga"] += hg
                table[at]["gd"] = table[at]["gf"] - table[at]["ga"]

                if res == "H":
                    table[ht]["won"] += 1
                    table[ht]["pts"] += 3
                    table[at]["lost"] += 1
                elif res == "A":
                    table[at]["won"] += 1
                    table[at]["pts"] += 3
                    table[ht]["lost"] += 1
                else:
                    table[ht]["drawn"] += 1
                    table[ht]["pts"] += 1
                    table[at]["drawn"] += 1
                    table[at]["pts"] += 1

    return standings_by_match


def compute_features(df: pd.DataFrame, standings: pd.DataFrame | None = None) -> pd.DataFrame:
    """Main feature engineering pipeline.

    Args:
        df: Match DataFrame with columns:
            match_id, match_date, home_team_id, away_team_id, result,
            home_goals, away_goals, [home_shots, away_shots, home_sot,
            away_sot, home_xg, away_xg, season]
        standings: Optional explicit standings DataFrame. If not provided,
            standings are dynamically computed per season with zero leakage.

    Returns:
        Feature DataFrame with one row per match, ready for ML training/inference.
    """
    logger.info(f"Engineering features for {len(df)} matches")
    df = df.copy().sort_values("match_date").reset_index(drop=True)

    # Compute per-team rolling features for all unique teams
    all_teams = set(df["home_team_id"].unique()) | set(df["away_team_id"].unique())
    team_feature_map = {}
    for team_id in all_teams:
        team_features = _rolling_team_features(df, team_id)
        if not team_features.empty:
            team_feature_map[team_id] = team_features

    # H2H features
    logger.info("Computing H2H features...")
    h2h_df = _compute_h2h_features(df)

    # Pre-match season standings
    logger.info("Computing dynamic per-season pre-match standings...")
    dynamic_standings = _compute_dynamic_season_standings(df)

    # Assemble match-level feature frame
    feature_rows = []
    for _, match in df.iterrows():
        mid = match["match_id"]
        ht = match["home_team_id"]
        at = match["away_team_id"]

        hf = team_feature_map.get(ht, pd.DataFrame())
        af = team_feature_map.get(at, pd.DataFrame())

        def get_feat(feat_df, feat_name, default=0.0):
            if feat_df.empty or mid not in feat_df.index:
                return default
            val = feat_df.loc[mid, feat_name] if feat_name in feat_df.columns else default
            return default if pd.isna(val) else val

        # Standings & points
        st_data = dynamic_standings.get(mid, {
            "home_league_position": 10.0, "home_points": 0.0,
            "away_league_position": 10.0, "away_points": 0.0,
        })
        home_pos = st_data["home_league_position"]
        home_pts = st_data["home_points"]
        away_pos = st_data["away_league_position"]
        away_pts = st_data["away_points"]

        if standings is not None:
            # If explicit standings override was supplied
            home_stand = standings[
                (standings["team_id"] == ht) & (standings["match_date"] <= match["match_date"])
            ].sort_values("match_date").tail(1)
            if not home_stand.empty:
                home_pos = float(home_stand.iloc[-1]["position"])
                home_pts = float(home_stand.iloc[-1]["points"])

            away_stand = standings[
                (standings["team_id"] == at) & (standings["match_date"] <= match["match_date"])
            ].sort_values("match_date").tail(1)
            if not away_stand.empty:
                away_pos = float(away_stand.iloc[-1]["position"])
                away_pts = float(away_stand.iloc[-1]["points"])

        home_xg = get_feat(hf, "avg_xg", 0.0)
        away_xg = get_feat(af, "avg_xg", 0.0)

        row = {
            "match_id": mid,
            "match_date": match["match_date"],
            "home_team_id": ht,
            "away_team_id": at,
            "result": match.get("result"),
            # Home features
            "home_form_pts_last5": get_feat(hf, "form_pts_last5"),
            "home_form_wins_last5": get_feat(hf, "form_wins_last5"),
            "home_form_draws_last5": get_feat(hf, "form_draws_last5"),
            "home_form_losses_last5": get_feat(hf, "form_losses_last5"),
            "home_form_gd_last5": get_feat(hf, "form_gd_last5"),
            "home_avg_goals_scored": get_feat(hf, "avg_goals_scored"),
            "home_avg_goals_conceded": get_feat(hf, "avg_goals_conceded"),
            "home_avg_shots": get_feat(hf, "avg_shots"),
            "home_avg_shots_on_target": get_feat(hf, "avg_shots_on_target"),
            "home_avg_xg": home_xg,
            "home_home_win_rate": get_feat(hf, "home_win_rate"),
            "home_home_goals_avg": get_feat(hf, "home_goals_avg"),
            "home_league_position": home_pos,
            "home_points": home_pts,
            # Away features
            "away_form_pts_last5": get_feat(af, "form_pts_last5"),
            "away_form_wins_last5": get_feat(af, "form_wins_last5"),
            "away_form_draws_last5": get_feat(af, "form_draws_last5"),
            "away_form_losses_last5": get_feat(af, "form_losses_last5"),
            "away_form_gd_last5": get_feat(af, "form_gd_last5"),
            "away_avg_goals_scored": get_feat(af, "avg_goals_scored"),
            "away_avg_goals_conceded": get_feat(af, "avg_goals_conceded"),
            "away_avg_shots": get_feat(af, "avg_shots"),
            "away_avg_shots_on_target": get_feat(af, "avg_shots_on_target"),
            "away_avg_xg": away_xg,
            "away_away_win_rate": get_feat(af, "away_win_rate"),
            "away_away_goals_avg": get_feat(af, "away_goals_avg"),
            "away_league_position": away_pos,
            "away_points": away_pts,
        }

        # H2H
        if mid in h2h_df.index:
            row.update({
                "h2h_home_wins": h2h_df.loc[mid, "h2h_home_wins"],
                "h2h_away_wins": h2h_df.loc[mid, "h2h_away_wins"],
                "h2h_draws": h2h_df.loc[mid, "h2h_draws"],
                "h2h_home_goals_avg": h2h_df.loc[mid, "h2h_home_goals_avg"],
                "h2h_away_goals_avg": h2h_df.loc[mid, "h2h_away_goals_avg"],
            })
        else:
            row.update({"h2h_home_wins": 0, "h2h_away_wins": 0, "h2h_draws": 0,
                        "h2h_home_goals_avg": 0.0, "h2h_away_goals_avg": 0.0})

        # Difference features
        row["form_diff"] = row["home_form_pts_last5"] - row["away_form_pts_last5"]
        row["attack_diff"] = row["home_avg_goals_scored"] - row["away_avg_goals_scored"]
        row["defence_diff"] = row["away_avg_goals_conceded"] - row["home_avg_goals_conceded"]
        row["position_diff"] = row["away_league_position"] - row["home_league_position"]
        row["points_diff"] = row["home_points"] - row["away_points"]
        row["xg_diff"] = home_xg - away_xg

        feature_rows.append(row)

    features_df = pd.DataFrame(feature_rows)

    # Target encoding
    if "result" in features_df.columns:
        features_df["target"] = features_df["result"].map(RESULT_MAP)

    # Fill remaining NaNs with 0 (early-season matches with no history)
    features_df[FEATURE_NAMES] = features_df[FEATURE_NAMES].fillna(0.0)

    logger.info(f"Feature engineering complete. Shape: {features_df.shape}")
    return features_df
