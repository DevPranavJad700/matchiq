"""Feature builder service — computes ML features from database records.

This module bridges the database and the ML model. Given two team IDs,
it queries the database to compute the same features used during training.

IMPORTANT: All features use only historical data (no future leakage).
"""

import logging
from datetime import datetime, timezone

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm_models import Match, Standing, TeamMatchStatistic

logger = logging.getLogger(__name__)

# Feature names must match exactly what was used during training
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
    # H2H
    "h2h_home_wins",
    "h2h_away_wins",
    "h2h_draws",
    "h2h_home_goals_avg",
    "h2h_away_goals_avg",
    # Difference features
    "form_diff",
    "attack_diff",
    "defence_diff",
    "position_diff",
    "points_diff",
    "xg_diff",
]


class FeatureBuilderService:
    """Builds feature vectors for match prediction from the database."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def build_features_for_prediction(
        self,
        home_team_id: int,
        away_team_id: int,
        as_of: datetime | None = None,
    ) -> np.ndarray:
        """Build a feature vector for a home_team vs away_team prediction.

        Args:
            home_team_id: ID of the home team
            away_team_id: ID of the away team
            as_of: Use only data before this datetime (default: now)

        Returns:
            numpy array of shape (1, n_features) ready for model.predict_proba()
        """
        if as_of is None:
            as_of = datetime.now(timezone.utc)

        home_features = self._compute_team_features(home_team_id, is_home=True, as_of=as_of)
        away_features = self._compute_team_features(away_team_id, is_home=False, as_of=as_of)
        h2h_features = self._compute_h2h_features(home_team_id, away_team_id, as_of=as_of)

        # Difference features (home - away)
        diff_features = {
            "form_diff": home_features["home_form_pts_last5"] - away_features["away_form_pts_last5"],
            "attack_diff": home_features["home_avg_goals_scored"] - away_features["away_avg_goals_scored"],
            "defence_diff": away_features["away_avg_goals_conceded"] - home_features["home_avg_goals_conceded"],
            "position_diff": away_features["away_league_position"] - home_features["home_league_position"],
            "points_diff": home_features["home_points"] - away_features["away_points"],
            "xg_diff": home_features["home_avg_xg"] - away_features["away_avg_xg"],
        }

        combined = {**home_features, **away_features, **h2h_features, **diff_features}
        vector = np.array([[combined.get(f, 0.0) for f in FEATURE_NAMES]], dtype=np.float64)
        return vector

    def _compute_team_features(
        self, team_id: int, is_home: bool, as_of: datetime
    ) -> dict:
        """Compute form, attack, defence, and league features for a team."""
        prefix = "home" if is_home else "away"

        # --- Last 10 completed matches ---
        recent_matches = self._get_recent_matches(team_id, as_of, limit=10)

        form5 = self._compute_form(team_id, recent_matches[:5])
        form10 = self._compute_form(team_id, recent_matches[:10])

        # --- Aggregate stats (last 10) ---
        stats = self._get_aggregate_stats(team_id, [m.id for m in recent_matches])

        # --- Home/Away specific performance ---
        if is_home:
            venue_matches = [m for m in recent_matches if m.home_team_id == team_id]
            venue_win_result = "H"
        else:
            venue_matches = [m for m in recent_matches if m.away_team_id == team_id]
            venue_win_result = "A"

        venue_wins = sum(1 for m in venue_matches if m.result == venue_win_result)
        venue_win_rate = venue_wins / len(venue_matches) if venue_matches else 0.0
        venue_goals = self._get_goals_for_venue(team_id, venue_matches, is_home)

        # --- League position / points ---
        standing = self._get_latest_standing(team_id)
        position = standing.position if standing else 10
        points = standing.points if standing else 0

        return {
            f"{prefix}_form_pts_last5": form5["points"],
            f"{prefix}_form_wins_last5": form5["wins"],
            f"{prefix}_form_draws_last5": form5["draws"],
            f"{prefix}_form_losses_last5": form5["losses"],
            f"{prefix}_form_gd_last5": form5["gd"],
            f"{prefix}_avg_goals_scored": stats["avg_goals_scored"],
            f"{prefix}_avg_goals_conceded": stats["avg_goals_conceded"],
            f"{prefix}_avg_shots": stats["avg_shots"],
            f"{prefix}_avg_shots_on_target": stats["avg_shots_on_target"],
            f"{prefix}_avg_xg": stats["avg_xg"],
            f"{prefix}_{'home' if is_home else 'away'}_win_rate": venue_win_rate,
            f"{prefix}_{'home' if is_home else 'away'}_goals_avg": venue_goals,
            f"{prefix}_league_position": float(position),
            f"{prefix}_points": float(points),
        }

    def _compute_form(self, team_id: int, matches: list) -> dict:
        """Compute form stats from a list of matches."""
        pts = wins = draws = losses = gf = ga = 0
        for m in matches:
            is_home = m.home_team_id == team_id
            result = m.result
            if result is None:
                continue
            if (is_home and result == "H") or (not is_home and result == "A"):
                pts += 3
                wins += 1
            elif result == "D":
                pts += 1
                draws += 1
            else:
                losses += 1

            # Find goals
            stat = next((s for s in m.statistics if s.team_id == team_id), None)
            if stat:
                gf += stat.goals or 0
                ga += stat.goals_conceded or 0

        return {"points": pts, "wins": wins, "draws": draws, "losses": losses, "gd": gf - ga}

    def _get_recent_matches(self, team_id: int, as_of: datetime, limit: int) -> list:
        """Get recent completed matches before as_of date."""
        stmt = (
            select(Match)
            .where(
                ((Match.home_team_id == team_id) | (Match.away_team_id == team_id)),
                Match.result.isnot(None),
                Match.match_date < as_of,
            )
            .order_by(Match.match_date.desc())
            .limit(limit)
        )
        matches = list(self.db.execute(stmt).scalars().all())

        # Load statistics eagerly for each match
        for match in matches:
            _ = match.statistics  # trigger load
        return matches

    def _get_aggregate_stats(self, team_id: int, match_ids: list[int]) -> dict:
        """Get average stats for a team across specific matches."""
        if not match_ids:
            return {
                "avg_goals_scored": 0.0, "avg_goals_conceded": 0.0,
                "avg_shots": 0.0, "avg_shots_on_target": 0.0, "avg_xg": 0.0,
            }

        stats = list(self.db.execute(
            select(TeamMatchStatistic).where(
                TeamMatchStatistic.team_id == team_id,
                TeamMatchStatistic.match_id.in_(match_ids),
            )
        ).scalars().all())

        if not stats:
            return {
                "avg_goals_scored": 0.0, "avg_goals_conceded": 0.0,
                "avg_shots": 0.0, "avg_shots_on_target": 0.0, "avg_xg": 0.0,
            }

        def safe_avg(attr: str) -> float:
            vals = [getattr(s, attr) for s in stats if getattr(s, attr) is not None]
            return round(sum(vals) / len(vals), 3) if vals else 0.0

        return {
            "avg_goals_scored": safe_avg("goals"),
            "avg_goals_conceded": safe_avg("goals_conceded"),
            "avg_shots": safe_avg("shots"),
            "avg_shots_on_target": safe_avg("shots_on_target"),
            "avg_xg": safe_avg("xg"),
        }

    def _get_goals_for_venue(self, team_id: int, matches: list, is_home: bool) -> float:
        """Average goals scored at home or away."""
        goals = []
        for m in matches:
            stat = next((s for s in m.statistics if s.team_id == team_id), None)
            if stat and stat.goals is not None:
                goals.append(stat.goals)
        return round(sum(goals) / len(goals), 3) if goals else 0.0

    def _get_latest_standing(self, team_id: int):
        return self.db.execute(
            select(Standing)
            .where(Standing.team_id == team_id)
            .order_by(Standing.updated_at.desc())
            .limit(1)
        ).scalar_one_or_none()

    def _compute_h2h_features(
        self, home_team_id: int, away_team_id: int, as_of: datetime
    ) -> dict:
        """Compute head-to-head statistics from last 5 meetings."""
        stmt = (
            select(Match)
            .where(
                (
                    (Match.home_team_id == home_team_id) & (Match.away_team_id == away_team_id)
                )
                | (
                    (Match.home_team_id == away_team_id) & (Match.away_team_id == home_team_id)
                ),
                Match.result.isnot(None),
                Match.match_date < as_of,
            )
            .order_by(Match.match_date.desc())
            .limit(5)
        )
        h2h_matches = list(self.db.execute(stmt).scalars().all())

        home_wins = draws = away_wins = 0
        home_goals_list = []
        away_goals_list = []

        for m in h2h_matches:
            if m.home_team_id == home_team_id:
                if m.result == "H":
                    home_wins += 1
                elif m.result == "D":
                    draws += 1
                else:
                    away_wins += 1
                home_goals_list.append(m.home_score or 0)
                away_goals_list.append(m.away_score or 0)
            else:
                if m.result == "A":
                    home_wins += 1
                elif m.result == "D":
                    draws += 1
                else:
                    away_wins += 1
                home_goals_list.append(m.away_score or 0)
                away_goals_list.append(m.home_score or 0)

        return {
            "h2h_home_wins": float(home_wins),
            "h2h_away_wins": float(away_wins),
            "h2h_draws": float(draws),
            "h2h_home_goals_avg": round(sum(home_goals_list) / len(home_goals_list), 2) if home_goals_list else 0.0,
            "h2h_away_goals_avg": round(sum(away_goals_list) / len(away_goals_list), 2) if away_goals_list else 0.0,
        }
