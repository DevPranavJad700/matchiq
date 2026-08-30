"""Dixon-Coles (1997) Goal-Based Poisson Model Engine for MatchIQ.

Implements the classic statistical model by Mark J. Dixon and Stuart G. Coles:
'Modelling Association Football Scores and Inefficiencies in the Football Betting Market'
Applied Statistics, 46(2), 265-280 (1997).

Models home and away goals as Poisson processes with team attack/defense ratings,
home pitch advantage, time-decay weighting, and low-score bivariate correlation.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

logger = logging.getLogger(__name__)


def tau(x: int, y: int, lam: float, mu: float, rho: float) -> float:
    """Dixon-Coles low-score bivariate interaction factor for (0,0), (0,1), (1,0), (1,1)."""
    if x == 0 and y == 0:
        return max(1e-6, 1.0 - lam * mu * rho)
    elif x == 0 and y == 1:
        return max(1e-6, 1.0 + lam * rho)
    elif x == 1 and y == 0:
        return max(1e-6, 1.0 + mu * rho)
    elif x == 1 and y == 1:
        return max(1e-6, 1.0 - rho)
    return 1.0


class DixonColesEngine:
    """Production Dixon-Coles goal model for match outcome and scoreline forecasting."""

    def __init__(self, xi: float = 0.0019, max_goals: int = 10):
        """
        Args:
            xi: Time decay half-life parameter (default 0.0019 ~ approx 1 year half-life).
            max_goals: Maximum score matrix dimension (0 to max_goals).
        """
        self.xi = xi
        self.max_goals = max_goals
        self.teams: List[str] = []
        self.team_to_idx: Dict[str, int] = {}
        self.attack_params: np.ndarray = np.array([])
        self.defense_params: np.ndarray = np.array([])
        self.home_advantage: float = 0.25
        self.rho: float = -0.05
        self.is_fitted: bool = False
        self.fitted_date: Optional[str] = None

    def fit(self, df: pd.DataFrame) -> "DixonColesEngine":
        """
        Fit attack/defense ratings, home advantage, and rho from historical match data.

        Args:
            df: DataFrame containing ['home_team_name', 'away_team_name', 'home_goals', 'away_goals', 'match_date']
        """
        logger.info(f"Fitting Dixon-Coles engine on {len(df)} matches...")
        matches_df = df.dropna(subset=["home_goals", "away_goals", "home_team_name", "away_team_name"]).copy()
        
        # Build team dictionary
        self.teams = sorted(list(set(matches_df["home_team_name"].unique()) | set(matches_df["away_team_name"].unique())))
        self.team_to_idx = {t: i for i, t in enumerate(self.teams)}
        n_teams = len(self.teams)

        # Parse match dates for time decay
        if "match_date" in matches_df.columns:
            matches_df["dt"] = pd.to_datetime(matches_df["match_date"])
            max_date = matches_df["dt"].max()
            days_diff = (max_date - matches_df["dt"]).dt.total_seconds() / 86400.0
            weights = np.exp(-self.xi * days_diff).values
        else:
            weights = np.ones(len(matches_df))

        home_idx = matches_df["home_team_name"].map(self.team_to_idx).values
        away_idx = matches_df["away_team_name"].map(self.team_to_idx).values
        hg = matches_df["home_goals"].values.astype(int)
        ag = matches_df["away_goals"].values.astype(int)
        n_matches = len(matches_df)

        # Initial parameter vector:
        # [attack_0 ... attack_N-1, defense_0 ... defense_N-1, home_advantage, rho]
        init_att = np.zeros(n_teams)
        init_def = np.zeros(n_teams)
        init_gamma = 0.25
        init_rho = -0.05
        init_params = np.concatenate([init_att, init_def, [init_gamma, init_rho]])

        def loss_func(params: np.ndarray) -> float:
            att = params[:n_teams]
            defe = params[n_teams:2*n_teams]
            gamma = params[-2]
            rho = params[-1]

            # Zero-sum constraint penalty: sum(att) == 0
            constraint_penalty = 1000.0 * (np.sum(att) ** 2)

            log_lam = att[home_idx] + defe[away_idx] + gamma
            log_mu = att[away_idx] + defe[home_idx]
            lam = np.clip(np.exp(log_lam), 1e-4, 15.0)
            mu = np.clip(np.exp(log_mu), 1e-4, 15.0)

            # Fully vectorized bivariate correction
            tau_vals = np.ones(n_matches, dtype=np.float64)
            m00 = (hg == 0) & (ag == 0)
            m01 = (hg == 0) & (ag == 1)
            m10 = (hg == 1) & (ag == 0)
            m11 = (hg == 1) & (ag == 1)

            tau_vals[m00] = np.clip(1.0 - lam[m00] * mu[m00] * rho, 1e-6, 10.0)
            tau_vals[m01] = np.clip(1.0 + lam[m01] * rho, 1e-6, 10.0)
            tau_vals[m10] = np.clip(1.0 + mu[m10] * rho, 1e-6, 10.0)
            tau_vals[m11] = np.clip(1.0 - rho, 1e-6, 10.0)

            # Poisson log likelihood
            poisson_h = hg * np.log(lam) - lam
            poisson_a = ag * np.log(mu) - mu
            nll = -np.sum(weights * (np.log(tau_vals) + poisson_h + poisson_a))
            return float(nll + constraint_penalty)

        res = minimize(
            loss_func,
            init_params,
            method="L-BFGS-B",
            options={"maxiter": 250}
        )

        opt = res.x
        self.attack_params = opt[:n_teams] - np.mean(opt[:n_teams])
        self.defense_params = opt[n_teams:2*n_teams] - np.mean(opt[n_teams:2*n_teams])
        self.home_advantage = float(opt[-2])
        self.rho = float(np.clip(opt[-1], -0.25, 0.25))
        self.is_fitted = True
        self.fitted_date = datetime.now(timezone.utc).isoformat()

        logger.info(
            f"✓ Dixon-Coles fitted successfully across {n_teams} teams: "
            f"HomeAdv={self.home_advantage:.3f}, rho={self.rho:.4f}"
        )
        return self

    def _get_team_params(self, team_name: str) -> Tuple[float, float]:
        """Get attack and defense params for a team, defaulting to league average if unseen."""
        if team_name in self.team_to_idx:
            idx = self.team_to_idx[team_name]
            return float(self.attack_params[idx]), float(self.defense_params[idx])
        return 0.0, 0.0

    def get_expected_goals(self, home_team: str, away_team: str) -> Tuple[float, float]:
        """Calculate expected goals lambda (home) and mu (away)."""
        att_h, def_h = self._get_team_params(home_team)
        att_a, def_a = self._get_team_params(away_team)
        lam = float(np.clip(np.exp(att_h + def_a + self.home_advantage), 0.2, 6.0))
        mu = float(np.clip(np.exp(att_a + def_h), 0.2, 6.0))
        return round(lam, 3), round(mu, 3)

    def predict_score_matrix(self, home_team: str, away_team: str) -> np.ndarray:
        """Compute full (max_goals+1) x (max_goals+1) bivariate score probability matrix."""
        lam, mu = self.get_expected_goals(home_team, away_team)
        matrix = np.zeros((self.max_goals + 1, self.max_goals + 1))

        for x in range(self.max_goals + 1):
            for y in range(self.max_goals + 1):
                p_h = poisson.pmf(x, lam)
                p_a = poisson.pmf(y, mu)
                t_val = tau(x, y, lam, mu, self.rho)
                matrix[x, y] = p_h * p_a * t_val

        # Normalize matrix sum to 1.0
        matrix_sum = np.sum(matrix)
        if matrix_sum > 0:
            matrix /= matrix_sum
        return matrix

    def predict_proba(self, home_team: str, away_team: str) -> np.ndarray:
        """
        Compute calibrated 3-way match outcome probabilities [P(Home Win), P(Draw), P(Away Win)].

        Returns:
            np.ndarray of shape (3,) summing to 1.0.
        """
        matrix = self.predict_score_matrix(home_team, away_team)
        p_home = float(np.sum(np.tril(matrix, -1)))
        p_draw = float(np.sum(np.diag(matrix)))
        p_away = float(np.sum(np.triu(matrix, 1)))
        total = p_home + p_draw + p_away
        return np.array([p_home / total, p_draw / total, p_away / total])

    def predict_top_scorelines(self, home_team: str, away_team: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """Return the top N most likely exact scorelines with their probabilities."""
        matrix = self.predict_score_matrix(home_team, away_team)
        flat_indices = np.argsort(matrix.ravel())[::-1][:top_n]
        results = []
        for idx in flat_indices:
            x, y = np.unravel_index(idx, matrix.shape)
            results.append({
                "score": f"{x} - {y}",
                "home_goals": int(x),
                "away_goals": int(y),
                "probability": round(float(matrix[x, y]), 4),
            })
        return results

    def save(self, path: Path) -> None:
        """Persist fitted model artifacts."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "teams": self.teams,
            "team_to_idx": self.team_to_idx,
            "attack_params": self.attack_params,
            "defense_params": self.defense_params,
            "home_advantage": self.home_advantage,
            "rho": self.rho,
            "xi": self.xi,
            "max_goals": self.max_goals,
            "is_fitted": self.is_fitted,
            "fitted_date": self.fitted_date,
        }
        joblib.dump(data, path)
        logger.info(f"Saved Dixon-Coles model to {path}")

    @classmethod
    def load(cls, path: Path) -> "DixonColesEngine":
        """Load persisted model artifact."""
        data = joblib.load(path)
        engine = cls(xi=data.get("xi", 0.0019), max_goals=data.get("max_goals", 10))
        engine.teams = data["teams"]
        engine.team_to_idx = data["team_to_idx"]
        engine.attack_params = data["attack_params"]
        engine.defense_params = data["defense_params"]
        engine.home_advantage = data["home_advantage"]
        engine.rho = data["rho"]
        engine.is_fitted = data["is_fitted"]
        engine.fitted_date = data.get("fitted_date")
        return engine
