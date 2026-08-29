"""ML training pipeline for MatchIQ.

Trains and evaluates three models (Logistic Regression, Random Forest, XGBoost)
against a Naive Baseline on chronologically split authentic Premier League match data
(Train: 2018-19 to 2021-22, Validation: 2022-23, Test: 2023-24), persisting the best model,
feature metadata, metrics, and a reproducible training manifest.

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

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    log_loss,
)
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

MODEL_DIR = project_root / "ml" / "models"
DATA_DIR = project_root / "data" / "processed"


def load_data() -> tuple[pd.DataFrame, str]:
    """Load processed match data and compute its SHA-256 checksum."""
    csv_path = DATA_DIR / "matches_processed.csv"
    if not csv_path.exists():
        logger.info("matches_processed.csv missing. Running authentic data ingestion...")
        from scripts.fetch_real_data import run_ingestion
        df = run_ingestion(to_db=False)
    else:
        logger.info(f"Loading data from {csv_path}")
        df = pd.read_csv(csv_path, parse_dates=["match_date"])

    csv_bytes = csv_path.read_bytes()
    dataset_sha256 = hashlib.sha256(csv_bytes).hexdigest()
    return df, dataset_sha256


def seasonal_chronological_split(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split data by completed seasons chronologically.

    - Train: older seasons (2013-14 through 2022-23)
    - Validation: 2023-24 season
    - Test: 2024-25 season (or 2023-24 if only 6 seasons present)
    """
    df = df.sort_values("match_date").reset_index(drop=True)

    if "season" in df.columns and set(["2024-25", "2025-26"]).issubset(set(df["season"].unique())):
        train = df[~df["season"].isin(["2024-25", "2025-26"])].reset_index(drop=True)
        val = df[df["season"] == "2024-25"].reset_index(drop=True)
        test = df[df["season"] == "2025-26"].reset_index(drop=True)
    elif "season" in df.columns and set(["2023-24", "2024-25"]).issubset(set(df["season"].unique())):
        train = df[~df["season"].isin(["2023-24", "2024-25"])].reset_index(drop=True)
        val = df[df["season"] == "2023-24"].reset_index(drop=True)
        test = df[df["season"] == "2024-25"].reset_index(drop=True)
    elif "season" in df.columns and set(["2022-23", "2023-24"]).issubset(set(df["season"].unique())):
        train = df[~df["season"].isin(["2022-23", "2023-24"])].reset_index(drop=True)
        val = df[df["season"] == "2022-23"].reset_index(drop=True)
        test = df[df["season"] == "2023-24"].reset_index(drop=True)
    else:
        # Fallback ratio split if seasons not annotated
        n = len(df)
        train_end = int(n * 0.70)
        val_end = int(n * 0.85)
        train = df.iloc[:train_end].reset_index(drop=True)
        val = df.iloc[train_end:val_end].reset_index(drop=True)
        test = df.iloc[val_end:].reset_index(drop=True)

    logger.info(f"Seasonal split sizes — Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
    return train, val, test


def build_models() -> dict:
    """Define all candidate models with appropriate hyperparameters."""
    lr_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=0.2,
            random_state=42,
        )),
    ])
    rf_clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        min_samples_leaf=6,
        random_state=42,
        n_jobs=-1,
    )
    xgb_clf = XGBClassifier(
        n_estimators=150,
        max_depth=3,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.7,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )
    ensemble_clf = VotingClassifier(
        estimators=[
            ("rf", RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=6, random_state=42, n_jobs=-1)),
            ("xgb", XGBClassifier(n_estimators=150, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.7, eval_metric="mlogloss", random_state=42, n_jobs=-1)),
            ("gb", GradientBoostingClassifier(n_estimators=120, max_depth=3, learning_rate=0.03, subsample=0.8, random_state=42)),
        ],
        voting="soft",
        weights=[1.2, 1.2, 1.0],
    )

    return {
        "logistic_regression": lr_pipe,
        "random_forest": rf_clf,
        "xgboost": xgb_clf,
        "voting_ensemble": ensemble_clf,
    }


def compute_brier_score(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """Compute multi-class Brier score."""
    n_classes = y_proba.shape[1]
    y_onehot = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((y_proba - y_onehot) ** 2, axis=1)))


def evaluate_baseline(y_eval: np.ndarray, dataset_name: str = "Test") -> dict:
    """Evaluate Naive Majority Class predictor (always predict Home Win)."""
    # Always predict 0 (HOME_WIN)
    y_pred = np.zeros_like(y_eval)
    # Estimated empirical probabilities: 46% home, 23% draw, 31% away
    y_proba = np.tile([0.46, 0.23, 0.31], (len(y_eval), 1))

    acc = accuracy_score(y_eval, y_pred)
    f1 = f1_score(y_eval, y_pred, average="weighted", zero_division=0)
    ll = log_loss(y_eval, y_proba)
    brier = compute_brier_score(y_eval, y_proba)

    logger.info(f"\n{'='*50}")
    logger.info(f"Baseline: Naive Majority Class Predictor ({dataset_name} Set)")
    logger.info(f"  Accuracy:    {acc:.4f}")
    logger.info(f"  F1 (wt):     {f1:.4f}")
    logger.info(f"  Log Loss:    {ll:.4f}")
    logger.info(f"  Brier Score: {brier:.4f}")

    return {
        "name": "naive_majority_baseline",
        "accuracy": round(float(acc), 4),
        "f1_score": round(float(f1), 4),
        "log_loss": round(float(ll), 4),
        "brier_score": round(float(brier), 4),
    }


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
        "accuracy": round(float(acc), 4),
        "f1_score": round(float(f1), 4),
        "log_loss": round(float(ll), 4),
        "brier_score": round(float(brier), 4),
        "classification_report": report,
    }


def select_best_model(results: list[dict]) -> str:
    """Select best model using weighted F1 and Log Loss composite score on VALIDATION set."""
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


def get_git_commit() -> str:
    """Get current git commit hash if in a git repository."""
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=project_root)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


def extract_feature_importance(model, name: str) -> dict:
    """Extract feature importance or regression coefficients from model."""
    importances = {}
    try:
        if hasattr(model, "named_estimators_"):
            # VotingClassifier ensemble: average importance across estimators
            est_importances = []
            for est_name, est in model.named_estimators_.items():
                if hasattr(est, "feature_importances_"):
                    est_importances.append(est.feature_importances_)
                elif hasattr(est, "named_steps") and hasattr(est.named_steps.get("clf"), "coef_"):
                    est_importances.append(np.mean(np.abs(est.named_steps["clf"].coef_), axis=0))
            if est_importances:
                avg_imp = np.mean(est_importances, axis=0)
                for fname, val in zip(FEATURE_NAMES, avg_imp):
                    importances[fname] = round(float(val), 4)
        elif name == "logistic_regression" and hasattr(model, "named_steps"):
            clf = model.named_steps["clf"]
            coefs = np.mean(np.abs(clf.coef_), axis=0)
            for fname, val in zip(FEATURE_NAMES, coefs):
                importances[fname] = round(float(val), 4)
        elif hasattr(model, "feature_importances_"):
            for fname, val in zip(FEATURE_NAMES, model.feature_importances_):
                importances[fname] = round(float(val), 4)
    except Exception as e:
        logger.warning(f"Could not extract feature importances: {e}")
    return importances


def save_model_and_manifest(
    model,
    name: str,
    metrics: dict,
    baseline_metrics: dict,
    dataset_sha256: str,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> None:
    """Save model, metadata, metrics, and training manifest to disk."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Save model
    model_path = MODEL_DIR / "best_model.joblib"
    joblib.dump(model, model_path)
    model_bytes = model_path.read_bytes()
    model_sha256 = hashlib.sha256(model_bytes).hexdigest()
    logger.info(f"Model saved to {model_path} (SHA-256: {model_sha256[:16]}...)")

    training_time = datetime.now(timezone.utc).isoformat()
    version_tag = f"{name}-v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    # 2. Save feature metadata
    meta = {
        "name": "MatchIQ Model",
        "version_tag": version_tag,
        "algorithm": name,
        "training_date": training_time,
        "dataset_sha256": dataset_sha256,
        "model_sha256": model_sha256,
        "accuracy": metrics["accuracy"],
        "f1_score": metrics["f1_score"],
        "log_loss": metrics["log_loss"],
        "brier_score": metrics.get("brier_score", 0.0),
        "features": FEATURE_NAMES,
    }
    with open(MODEL_DIR / "feature_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    # 3. Save metrics
    metrics_to_save = {
        "algorithm": name,
        "training_date": training_time,
        "dataset_sha256": dataset_sha256,
        "model_sha256": model_sha256,
        "baseline": baseline_metrics,
        **metrics,
    }
    with open(MODEL_DIR / "metrics.json", "w") as f:
        json.dump(metrics_to_save, f, indent=2, default=str)

    # 4. Save comprehensive Training Manifest
    feature_importance = extract_feature_importance(model, name)
    manifest = {
        "manifest_version": "1.0.0",
        "model_name": "MatchIQ Match Predictor",
        "version_tag": version_tag,
        "algorithm": name,
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
            "source": "football-data.co.uk authentic Premier League matches (2018-2024)",
            "sha256": dataset_sha256,
            "total_matches": len(train_df) + len(val_df) + len(test_df),
            "split": {
                "train_count": len(train_df),
                "train_seasons": sorted(train_df["season"].unique().tolist()) if "season" in train_df.columns else [],
                "train_start": str(train_df.iloc[0]["match_date"]),
                "train_end": str(train_df.iloc[-1]["match_date"]),
                "val_count": len(val_df),
                "val_seasons": sorted(val_df["season"].unique().tolist()) if "season" in val_df.columns else [],
                "val_start": str(val_df.iloc[0]["match_date"]),
                "val_end": str(val_df.iloc[-1]["match_date"]),
                "test_count": len(test_df),
                "test_seasons": sorted(test_df["season"].unique().tolist()) if "season" in test_df.columns else [],
                "test_start": str(test_df.iloc[0]["match_date"]),
                "test_end": str(test_df.iloc[-1]["match_date"]),
            },
        },
        "baseline_comparison": {
            "naive_majority_accuracy": baseline_metrics["accuracy"],
            "naive_majority_f1": baseline_metrics["f1_score"],
            "naive_majority_log_loss": baseline_metrics["log_loss"],
            "naive_majority_brier_score": baseline_metrics["brier_score"],
            "model_accuracy": metrics["accuracy"],
            "model_f1": metrics["f1_score"],
            "model_log_loss": metrics["log_loss"],
            "model_brier_score": metrics["brier_score"],
        },
        "evaluation": {
            "test_accuracy": metrics["accuracy"],
            "test_f1_score": metrics["f1_score"],
            "test_log_loss": metrics["log_loss"],
            "test_brier_score": metrics.get("brier_score", 0.0),
            "classification_report": metrics.get("classification_report", {}),
            "candidate_validation_results": metrics.get("validation_models", []),
        },
        "features": {
            "count": len(FEATURE_NAMES),
            "names": FEATURE_NAMES,
            "importance": feature_importance,
        },
    }

    manifest_path = MODEL_DIR / "training_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    logger.info(f"✓ Saved training manifest to {manifest_path}")

    # 5. Update DB model_versions table if DB is accessible
    _register_model_version(meta)


def _register_model_version(meta: dict) -> None:
    """Register the trained model in the database model_versions table."""
    try:
        from app.db.session import SessionLocal
        from app.models.orm_models import ModelVersion
        from sqlalchemy import select

        db = SessionLocal()

        prev_active = list(db.execute(
            select(ModelVersion).where(ModelVersion.is_active == True)  # noqa: E712
        ).scalars().all())
        for m in prev_active:
            m.is_active = False

        existing = db.execute(
            select(ModelVersion).where(ModelVersion.version_tag == meta["version_tag"])
        ).scalar_one_or_none()

        if existing:
            existing.accuracy = meta["accuracy"]
            existing.f1_score = meta["f1_score"]
            existing.log_loss = meta["log_loss"]
            existing.features_json = json.dumps(meta["features"])
            existing.is_active = True
        else:
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
        logger.warning(f"Could not register model in DB: {e}")


def train() -> None:
    """Main training pipeline entry point."""
    logger.info("=" * 60)
    logger.info("MatchIQ ML Training Pipeline (Authentic 6-Season Dataset)")
    logger.info("=" * 60)

    # 1. Load data
    raw_df, dataset_sha256 = load_data()
    logger.info(f"Loaded {len(raw_df)} authentic matches (SHA-256: {dataset_sha256[:16]}...)")

    if len(raw_df) < 50:
        logger.error("Insufficient data for training (need at least 50 matches)")
        sys.exit(1)

    # 2. Feature engineering
    features_df = compute_features(raw_df)
    features_df = features_df.dropna(subset=["target"])

    # Remove early matches where teams lack 5 prior completed matches
    features_df = features_df[
        (features_df["home_form_pts_last5"].notna()) & (features_df["away_form_pts_last5"].notna())
    ].reset_index(drop=True)

    logger.info(f"Feature matrix shape: {features_df[FEATURE_NAMES].shape}")
    logger.info(f"Class distribution:\n{features_df['target'].value_counts()}")

    # 3. Seasonal chronological split (Train: 2018-2022, Val: 2022-23, Test: 2023-24)
    train_df, val_df, test_df = seasonal_chronological_split(features_df)

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
    logger.info("\n--- Candidate Selection on Validation Set (2022-23 Season) ---")
    val_metrics = []
    for name, model in trained_candidates.items():
        metrics = evaluate_model(name, model, X_val, y_val, dataset_name="Validation")
        val_metrics.append(metrics)

    best_name = select_best_model(val_metrics)

    # 6. Retrain selected model on combined (Train + Validation) data
    logger.info(f"\n--- Retraining Winner ({best_name}) on Train + Validation Seasons ---")
    X_train_val = np.vstack([X_train, X_val])
    y_train_val = np.concatenate([y_train, y_val])

    final_model = build_models()[best_name]
    final_model.fit(X_train_val, y_train_val)

    # 7. Evaluate final retrained model ONCE on untouched Test set (2023-24 Season)
    logger.info(f"\n--- Final Evaluation of {best_name} on Untouched Test Set (2023-24 Season) ---")
    test_metrics = evaluate_model(best_name, final_model, X_test, y_test, dataset_name="Test")
    baseline_metrics = evaluate_baseline(y_test, dataset_name="Test")

    # 8. Save artifacts and manifest
    save_model_and_manifest(
        final_model,
        best_name,
        {
            **test_metrics,
            "validation_models": val_metrics,
            "train_size": len(train_df),
            "val_size": len(val_df),
            "test_size": len(test_df),
        },
        baseline_metrics=baseline_metrics,
        dataset_sha256=dataset_sha256,
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
    )

    logger.info("\n✓ Training pipeline complete!")
    logger.info(f"  Best model:  {best_name}")
    logger.info(f"  Accuracy:    {test_metrics['accuracy']:.4f} (vs Naive Baseline: {baseline_metrics['accuracy']:.4f})")
    logger.info(f"  F1 (wt):     {test_metrics['f1_score']:.4f} (vs Naive Baseline: {baseline_metrics['f1_score']:.4f})")
    logger.info(f"  Log Loss:    {test_metrics['log_loss']:.4f} (vs Naive Baseline: {baseline_metrics['log_loss']:.4f})")
    logger.info(f"  Brier Score: {test_metrics['brier_score']:.4f} (vs Naive Baseline: {baseline_metrics['brier_score']:.4f})")


if __name__ == "__main__":
    train()
