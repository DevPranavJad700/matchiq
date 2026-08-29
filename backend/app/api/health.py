"""Health check, model info, and dataset provenance endpoints."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.ml import model_loader
from app.schemas.schemas import HealthOut, ModelInfoOut, ProvenanceOut

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthOut)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return HealthOut(
        status="ok" if db_ok else "degraded",
        version=settings.APP_VERSION,
        db_connected=db_ok,
        model_loaded=model_loader.is_model_loaded(),
        data_mode=settings.DATA_MODE,
    )


@router.get("/model/info", response_model=ModelInfoOut)
def get_model_info():
    """Get information about the currently loaded ML model."""
    meta = model_loader.get_model_metadata()
    if not meta:
        raise HTTPException(status_code=503, detail="Model not loaded")

    from datetime import datetime
    training_date = None
    if td := meta.get("training_date"):
        try:
            training_date = datetime.fromisoformat(td)
        except Exception:
            pass

    return ModelInfoOut(
        name=meta.get("name", "MatchIQ Model"),
        version_tag=meta.get("version_tag", "unknown"),
        algorithm=meta.get("algorithm", "unknown"),
        training_date=training_date,
        accuracy=meta.get("accuracy"),
        f1_score=meta.get("f1_score"),
        log_loss=meta.get("log_loss"),
        features=model_loader.get_feature_names(),
        is_active=True,
    )


@router.get("/system/provenance", response_model=ProvenanceOut)
@router.get("/health/provenance", response_model=ProvenanceOut)
def get_dataset_provenance():
    """Get verified dataset provenance and SHA-256 integrity information."""
    prov_path = Path(settings.PROVENANCE_PATH)
    if not prov_path.is_absolute():
        # Resolve relative to project root or workspace
        prov_path = Path(__file__).parent.parent.parent.parent / settings.PROVENANCE_PATH

    if not prov_path.exists():
        raise HTTPException(status_code=404, detail="Dataset provenance manifest not found")

    try:
        with open(prov_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read provenance: {e}")
