"""ML training pipeline for MatchIQ.

Trains and evaluates three models (Logistic Regression, Random Forest, XGBoost)
on chronologically split football match data and persists the best model.

Usage:
    python -m ml.training.train

The script:
1. Loads processed match data from the database or CSV
2. Engineers features (with anti-leakage measures)
3. Splits chronologically (train/val/test)
4. Trains all models
5. Evaluates on the held-out test set
6. Selects the best model by weighted F1 + Log Loss
7. Saves the model, metadata, and metrics
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    log_loss,
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from ml.features.feature_engineering import FEATURE_NAMES, compute_features  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

MODEL_DIR = project_root / "ml" / "models"
DATA_DIR = project_root / "data" / "processed"


def load_data() -> pd.DataFrame:
    """Load processed match data. Prefers DB, falls back to CSV."""
    csv_path = DATA_DIR / "matches_processed.csv"
    if csv_path.exists():
        logger.info(f"Loading data from {csv_path}")
        df = pd.read_csv(csv_path, parse_dates=["match_date"])
        return df

    # Try loading from DB
    try:
        from app.db.session import SessionLocal
        from app.models.orm_models import Match
        from sqlalchemy import select

        db = SessionLocal()
        logger.info("Loading data from database...")
        matches = list(db.execute(
            select(Match).where(Match.result.isnot(None)).order_by(Match.match_date)
        ).scalars().all())

        rows = []
        for m in matches:
            stats = {s.team_id: s for s in m.statistics}
            hs = stats.get(m.home_team_id)
            as_ = stats.get(m.away_team_id)
            rows.append({
                "match_id": m.id,
                "match_date": m.match_date,
                "home_team_id": m.home_team_id,
                "away_team_id": m.away_team_id,
                "result": m.result,
                "home_goals": m.home_score,
                "away_goals": m.away_score,
                "home_shots": hs.shots if hs else None,
                "away_shots": as_.shots if as_ else None,
                "home_sot": hs.shots_on_target if hs else None,
                "away_sot": as_.shots_on_target if as_ else None,
                "home_xg": hs.xg if hs else None,
                "away_xg": as_.xg if as_ else None,
            })
        db.close()
        return pd.DataFrame(rows)
    except Exception as e:
        logger.error(f"Could not load from DB: {e}")
        raise FileNotFoundError(
            "No data found. Run scripts/seed_demo_data.py first, "
            "or ensure data/processed/matches_processed.csv exists."
        )


def chronological_split(
    df: pd.DataFrame, train_frac: float = 0.70, val_frac: float = 0.15
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split data chronologically to avoid temporal leakage.

    Time-based splitting is critical for football prediction:
    we must never let future match results influence model training.
    """
    df = df.sort_values("match_date").reset_index(drop=True)
    n = len(df)
    train_end = int(n * train_frac)
    val_end = int(n * (train_frac + val_frac))

    train = df.iloc[:train_end]
    val = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]

    logger.info(f"Split sizes — Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
    return train, val, test


def build_models() -> dict:
    """Define all candidate models with appropriate hyperparameters."""
    return {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                max_iter=1000,
                C=1.0,
                class_weight="balanced",
                random_state=42,
            )),
        ]),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "xgboost": XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=-1,
        ),
    }


def compute_brier_score(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """Compute multi-class Brier score."""
    n_classes = y_proba.shape[1]
    y_onehot = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((y_proba - y_onehot) ** 2, axis=1)))


def evaluate_model(name: str, model, X_eval: np.ndarray, y_eval: np.ndarray, dataset_name: str = "Validation") -> dict:
    """Evaluate a trained model and return metrics dict."""
    y_pred = model.predict(X_eval)
    y_proba = model.predict_proba(X_eval)

    acc = accuracy_score(y_eval, y_pred)
    f1 = f1_score(y_eval, y_pred, average="weighted")
    ll = log_loss(y_eval, y_proba)
    brier = compute_brier_score(y_eval, y_proba)

    report = classification_report(
        y_eval, y_pred, target_names=["HOME_WIN", "DRAW", "AWAY_WIN"], output_dict=True
    )

    logger.info(f"\n{'='*50}")
    logger.info(f"Model: {name} ({dataset_name} Set)")
    logger.info(f"  Accuracy:    {acc:.4f}")
    logger.info(f"  F1 (wt):     {f1:.4f}")
    logger.info(f"  Log Loss:    {ll:.4f}")
    logger.info(f"  Brier Score: {brier:.4f}")
    logger.info(f"\n{classification_report(y_eval, y_pred, target_names=['HOME_WIN', 'DRAW', 'AWAY_WIN'])}")

    return {
        "name": name,
        "accuracy": round(acc, 4),
        "f1_score": round(f1, 4),
        "log_loss": round(ll, 4),
        "brier_score": round(brier, 4),
        "classification_report": report,
    }


def select_best_model(results: list[dict]) -> str:
    """Select best model using weighted F1 and Log Loss composite score on VALIDATION set.

    We do NOT select solely on accuracy because Draw is the minority class.
    The composite score rewards both discriminative power (F1) and
    calibrated probabilities (low log loss).

    Score = F1 * 0.6 + (1 - normalized_log_loss) * 0.4
    """
    max_ll = max(r["log_loss"] for r in results)
    min_ll = min(r["log_loss"] for r in results)
    ll_range = max_ll - min_ll if max_ll != min_ll else 1.0

    scored = []
    for r in results:
        norm_ll = (r["log_loss"] - min_ll) / ll_range  # 0=best, 1=worst
        score = r["f1_score"] * 0.6 + (1 - norm_ll) * 0.4
        scored.append((r["name"], score))
        logger.info(f"  Validation Composite score {r['name']}: {score:.4f}")

    best = max(scored, key=lambda x: x[1])
    logger.info(f"\n✓ Best model selected on Validation set: {best[0]} (score: {best[1]:.4f})")
    return best[0]


def save_model(model, name: str, metrics: dict) -> None:
    """Save model, metadata, and metrics to disk."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Save model
    model_path = MODEL_DIR / "best_model.joblib"
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")

    # Save feature metadata
    version_tag = f"{name}-v{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    meta = {
        "name": "MatchIQ Model",
        "version_tag": version_tag,
        "algorithm": name,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "accuracy": metrics["accuracy"],
        "f1_score": metrics["f1_score"],
        "log_loss": metrics["log_loss"],
        "brier_score": metrics.get("brier_score", 0.0),
        "features": FEATURE_NAMES,
    }
    with open(MODEL_DIR / "feature_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    # Save all model comparison metrics
    metrics_to_save = {
        "algorithm": name,
        "training_date": meta["training_date"],
        **metrics,
    }
    with open(MODEL_DIR / "metrics.json", "w") as f:
        json.dump(metrics_to_save, f, indent=2, default=str)

    logger.info("Feature metadata and metrics saved")

    # Update DB model_versions table if DB is accessible
    _register_model_version(meta)


def _register_model_version(meta: dict) -> None:
    """Register the trained model in the database model_versions table."""
    try:
        from app.db.session import SessionLocal
        from app.models.orm_models import ModelVersion
        from sqlalchemy import select

        db = SessionLocal()

        # Deactivate previous active models
        prev_active = list(db.execute(
            select(ModelVersion).where(ModelVersion.is_active == True)  # noqa: E712
        ).scalars().all())
        for m in prev_active:
            m.is_active = False

        mv = ModelVersion(
            name=meta["name"],
            version_tag=meta["version_tag"],
            algorithm=meta["algorithm"],
            accuracy=meta["accuracy"],
            f1_score=meta["f1_score"],
            log_loss=meta["log_loss"],
            features_json=json.dumps(meta["features"]),
            is_active=True,
        )
        db.add(mv)
        db.commit()
        db.close()
        logger.info(f"Model version '{meta['version_tag']}' registered in database")
    except Exception as e:
        logger.warning(f"Could not register model in DB (training may be offline): {e}")


def train() -> None:
    """Main training pipeline entry point."""
    logger.info("=" * 60)
    logger.info("MatchIQ ML Training Pipeline")
    logger.info("=" * 60)

    # 1. Load data
    raw_df = load_data()
    logger.info(f"Loaded {len(raw_df)} matches")

    if len(raw_df) < 50:
        logger.error("Insufficient data for training (need at least 50 matches)")
        sys.exit(1)

    # 2. Feature engineering
    features_df = compute_features(raw_df)
    features_df = features_df.dropna(subset=["target"])

    # Remove early season matches where teams lack 5 prior completed matches
    features_df = features_df[
        (features_df["home_form_pts_last5"].notna()) & (features_df["away_form_pts_last5"].notna())
    ].reset_index(drop=True)

    logger.info(f"Feature matrix shape: {features_df[FEATURE_NAMES].shape}")
    logger.info(f"Class distribution:\n{features_df['target'].value_counts()}")

    # 3. Chronological split
    train_df, val_df, test_df = chronological_split(features_df)

    X_train = train_df[FEATURE_NAMES].values
    y_train = train_df["target"].values.astype(int)
    X_val = val_df[FEATURE_NAMES].values
    y_val = val_df["target"].values.astype(int)
    X_test = test_df[FEATURE_NAMES].values
    y_test = test_df["target"].values.astype(int)

    # 4. Train candidate models on Train set
    candidate_models = build_models()
    trained_candidates = {}

    for name, model in candidate_models.items():
        logger.info(f"\nTraining candidate model: {name}...")
        if name == "xgboost":
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False,
            )
        else:
            model.fit(X_train, y_train)
        trained_candidates[name] = model

    # 5. Evaluate candidate models on Validation set to select the winner
    logger.info("\n--- Candidate Selection on Validation Set ---")
    val_metrics = []
    for name, model in trained_candidates.items():
        metrics = evaluate_model(name, model, X_val, y_val, dataset_name="Validation")
        val_metrics.append(metrics)

    best_name = select_best_model(val_metrics)

    # 6. Retrain selected model on combined (Train + Validation) data
    logger.info(f"\n--- Retraining Winner ({best_name}) on Train + Validation Set ---")
    X_train_val = np.vstack([X_train, X_val])
    y_train_val = np.concatenate([y_train, y_val])

    final_model = build_models()[best_name]
    final_model.fit(X_train_val, y_train_val)

    # 7. Evaluate final retrained model ONCE on untouched Test set
    logger.info(f"\n--- Final Evaluation of {best_name} on Untouched Test Set ---")
    test_metrics = evaluate_model(best_name, final_model, X_test, y_test, dataset_name="Test")

    # 8. Save artifacts
    save_model(final_model, best_name, {
        **test_metrics,
        "validation_models": val_metrics,
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
    })

    logger.info("\n✓ Training pipeline complete!")
    logger.info(f"  Best model:  {best_name}")
    logger.info(f"  Accuracy:    {test_metrics['accuracy']:.4f}")
    logger.info(f"  F1 (wt):     {test_metrics['f1_score']:.4f}")
    logger.info(f"  Log Loss:    {test_metrics['log_loss']:.4f}")
    logger.info(f"  Brier Score: {test_metrics['brier_score']:.4f}")


if __name__ == "__main__":
    train()
