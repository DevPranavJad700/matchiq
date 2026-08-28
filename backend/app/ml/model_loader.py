"""ML model loader — loads the trained model once at startup.

The model is intentionally loaded once and cached as a module-level singleton.
This avoids reloading from disk on every prediction request.
"""

import json
import logging
import os
from pathlib import Path

import joblib
import numpy as np

logger = logging.getLogger(__name__)

_model = None
_feature_names: list[str] = []
_model_metadata: dict = {}
_explainer = None


def _get_model_dir() -> Path:
    """Resolve the model directory, supporting both dev and Docker contexts."""
    env_dir = os.environ.get("MODEL_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.extend([
        Path("ml/models"),
        Path("../ml/models"),
    ])
    for p in candidates:
        if p.exists():
            return p
    return Path("ml/models")


def load_model() -> bool:
    """Load the model, feature metadata, and SHAP explainer from disk.

    Returns True if successfully loaded, False otherwise.
    """
    global _model, _feature_names, _model_metadata, _explainer

    model_dir = _get_model_dir()
    model_path = model_dir / "best_model.joblib"
    meta_path = model_dir / "feature_metadata.json"

    if not model_path.exists():
        logger.warning(f"Model file not found at {model_path}. Predictions unavailable.")
        return False

    try:
        _model = joblib.load(model_path)
        logger.info(f"Model loaded from {model_path}")

        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
                _feature_names = meta.get("features", [])
                _model_metadata = meta
            logger.info(f"Feature metadata loaded: {len(_feature_names)} features")

        # Load SHAP explainer (TreeExplainer for RF/XGBoost, LinearExplainer/Explainer for Pipelines)
        try:
            import shap
            # Extract final estimator if model is a Pipeline
            clf = _model.named_steps.get("clf", _model) if hasattr(_model, "named_steps") else _model
            
            try:
                _explainer = shap.TreeExplainer(clf)
                logger.info("SHAP TreeExplainer initialized")
            except Exception:
                try:
                    _explainer = shap.Explainer(clf)
                    logger.info("SHAP Explainer initialized")
                except Exception:
                    _explainer = clf  # fallback to direct model coefficient inspection
                    logger.info("SHAP direct coefficient fallback initialized")
        except Exception as e:
            logger.warning(f"SHAP explainer unavailable: {e}. Explanations will use coefficient weights.")
            _explainer = None

        return True

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return False


def get_model():
    """Return the loaded model. Raises RuntimeError if not loaded."""
    if _model is None:
        raise RuntimeError("Model not loaded. Run load_model() first.")
    return _model


def get_feature_names() -> list[str]:
    return _feature_names


def get_model_metadata() -> dict:
    return _model_metadata


def get_explainer():
    return _explainer


def is_model_loaded() -> bool:
    return _model is not None


def predict_proba(feature_vector: np.ndarray) -> np.ndarray:
    """Run inference. Returns probabilities array of shape (1, 3)."""
    model = get_model()
    return model.predict_proba(feature_vector)


def explain_prediction(feature_vector: np.ndarray) -> list[dict]:
    """Generate SHAP or feature impact explanation for a prediction.

    Returns a list of {feature, value, impact, description} dicts,
    sorted by absolute impact descending.
    """
    if _model is None:
        return []

    try:
        proba = predict_proba(feature_vector)[0]
        best_class = int(np.argmax(proba))
        class_shap = None

        # 1. Try SHAP explainer if available
        if _explainer is not None and not hasattr(_explainer, "coef_"):
            try:
                # If pipeline, transform feature vector first
                X_trans = feature_vector
                if hasattr(_model, "named_steps") and "scaler" in _model.named_steps:
                    X_trans = _model.named_steps["scaler"].transform(feature_vector)

                shap_values = _explainer.shap_values(X_trans)

                if isinstance(shap_values, list):
                    class_shap = shap_values[best_class][0]
                elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
                    class_shap = shap_values[0, :, best_class]
                elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 2:
                    class_shap = shap_values[0]
            except Exception as se:
                logger.debug(f"SHAP explanation call bypassed: {se}")

        # 2. Fallback to coefficient-based feature contribution for linear/logistic models
        if class_shap is None:
            clf = _model.named_steps.get("clf", _model) if hasattr(_model, "named_steps") else _model
            scaler = _model.named_steps.get("scaler", None) if hasattr(_model, "named_steps") else None

            if hasattr(clf, "coef_"):
                coefs = clf.coef_[best_class] if clf.coef_.ndim > 1 else clf.coef_
                X_trans = scaler.transform(feature_vector)[0] if scaler else feature_vector[0]
                class_shap = X_trans * coefs
            else:
                # Feature importance fallback for RF/XGBoost
                importances = getattr(clf, "feature_importances_", np.zeros(len(_feature_names)))
                class_shap = feature_vector[0] * importances

        factors = []
        for fname, fval, impact in zip(_feature_names, feature_vector[0], class_shap):
            factors.append(
                {
                    "feature": fname,
                    "value": round(float(fval), 4),
                    "impact": round(float(impact), 4),
                    "description": _feature_to_description(fname, float(fval), float(impact)),
                }
            )

        # Sort by absolute impact, return top 10
        factors.sort(key=lambda x: abs(x["impact"]), reverse=True)
        return factors[:10]

    except Exception as e:
        logger.warning(f"Feature explanation failed: {e}")
        return []


def _feature_to_description(feature: str, value: float, impact: float) -> str:
    """Convert a feature name + value into a human-readable description."""
    direction = "positive" if impact > 0 else "negative"
    magnitude = "strongly" if abs(impact) > 0.15 else ("moderately" if abs(impact) > 0.05 else "slightly")

    label_map = {
        "home_form_pts_last5": f"Home team earned {value:.0f} pts from last 5 matches",
        "away_form_pts_last5": f"Away team earned {value:.0f} pts from last 5 matches",
        "home_avg_goals_scored": f"Home team scores {value:.2f} goals/match on avg",
        "away_avg_goals_scored": f"Away team scores {value:.2f} goals/match on avg",
        "home_avg_goals_conceded": f"Home team concedes {value:.2f} goals/match on avg",
        "away_avg_goals_conceded": f"Away team concedes {value:.2f} goals/match on avg",
        "home_league_position": f"Home team is {value:.0f}th in the league",
        "away_league_position": f"Away team is {value:.0f}th in the league",
        "form_diff": f"Home form advantage of {value:.2f} pts",
        "attack_diff": f"Attack strength difference: {value:.2f}",
        "defence_diff": f"Defence strength difference: {value:.2f}",
        "position_diff": f"League position difference: {value:.0f}",
        "h2h_home_wins": f"Home team won {value:.0f} of last H2H meetings",
        "h2h_away_wins": f"Away team won {value:.0f} of last H2H meetings",
        "home_home_win_rate": f"Home team wins {value*100:.0f}% of home matches",
        "away_away_win_rate": f"Away team wins {value*100:.0f}% of away matches",
    }

    base = label_map.get(feature, f"{feature.replace('_', ' ').title()}: {value:.3f}")
    return f"{base} ({magnitude} {direction} impact)"
