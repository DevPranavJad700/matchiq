"""Prediction service — orchestrates feature building, inference, and persistence."""

import json
import logging

from sqlalchemy.orm import Session

from app.ml import model_loader
from app.models.orm_models import Prediction
from app.repositories.league_repository import PredictionRepository
from app.repositories.team_repository import TeamRepository
from app.schemas.schemas import ExplanationFactor, PredictionOut, ProbabilitiesOut, TeamSummary
from app.services.feature_builder import FeatureBuilderService

logger = logging.getLogger(__name__)

# Map numeric class index to result label
CLASS_LABELS = {0: "HOME_WIN", 1: "DRAW", 2: "AWAY_WIN"}


def _compute_confidence(max_prob: float) -> str:
    """Classify prediction confidence based on maximum probability."""
    if max_prob >= 0.60:
        return "HIGH"
    elif max_prob >= 0.45:
        return "MEDIUM"
    return "LOW"


class PredictionService:
    """Orchestrates match outcome prediction end-to-end."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.team_repo = TeamRepository(db)
        self.prediction_repo = PredictionRepository(db)
        self.feature_builder = FeatureBuilderService(db)

    def predict(self, home_team_id: int, away_team_id: int) -> PredictionOut:
        """
        Full prediction pipeline:
        1. Validate teams exist
        2. Build feature vector from DB
        3. Run model inference
        4. Generate SHAP explanation
        5. Persist prediction
        6. Return structured response
        """
        # 1. Validate teams
        home_team = self.team_repo.get_by_id(home_team_id)
        away_team = self.team_repo.get_by_id(away_team_id)

        if home_team is None:
            raise ValueError(f"Home team ID {home_team_id} not found")
        if away_team is None:
            raise ValueError(f"Away team ID {away_team_id} not found")
        if home_team_id == away_team_id:
            raise ValueError("Home and away teams must be different")

        if not model_loader.is_model_loaded():
            raise RuntimeError("Prediction model is not loaded. Run the training pipeline first.")

        # 2. Build feature vector
        logger.info(f"Building features for {home_team.name} vs {away_team.name}")
        feature_vector = self.feature_builder.build_features_for_prediction(
            home_team_id, away_team_id
        )

        # 3. Inference
        proba = model_loader.predict_proba(feature_vector)[0]
        predicted_class_idx = int(proba.argmax())
        predicted_result = CLASS_LABELS[predicted_class_idx]
        confidence = _compute_confidence(float(proba.max()))

        logger.info(
            f"Prediction: {predicted_result} | Probs: H={proba[0]:.3f} D={proba[1]:.3f} A={proba[2]:.3f}"
        )

        # 4. SHAP explanation
        raw_explanations = model_loader.explain_prediction(feature_vector)
        explanation_factors = [
            ExplanationFactor(**f) for f in raw_explanations
        ]

        # 5. Get active model version
        active_model = self.prediction_repo.get_active_model_version()
        model_version_id = active_model.id if active_model else None
        model_version_tag = active_model.version_tag if active_model else model_loader.get_model_metadata().get("version_tag", "unknown")

        # 6. Persist to DB
        prediction = Prediction(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            model_version_id=model_version_id,
            home_win_probability=round(float(proba[0]), 4),
            draw_probability=round(float(proba[1]), 4),
            away_win_probability=round(float(proba[2]), 4),
            predicted_result=predicted_result,
            confidence=confidence,
            explanation_json=json.dumps([f.model_dump() for f in explanation_factors]),
        )
        saved = self.prediction_repo.create(prediction)

        return PredictionOut(
            id=saved.id,
            home_team=TeamSummary(id=home_team.id, name=home_team.name, short_name=home_team.short_name),
            away_team=TeamSummary(id=away_team.id, name=away_team.name, short_name=away_team.short_name),
            probabilities=ProbabilitiesOut(
                home_win=round(float(proba[0]), 4),
                draw=round(float(proba[1]), 4),
                away_win=round(float(proba[2]), 4),
            ),
            predicted_result=predicted_result,
            confidence=confidence,
            model_version=model_version_tag,
            explanation=explanation_factors,
            created_at=saved.created_at,
        )
