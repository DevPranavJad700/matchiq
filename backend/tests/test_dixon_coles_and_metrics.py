"""Tests for Dixon-Coles goal model, RPS scoring, and betting-market probability benchmarks."""

import numpy as np
import pandas as pd
import pytest

from ml.models.dixon_coles import DixonColesEngine
from ml.training.train import compute_rps, sweep_draw_thresholds


def test_compute_rps_perfect_prediction():
    """RPS should be exactly 0.0 when predicted probabilities match actual outcome with 100% certainty."""
    # Outcomes: 0 (Home), 1 (Draw), 2 (Away)
    y_true = np.array([0, 1, 2])
    y_proba = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ])
    rps = compute_rps(y_true, y_proba)
    assert rps == pytest.approx(0.0, abs=1e-6)


def test_compute_rps_known_benchmark():
    """RPS calculation matches analytical Epstein (1969) formula."""
    y_true = np.array([0])  # Actual: Home Win
    # Pred: 50% Home, 30% Draw, 20% Away
    # Cum Pred: [0.5, 0.8]
    # Cum True: [1.0, 1.0]
    # Diff: [-0.5, -0.2] -> squared: [0.25, 0.04] -> sum = 0.29 -> 0.5 * 0.29 = 0.145
    y_proba = np.array([[0.50, 0.30, 0.20]])
    rps = compute_rps(y_true, y_proba)
    assert rps == pytest.approx(0.145, abs=1e-5)


def test_dixon_coles_engine_fit_and_predict():
    """DixonColesEngine fits on synthetic matches and produces normalized score matrices."""
    synthetic_matches = pd.DataFrame([
        {"home_team_name": "Arsenal", "away_team_name": "Chelsea", "home_goals": 2, "away_goals": 1, "match_date": "2024-01-01"},
        {"home_team_name": "Chelsea", "away_team_name": "Liverpool", "home_goals": 1, "away_goals": 1, "match_date": "2024-01-08"},
        {"home_team_name": "Liverpool", "away_team_name": "Arsenal", "home_goals": 0, "away_goals": 2, "match_date": "2024-01-15"},
        {"home_team_name": "Arsenal", "away_team_name": "Liverpool", "home_goals": 3, "away_goals": 1, "match_date": "2024-01-22"},
    ])

    engine = DixonColesEngine(xi=0.0019)
    engine.fit(synthetic_matches)
    assert engine.is_fitted

    matrix = engine.predict_score_matrix("Arsenal", "Chelsea")
    assert matrix.shape == (11, 11)
    assert np.sum(matrix) == pytest.approx(1.0, abs=1e-4)

    probs = engine.predict_proba("Arsenal", "Chelsea")
    assert len(probs) == 3
    assert np.sum(probs) == pytest.approx(1.0, abs=1e-4)
    assert probs[0] > probs[2]  # Arsenal stronger in synthetic data

    lam, mu = engine.get_expected_goals("Arsenal", "Chelsea")
    assert 0.2 <= lam <= 6.0
    assert 0.2 <= mu <= 6.0

    scorelines = engine.predict_top_scorelines("Arsenal", "Chelsea", top_n=3)
    assert len(scorelines) == 3
    assert all("score" in s and "probability" in s for s in scorelines)


def test_sweep_draw_thresholds():
    """sweep_draw_thresholds evaluates a sweep across theta and records per-class statistics."""
    y_val = np.array([0, 1, 2, 1, 0, 2, 1, 0, 1, 2])
    y_proba_val = np.array([
        [0.60, 0.25, 0.15],
        [0.35, 0.35, 0.30],
        [0.20, 0.20, 0.60],
        [0.40, 0.32, 0.28],
        [0.55, 0.25, 0.20],
        [0.10, 0.15, 0.75],
        [0.30, 0.38, 0.32],
        [0.70, 0.15, 0.15],
        [0.35, 0.34, 0.31],
        [0.15, 0.25, 0.60],
    ])
    sweep = sweep_draw_thresholds(y_val, y_proba_val)
    assert len(sweep) > 0
    assert "theta" in sweep[0]
    assert "draw_recall" in sweep[0]
    assert "predicted_counts" in sweep[0]
