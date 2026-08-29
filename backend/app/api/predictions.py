"""Predictions API router."""

import json
import logging
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.schemas import (
    ExplanationFactor,
    PredictRequest,
    PredictionOut,
    ProbabilitiesOut,
    TeamSummary,
)
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predict", tags=["predictions"])
logger = logging.getLogger(__name__)

# In-memory rate limiting state: ip -> list of timestamps
_rate_limit_store = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 30
RATE_LIMIT_WINDOW_SECONDS = 60


def check_rate_limit(request: Request):
    """Enforce simple rate limiting per client IP."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    timestamps = [t for t in _rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({RATE_LIMIT_MAX_REQUESTS} requests per minute). Try again later."
        )
    timestamps.append(now)
    _rate_limit_store[client_ip] = timestamps


@router.post("", response_model=PredictionOut)
def predict_match(request: PredictRequest, req: Request, db: Session = Depends(get_db)):
    """
    Predict the outcome of a match between two teams.

    Returns probabilities for HOME_WIN / DRAW / AWAY_WIN with SHAP explanations.
    """
    check_rate_limit(req)
    logger.info(f"Prediction request: home={request.home_team_id} away={request.away_team_id}")
    try:
        service = PredictionService(db)
        return service.predict(request.home_team_id, request.away_team_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Prediction failed. See server logs.")


@router.get("/recent")
def get_recent_predictions(db: Session = Depends(get_db)):
    """Get the 10 most recent predictions."""
    from app.repositories.league_repository import PredictionRepository
    repo = PredictionRepository(db)
    predictions = repo.get_recent(limit=10)
    result = []
    for p in predictions:
        result.append({
            "id": p.id,
            "home_team": {"id": p.home_team.id, "name": p.home_team.name},
            "away_team": {"id": p.away_team.id, "name": p.away_team.name},
            "home_win_probability": p.home_win_probability,
            "draw_probability": p.draw_probability,
            "away_win_probability": p.away_win_probability,
            "predicted_result": p.predicted_result,
            "confidence": p.confidence,
            "created_at": p.created_at,
        })
    return result


@router.get("/{prediction_id}", response_model=PredictionOut)
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Get a specific prediction by ID."""
    from app.repositories.league_repository import PredictionRepository
    repo = PredictionRepository(db)
    p = repo.get_by_id(prediction_id)
    if p is None:
        raise HTTPException(status_code=404, detail=f"Prediction {prediction_id} not found")

    explanation = []
    if p.explanation_json:
        try:
            explanation = [ExplanationFactor(**f) for f in json.loads(p.explanation_json)]
        except Exception:
            pass

    return PredictionOut(
        id=p.id,
        home_team=TeamSummary(id=p.home_team.id, name=p.home_team.name, short_name=p.home_team.short_name),
        away_team=TeamSummary(id=p.away_team.id, name=p.away_team.name, short_name=p.away_team.short_name),
        probabilities=ProbabilitiesOut(
            home_win=p.home_win_probability,
            draw=p.draw_probability,
            away_win=p.away_win_probability,
        ),
        predicted_result=p.predicted_result,
        confidence=p.confidence or "MEDIUM",
        model_version=p.model_version.version_tag if p.model_version else None,
        explanation=explanation,
        created_at=p.created_at,
    )
