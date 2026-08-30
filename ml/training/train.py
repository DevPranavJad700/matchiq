"""ML training pipeline for MatchIQ.

Trains and evaluates candidate models (Logistic Regression, Random Forest, XGBoost, Voting Ensemble)
alongside statistical Dixon-Coles goal modeling and betting-market implied probability baselines
on chronologically split authentic Premier League match data (13 seasons: 2013–2026, 4,940 matches).

Features:
- Ranked Probability Score (RPS) calculation (Epstein 1969, Constantinou & Fenton 2012)
- Betting-market closing odds de-vigged implied probability benchmark
- Probability calibration via CalibratedClassifierCV
- Statistical Dixon-Coles (1997) goal-based Poisson modeling
- Decision threshold optimization for balanced 3-way outcome recall (resolving draw-blindness)
- Reproducible model artifacts, calibration metrics, and training manifest.

Usage:
    python -m ml.training.train
"""

import hashlib
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    log_loss,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost
from xgboost import XGBClassifier

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from ml.features.feature_engineering import FEATURE_NAMES, compute_features  # noqa: E402
from ml.models.dixon_coles import DixonColesEngine  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

MODEL_DIR = project_root / "ml" / "models"
DATA_DIR = project_root / "data" / "processed"


def load_data() -> Tuple[pd.DataFrame, str]:
    """Load processed match data and compute its SHA-256 checksum."""
    csv_path = DATA_DIR / "matches_processed.csv"
    if not csv_path.exists():
        logger.info("matches_processed.csv missing. Running authentic data ingestion...")
        from scripts.fetch_real_data import parse_and_clean_matches, save_dataset_and_provenance
        df = parse_and_clean_matches()
        save_dataset_and_provenance(df)
    else:
        logger.info(f"Loading data from {csv_path}")
        df = pd.read_csv(csv_path, parse_dates=["match_date"])

    csv_bytes = csv_path.read_bytes()
    dataset_sha256 = hashlib.sha256(csv_bytes).hexdigest()
    return df, dataset_sha256


def seasonal_chronological_split(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split data by completed seasons chronologically.

    - Train (70%): 2013-14 through 2022-23 (3,458 matches)
    - Validation (15%): 2023-24 and 2024-25 (741 matches)
    - Test (15%): 2025-26 (741 matches)
    """
    df = df.sort_values("match_date").reset_index(drop=True)

    if "season" in df.columns and set(["2024-25", "2025-26"]).issubset(set(df["season"].unique())):
        train = df[~df["season"].isin(["2024-25", "2025-26"])].reset_index(drop=True)
        val = df[df["season"] == "2024-25"].reset_index(drop=True)
        test = df[df["season"] == "2025-26"].reset_index(drop=True)
    else:
        n = len(df)
        train_end = int(n * 0.70)
        val_end = int(n * 0.85)
        train = df.iloc[:train_end].reset_index(drop=True)
        val = df.iloc[train_end:val_end].reset_index(drop=True)
        test = df.iloc[val_end:].reset_index(drop=True)

    logger.info(f"Seasonal split sizes — Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
    return train, val, test


def compute_rps(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """
    Compute Ranked Probability Score (RPS) for ordered 3-way match outcomes (Home < Draw < Away).
    RPS is the standard metric in academic football forecasting (Epstein 1969; Constantinou & Fenton 2012).
    """
    N = len(y_true)
    cum_prob = np.cumsum(y_proba, axis=1)  # shape (N, 3)
    one_hot = np.zeros((N, 3))
    one_hot[np.arange(N), y_true] = 1.0
    cum_true = np.cumsum(one_hot, axis=1)
    rps_per_match = 0.5 * np.sum((cum_prob[:, :2] - cum_true[:, :2]) ** 2, axis=1)
    return float(np.mean(rps_per_match))


def compute_brier_score(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """Compute multi-class Brier score."""
    n_classes = y_proba.shape[1]
    y_onehot = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((y_proba - y_onehot) ** 2, axis=1)))


def evaluate_baseline(y_eval: np.ndarray, dataset_name: str = "Test") -> dict:
    """Evaluate Naive Majority Class predictor (always predict Home Win)."""
    y_pred = np.zeros_like(y_eval)
    y_proba = np.tile([0.46, 0.23, 0.31], (len(y_eval), 1))

    acc = accuracy_score(y_eval, y_pred)
    f1 = f1_score(y_eval, y_pred, average="weighted", zero_division=0)
    ll = log_loss(y_eval, y_proba)
    brier = compute_brier_score(y_eval, y_proba)
    rps = compute_rps(y_eval, y_proba)

    logger.info(f"\n{'='*55}")
    logger.info(f"Baseline: Naive Majority Class ({dataset_name} Set)")
    logger.info(f"  Accuracy:    {acc:.4f}")
    logger.info(f"  F1 (wt):     {f1:.4f}")
    logger.info(f"  Log Loss:    {ll:.4f}")
    logger.info(f"  Brier Score: {brier:.4f}")
    logger.info(f"  RPS:         {rps:.4f}")

    return {
        "name": "naive_majority_baseline",
        "accuracy": round(float(acc), 4),
        "f1_score": round(float(f1), 4),
        "log_loss": round(float(ll), 4),
        "brier_score": round(float(brier), 4),
        "rps": round(float(rps), 4),
    }


def evaluate_market_baseline(eval_df: pd.DataFrame, dataset_name: str = "Test") -> dict:
    """Evaluate closing betting market implied probabilities."""
    odds_cols = ["market_prob_home", "market_prob_draw", "market_prob_away"]
    if not all(col in eval_df.columns for col in odds_cols):
        return {}

    valid_df = eval_df.dropna(subset=odds_cols).copy()
    if valid_df.empty:
        return {}

    y_true = valid_df["target"].values.astype(int)
    y_proba = valid_df[odds_cols].values
    y_proba = y_proba / np.sum(y_proba, axis=1, keepdims=True)
    y_pred = np.argmax(y_proba, axis=1)

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    ll = log_loss(y_true, y_proba)
    brier = compute_brier_score(y_true, y_proba)
    rps = compute_rps(y_true, y_proba)

    logger.info(f"\n{'='*55}")
    logger.info(f"Benchmark: Closing Betting Market Odds ({dataset_name} Set, {len(valid_df)} matches)")
    logger.info(f"  Accuracy:    {acc:.4f}")
    logger.info(f"  F1 (wt):     {f1:.4f}")
    logger.info(f"  Log Loss:    {ll:.4f}")
    logger.info(f"  Brier Score: {brier:.4f}")
    logger.info(f"  RPS:         {rps:.4f}")

    return {
        "name": "betting_market_baseline",
        "accuracy": round(float(acc), 4),
        "f1_score": round(float(f1), 4),
        "log_loss": round(float(ll), 4),
        "brier_score": round(float(brier), 4),
        "rps": round(float(rps), 4),
    }


def build_candidate_models() -> dict:
    """Define base candidate models."""
    lr_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=0.2,
            class_weight="balanced",
            random_state=42,
        )),
    ])
    rf_clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_split=6,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    xgb_clf = XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.04,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="mlogloss",
        random_state=42,
    )
    gb_clf = GradientBoostingClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.04,
        subsample=0.8,
        random_state=42,
    )
    ensemble_clf = VotingClassifier(
        estimators=[
            ("rf", rf_clf),
            ("xgb", xgb_clf),
            ("gb", gb_clf),
        ],
        voting="soft",
    )

    return {
        "logistic_regression": lr_pipe,
        "random_forest": rf_clf,
        "xgboost": xgb_clf,
        "voting_ensemble": ensemble_clf,
    }


def evaluate_model(
    name: str,
    model,
    X_eval: np.ndarray,
    y_eval: np.ndarray,
    dataset_name: str = "Validation",
    draw_threshold: Optional[float] = None,
) -> dict:
    """Evaluate a trained model with both argmax and threshold-adjusted metrics."""
    y_proba = model.predict_proba(X_eval)
    y_pred_raw = model.predict(X_eval)

    # Standard argmax metrics
    acc_raw = accuracy_score(y_eval, y_pred_raw)
    f1_raw = f1_score(y_eval, y_pred_raw, average="weighted", zero_division=0)
    ll = log_loss(y_eval, y_proba)
    brier = compute_brier_score(y_eval, y_proba)
    rps = compute_rps(y_eval, y_proba)

    report_raw = classification_report(
        y_eval, y_pred_raw, target_names=["HOME_WIN", "DRAW", "AWAY_WIN"], output_dict=True, zero_division=0
    )

    # Threshold-tuned predictions if threshold provided
    tuned_info = {}
    if draw_threshold is not None:
        y_pred_tuned = np.argmax(y_proba, axis=1)
        draw_mask = y_proba[:, 1] >= draw_threshold
        y_pred_tuned[draw_mask] = 1

        acc_tuned = accuracy_score(y_eval, y_pred_tuned)
        f1_tuned = f1_score(y_eval, y_pred_tuned, average="weighted", zero_division=0)
        macro_f1_tuned = f1_score(y_eval, y_pred_tuned, average="macro", zero_division=0)
        report_tuned = classification_report(
            y_eval, y_pred_tuned, target_names=["HOME_WIN", "DRAW", "AWAY_WIN"], output_dict=True, zero_division=0
        )
        tuned_info = {
            "draw_threshold": round(draw_threshold, 4),
            "accuracy_tuned": round(float(acc_tuned), 4),
            "f1_weighted_tuned": round(float(f1_tuned), 4),
            "f1_macro_tuned": round(float(macro_f1_tuned), 4),
            "draw_recall_tuned": round(float(report_tuned["DRAW"]["recall"]), 4),
            "draw_precision_tuned": round(float(report_tuned["DRAW"]["precision"]), 4),
            "classification_report_tuned": report_tuned,
        }

    logger.info(f"\n{'='*55}")
    logger.info(f"Model: {name} ({dataset_name} Set)")
    logger.info(f"  Accuracy (argmax): {acc_raw:.4f}")
    logger.info(f"  F1 (weighted):     {f1_raw:.4f}")
    logger.info(f"  Log Loss:          {ll:.4f}")
    logger.info(f"  Brier Score:       {brier:.4f}")
    logger.info(f"  RPS:               {rps:.4f}")
    if draw_threshold is not None:
        logger.info(f"  Tuned Draw Recall (θ={draw_threshold:.3f}): {tuned_info['draw_recall_tuned']:.4f} (F1 wt: {tuned_info['f1_weighted_tuned']:.4f})")

    return {
        "name": name,
        "accuracy": round(float(acc_raw), 4),
        "f1_score": round(float(f1_raw), 4),
        "log_loss": round(float(ll), 4),
        "brier_score": round(float(brier), 4),
        "rps": round(float(rps), 4),
        "classification_report": report_raw,
        **tuned_info,
    }


def tune_draw_threshold(y_val: np.ndarray, y_proba_val: np.ndarray) -> float:
    """Find the optimal Draw threshold theta in [0.20, 0.35] that maximizes Macro F1."""
    best_theta = 0.3333
    best_score = 0.0
    for theta in np.linspace(0.20, 0.35, 31):
        y_pred = np.argmax(y_proba_val, axis=1)
        draw_mask = y_proba_val[:, 1] >= theta
        y_pred[draw_mask] = 1
        score = f1_score(y_val, y_pred, average="macro", zero_division=0)
        if score > best_score:
            best_score = score
            best_theta = theta
    logger.info(f"Optimal validation draw threshold: θ = {best_theta:.3f} (Macro F1 = {best_score:.4f})")
    return float(best_theta)


def tune_blend_weight(
    y_val: np.ndarray,
    ml_proba_val: np.ndarray,
    dc_proba_val: np.ndarray,
) -> Tuple[float, float, List[Dict[str, float]]]:
    """Perform grid search over blend weight w in [0.0, 1.0] to minimize validation RPS."""
    best_w = 0.5
    best_rps = 999.0
    sweep_results = []
    for w in np.linspace(0.0, 1.0, 21):
        w = round(float(w), 2)
        blend_val = w * ml_proba_val + (1.0 - w) * dc_proba_val
        rps = compute_rps(y_val, blend_val)
        ll = log_loss(y_val, blend_val)
        acc = accuracy_score(y_val, np.argmax(blend_val, axis=1))
        sweep_results.append({
            "weight_ml": w,
            "weight_dixon_coles": round(1.0 - w, 2),
            "val_rps": round(float(rps), 4),
            "val_log_loss": round(float(ll), 4),
            "val_accuracy": round(float(acc), 4),
        })
        if rps < best_rps:
            best_rps = rps
            best_w = w
    logger.info(f"Optimal validation blend weight: w_ML = {best_w:.2f}, w_DC = {1.0-best_w:.2f} (Val RPS = {best_rps:.4f})")
    return best_w, best_rps, sweep_results


def select_best_model(results: List[dict]) -> str:
    """Select best model using multi-metric composite score on VALIDATION set."""
    min_ll = min(r["log_loss"] for r in results)
    max_ll = max(r["log_loss"] for r in results)
    ll_range = max_ll - min_ll if max_ll != min_ll else 1.0

    scored = []
    for r in results:
        norm_ll = (r["log_loss"] - min_ll) / ll_range
        # 40% F1 score, 30% Log Loss, 30% RPS
        score = r["f1_score"] * 0.4 + (1.0 - norm_ll) * 0.3 + (1.0 - r["rps"]) * 0.3
        scored.append((r["name"], score))
        logger.info(f"  Validation composite score for {r['name']}: {score:.4f} (RPS: {r['rps']:.4f}, LL: {r['log_loss']:.4f})")

    best = max(scored, key=lambda x: x[1])
    logger.info(f"\n✓ Best model selected on Validation set: {best[0]} (composite score: {best[1]:.4f})")
    return best[0]


def extract_feature_importance(model, name: str) -> Dict[str, float]:
    """Extract feature importance weights."""
    importance = {}
    try:
        if hasattr(model, "feature_importances_"):
            vals = model.feature_importances_
            for f, v in zip(FEATURE_NAMES, vals):
                importance[f] = round(float(v), 4)
        elif hasattr(model, "estimator") and hasattr(model.estimator, "feature_importances_"):
            vals = model.estimator.feature_importances_
            for f, v in zip(FEATURE_NAMES, vals):
                importance[f] = round(float(v), 4)
        elif name == "logistic_regression" and hasattr(model, "named_steps"):
            coef = np.mean(np.abs(model.named_steps["clf"].coef_), axis=0)
            norm = coef / np.sum(coef)
            for f, v in zip(FEATURE_NAMES, norm):
                importance[f] = round(float(v), 4)
    except Exception as e:
        logger.warning(f"Could not extract feature importance: {e}")
    return importance


def get_git_commit() -> str:
    """Get current git commit hash."""
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=project_root)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


def train() -> None:
    """Main training pipeline entry point."""
    logger.info("=" * 65)
    logger.info("MatchIQ Machine Learning & Dixon-Coles Training Pipeline")
    logger.info("=" * 65)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    raw_df, dataset_sha256 = load_data()
    logger.info(f"Loaded {len(raw_df)} matches (Dataset SHA-256: {dataset_sha256[:16]}...)")

    # 2. Feature engineering
    features_df = compute_features(raw_df)
    features_df = features_df.dropna(subset=["target"])
    features_df = features_df[
        (features_df["home_form_pts_last5"].notna()) & (features_df["away_form_pts_last5"].notna())
    ].reset_index(drop=True)

    logger.info(f"Feature matrix shape: {features_df[FEATURE_NAMES].shape}")

    # 3. Seasonal chronological split
    train_df, val_df, test_df = seasonal_chronological_split(features_df)

    X_train, y_train = train_df[FEATURE_NAMES].values, train_df["target"].values.astype(int)
    X_val, y_val = val_df[FEATURE_NAMES].values, val_df["target"].values.astype(int)
    X_test, y_test = test_df[FEATURE_NAMES].values, test_df["target"].values.astype(int)

    # 4. Train Dixon-Coles Goal Engine
    logger.info("\n--- Training Dixon-Coles (1997) Goal Model Engine ---")
    dc_engine = DixonColesEngine(xi=0.0019)
    dc_engine.fit(train_df)
    dc_engine.save(MODEL_DIR / "dixon_coles.joblib")

    # Dixon-Coles validation metrics
    dc_val_probs = np.array([dc_engine.predict_proba(r["home_team_name"], r["away_team_name"]) for _, r in val_df.iterrows()])
    dc_val_rps = compute_rps(y_val, dc_val_probs)
    dc_val_ll = log_loss(y_val, dc_val_probs)
    dc_val_acc = accuracy_score(y_val, np.argmax(dc_val_probs, axis=1))
    logger.info(f"Dixon-Coles Validation Metrics — Acc: {dc_val_acc:.4f}, LogLoss: {dc_val_ll:.4f}, RPS: {dc_val_rps:.4f}")

    # 5. Train candidate ML models with CalibratedClassifierCV
    base_models = build_candidate_models()
    calibrated_models = {}

    for name, model in base_models.items():
        logger.info(f"\nTraining and calibrating candidate model: {name}...")
        if name == "xgboost":
            model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        else:
            model.fit(X_train, y_train)

        # Apply CalibratedClassifierCV (Platt scaling) using 5-fold CV on training split
        cal_model = CalibratedClassifierCV(estimator=model, method="sigmoid", cv=5)
        cal_model.fit(X_train, y_train)
        calibrated_models[name] = cal_model

    # 6. Evaluate candidate models on Validation set to select best candidate
    logger.info("\n--- Candidate Selection on Validation Set ---")
    val_metrics = []
    for name, cal_model in calibrated_models.items():
        metrics = evaluate_model(name, cal_model, X_val, y_val, dataset_name="Validation")
        val_metrics.append(metrics)

    best_name = select_best_model(val_metrics)

    # 7. Tune draw threshold and blend weight on validation set
    best_val_model = calibrated_models[best_name]
    best_val_proba = best_val_model.predict_proba(X_val)
    optimal_draw_threshold = tune_draw_threshold(y_val, best_val_proba)
    best_blend_w, best_val_blend_rps, blend_sweep = tune_blend_weight(y_val, best_val_proba, dc_val_probs)

    # 8. Retrain winner on combined Train + Validation data
    logger.info(f"\n--- Retraining Winner ({best_name}) on Train + Validation Data ---")
    X_train_val = np.vstack([X_train, X_val])
    y_train_val = np.concatenate([y_train, y_val])
    train_val_df = pd.concat([train_df, val_df]).reset_index(drop=True)

    # Retrain Dixon-Coles on Train + Validation
    dc_engine.fit(train_val_df)
    dc_engine.save(MODEL_DIR / "dixon_coles.joblib")

    # Retrain calibrated ML model
    base_final = build_candidate_models()[best_name]
    cal_final = CalibratedClassifierCV(estimator=base_final, method="sigmoid", cv=5)
    cal_final.fit(X_train_val, y_train_val)

    # 9. Evaluate candidate model ONCE on untouched Test set
    logger.info(f"\n--- Final Evaluation of {best_name} on Untouched Test Set ---")
    test_metrics = evaluate_model(
        best_name,
        cal_final,
        X_test,
        y_test,
        dataset_name="Test",
        draw_threshold=optimal_draw_threshold,
    )
    baseline_metrics = evaluate_baseline(y_test, dataset_name="Test")
    market_metrics = evaluate_market_baseline(test_df, dataset_name="Test")

    # Evaluate Dixon-Coles on Test set
    dc_test_probs = np.array([dc_engine.predict_proba(r["home_team_name"], r["away_team_name"]) for _, r in test_df.iterrows()])
    dc_test_rps = compute_rps(y_test, dc_test_probs)
    dc_test_ll = log_loss(y_test, dc_test_probs)
    dc_test_acc = accuracy_score(y_test, np.argmax(dc_test_probs, axis=1))
    logger.info(f"Dixon-Coles Test Metrics — Acc: {dc_test_acc:.4f}, LogLoss: {dc_test_ll:.4f}, RPS: {dc_test_rps:.4f}")

    # Evaluate Blended ML + Dixon-Coles Ensemble on Test set with validation-tuned weight
    blended_test_probs = best_blend_w * cal_final.predict_proba(X_test) + (1.0 - best_blend_w) * dc_test_probs
    blend_acc = accuracy_score(y_test, np.argmax(blended_test_probs, axis=1))
    blend_ll = log_loss(y_test, blended_test_probs)
    blend_brier = compute_brier_score(y_test, blended_test_probs)
    blend_rps = compute_rps(y_test, blended_test_probs)
    logger.info(f"\n--- Optimal Blended Model ({int(best_blend_w*100)}% ML + {int((1-best_blend_w)*100)}% Dixon-Coles) Test Performance ---")
    logger.info(f"  Accuracy:    {blend_acc:.4f}")
    logger.info(f"  Log Loss:    {blend_ll:.4f}")
    logger.info(f"  Brier Score: {blend_brier:.4f}")
    logger.info(f"  RPS:         {blend_rps:.4f}")

    # 10. Refit on 100% of authentic data for live production deployment
    logger.info("\n--- Refitting Final Production Model on Full 13-Season Dataset (4,940 matches) ---")
    X_all = features_df[FEATURE_NAMES].values
    y_all = features_df["target"].values.astype(int)
    base_prod = build_candidate_models()[best_name]
    prod_model = CalibratedClassifierCV(estimator=base_prod, method="sigmoid", cv=5)
    prod_model.fit(X_all, y_all)

    # Refit Dixon-Coles on full dataset
    dc_engine.fit(features_df)
    dc_engine.save(MODEL_DIR / "dixon_coles.joblib")

    # 11. Persist model, metadata, and manifest
    model_path = MODEL_DIR / "best_model.joblib"
    joblib.dump(prod_model, model_path)
    model_sha256 = hashlib.sha256(model_path.read_bytes()).hexdigest()

    training_time = datetime.now(timezone.utc).isoformat()
    version_tag = f"{best_name}-v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    meta = {
        "name": "MatchIQ Model",
        "version_tag": version_tag,
        "algorithm": best_name,
        "training_date": training_time,
        "dataset_sha256": dataset_sha256,
        "model_sha256": model_sha256,
        "accuracy": test_metrics["accuracy"],
        "f1_score": test_metrics["f1_score"],
        "log_loss": test_metrics["log_loss"],
        "brier_score": test_metrics["brier_score"],
        "rps": test_metrics["rps"],
        "optimal_draw_threshold": optimal_draw_threshold,
        "features": FEATURE_NAMES,
    }
    with open(MODEL_DIR / "feature_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    metrics_to_save = {
        "algorithm": best_name,
        "training_date": training_time,
        "dataset_sha256": dataset_sha256,
        "model_sha256": model_sha256,
        "baseline": baseline_metrics,
        "market_benchmark": market_metrics,
        "dixon_coles_test": {
            "accuracy": round(float(dc_test_acc), 4),
            "log_loss": round(float(dc_test_ll), 4),
            "rps": round(float(dc_test_rps), 4),
        },
        "blended_ensemble_test": {
            "accuracy": round(float(blend_acc), 4),
            "log_loss": round(float(blend_ll), 4),
            "brier_score": round(float(blend_brier), 4),
            "rps": round(float(blend_rps), 4),
        },
        "optimal_draw_threshold": round(optimal_draw_threshold, 4),
        "optimal_blend_weight_ml": round(float(best_blend_w), 2),
        "optimal_blend_weight_dixon_coles": round(float(1.0 - best_blend_w), 2),
        "blend_validation_sweep": blend_sweep,
        "validation_models": val_metrics,
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "full_dataset_size": len(features_df),
        **test_metrics,
    }
    with open(MODEL_DIR / "metrics.json", "w") as f:
        json.dump(metrics_to_save, f, indent=2, default=str)

    # Save comprehensive Training Manifest
    feature_importance = extract_feature_importance(prod_model, best_name)
    manifest = {
        "manifest_version": "2.0.0",
        "model_name": "MatchIQ Match Predictor",
        "version_tag": version_tag,
        "algorithm": best_name,
        "training_timestamp": training_time,
        "git_commit": get_git_commit(),
        "reproducibility": {
            "random_seed": 42,
            "python_version": sys.version.split()[0],
            "scikit_learn_version": sklearn.__version__,
            "xgboost_version": xgboost.__version__,
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
            "joblib_version": joblib.__version__,
        },
        "dataset": {
            "source": "football-data.co.uk authentic Premier League matches (2013-2026)",
            "sha256": dataset_sha256,
            "total_matches": len(features_df),
            "split": {
                "train_count": len(train_df),
                "val_count": len(val_df),
                "test_count": len(test_df),
            },
        },
        "baseline_comparison": {
            "naive_majority": baseline_metrics,
            "betting_market": market_metrics,
            "calibrated_model": {
                "accuracy": test_metrics["accuracy"],
                "f1_score": test_metrics["f1_score"],
                "log_loss": test_metrics["log_loss"],
                "brier_score": test_metrics["brier_score"],
                "rps": test_metrics["rps"],
            },
            "blended_dixon_coles": {
                "accuracy": round(float(blend_acc), 4),
                "log_loss": round(float(blend_ll), 4),
                "brier_score": round(float(blend_brier), 4),
                "rps": round(float(blend_rps), 4),
            },
        },
        "evaluation": {
            "test_metrics": test_metrics,
            "candidate_validation_results": val_metrics,
        },
        "features": {
            "count": len(FEATURE_NAMES),
            "names": FEATURE_NAMES,
            "importance": feature_importance,
        },
    }
    with open(MODEL_DIR / "training_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    logger.info("\n✓ Training pipeline complete!")
    logger.info(f"  Selected Model:   {best_name}")
    logger.info(f"  Test Accuracy:    {test_metrics['accuracy']:.4f} (Market Baseline: {market_metrics.get('accuracy', 0.0):.4f})")
    logger.info(f"  Test Log Loss:    {test_metrics['log_loss']:.4f} (Market Baseline: {market_metrics.get('log_loss', 0.0):.4f})")
    logger.info(f"  Test Brier Score: {test_metrics['brier_score']:.4f}")
    logger.info(f"  Test RPS:         {test_metrics['rps']:.4f} (Market Baseline: {market_metrics.get('rps', 0.0):.4f})")
    logger.info(f"  Draw Recall:      {test_metrics.get('draw_recall_tuned', 0.0):.4f} (Tuned θ={optimal_draw_threshold:.3f})")


if __name__ == "__main__":
    train()
