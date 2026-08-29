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
                    class_shap = np.array(shap_values[best_class]).flatten()
                elif isinstance(shap_values, np.ndarray):
                    if shap_values.ndim == 3:
                        if shap_values.shape[2] == len(proba):
                            class_shap = shap_values[0, :, best_class]
                        elif shap_values.shape[0] == len(proba):
                            class_shap = shap_values[best_class, 0, :]
                        else:
                            class_shap = shap_values[0, :, 0]
                    elif shap_values.ndim == 2:
                        class_shap = shap_values[0]
                    elif shap_values.ndim == 1:
                        class_shap = shap_values
            except Exception as se:
                logger.debug(f"SHAP explanation call bypassed: {se}")

        # 2. Fallback to coefficient-based feature contribution for linear/logistic models
        if class_shap is None or np.all(np.abs(class_shap) < 1e-6):
            clf = _model.named_steps.get("clf", _model) if hasattr(_model, "named_steps") else _model
            scaler = _model.named_steps.get("scaler", None) if hasattr(_model, "named_steps") else None

            if hasattr(clf, "coef_"):
                coefs = clf.coef_[best_class] if clf.coef_.ndim > 1 else clf.coef_
                X_trans = scaler.transform(feature_vector)[0] if scaler else feature_vector[0]
                class_shap = X_trans * coefs
            elif hasattr(clf, "feature_importances_"):
                # Feature importance signed by correlation/difference
                importances = clf.feature_importances_
                # Normalize and sign by feature value deviation
                class_shap = importances * np.sign(feature_vector[0])

        # 3. Robust marginal sensitivity fallback if still zero
        if class_shap is None or np.all(np.abs(class_shap) < 1e-6):
            base_p = proba[best_class]
            class_shap = np.zeros(len(_feature_names))
            for j in range(len(_feature_names)):
                X_pert = feature_vector.copy()
                X_pert[0, j] = 0.0
                pert_p = predict_proba(X_pert)[0][best_class]
                class_shap[j] = base_p - pert_p

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


def _ordinal(n: float | int) -> str:
    """Format integers as ordinals: 1st, 2nd, 3rd, 4th..."""
    try:
        val = int(round(float(n)))
        if 11 <= (val % 100) <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(val % 10, "th")
        return f"{val}{suffix}"
    except Exception:
        return f"{n}"


def _feature_to_description(feature: str, value: float, impact: float) -> str:
    """Convert a feature name + value into a human-readable description."""
    direction = "boost" if impact >= 0 else "drag"
    magnitude = "Strong" if abs(impact) > 0.08 else ("Moderate" if abs(impact) > 0.025 else "Slight")

    label_map = {
        "home_form_pts_last5": f"Home team earned {value:.0f} pts in last 5 matches",
        "away_form_pts_last5": f"Away team earned {value:.0f} pts in last 5 matches",
        "home_form_wins_last5": f"Home team won {value:.0f} of last 5 matches",
        "away_form_wins_last5": f"Away team won {value:.0f} of last 5 matches",
        "home_form_draws_last5": f"Home team drew {value:.0f} of last 5 matches",
        "away_form_draws_last5": f"Away team drew {value:.0f} of last 5 matches",
        "home_form_losses_last5": f"Home team lost {value:.0f} of last 5 matches",
        "away_form_losses_last5": f"Away team lost {value:.0f} of last 5 matches",
        "home_form_gd_last5": f"Home team goal difference in last 5 matches: {value:+.0f}",
        "away_form_gd_last5": f"Away team goal difference in last 5 matches: {value:+.0f}",
        "home_avg_goals_scored": f"Home team scores {value:.2f} goals/match on avg",
        "away_avg_goals_scored": f"Away team scores {value:.2f} goals/match on avg",
        "home_avg_goals_conceded": f"Home team concedes {value:.2f} goals/match on avg",
        "away_avg_goals_conceded": f"Away team concedes {value:.2f} goals/match on avg",
        "home_avg_shots": f"Home team averages {value:.1f} shots per match",
        "away_avg_shots": f"Away team averages {value:.1f} shots per match",
        "home_avg_shots_on_target": f"Home team averages {value:.1f} shots on target",
        "away_avg_shots_on_target": f"Away team averages {value:.1f} shots on target",
        "home_avg_xg": f"Home team estimated xG: {value:.2f}",
        "away_avg_xg": f"Away team estimated xG: {value:.2f}",
        "home_league_position": f"Home team is {_ordinal(value)} in current standings",
        "away_league_position": f"Away team is {_ordinal(value)} in current standings",
        "home_points": f"Home team has accumulated {value:.0f} pts this campaign",
        "away_points": f"Away team has accumulated {value:.0f} pts this campaign",
        "points_diff": f"Pre-match points differential: {value:+.0f} pts",
        "position_diff": f"Pre-match league position diff: {value:+.0f} places",
        "form_diff": f"Recent 5-match form advantage: {value:+.2f} pts",
        "attack_diff": f"Attack strength differential: {value:+.2f} goals",
        "defence_diff": f"Defence strength differential: {value:+.2f} goals conceded",
        "xg_diff": f"Expected goals (xG) differential: {value:+.2f}",
        "h2h_home_wins": f"Home team won {value:.0f} recent head-to-head matches",
        "h2h_away_wins": f"Away team won {value:.0f} recent head-to-head matches",
        "h2h_draws": f"Recent head-to-head drawn matches: {value:.0f}",
        "home_home_win_rate": f"Home team wins {value*100:.0f}% of home fixtures",
        "away_away_win_rate": f"Away team wins {value*100:.0f}% of away fixtures",
        "home_home_goals_avg": f"Home team scores {value:.2f} goals/match at home",
        "away_away_goals_avg": f"Away team scores {value:.2f} goals/match away",
        "home_elo": f"Home team Elo power rating: {value:.0f}",
        "away_elo": f"Away team Elo power rating: {value:.0f}",
        "elo_diff": f"Home Elo advantage of {value:+.0f} pts (inc. home ground)",
        "home_rest_days": f"Home squad has {value:.0f} days of recovery",
        "away_rest_days": f"Away squad has {value:.0f} days of recovery",
        "rest_diff": f"Schedule recovery advantage: {value:+.0f} days",
    }

    base = label_map.get(feature, f"{feature.replace('_', ' ').title()}: {value:.3f}")
    return f"{base} ({magnitude} {direction})"
