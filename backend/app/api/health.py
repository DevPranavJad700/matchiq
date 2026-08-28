"""Health check and model info endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.ml import model_loader
from app.schemas.schemas import HealthOut, ModelInfoOut

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
    )


@router.get("/model/info", response_model=ModelInfoOut)
def get_model_info():
    """Get information about the currently loaded ML model."""
    meta = model_loader.get_model_metadata()
    if not meta:
        from fastapi import HTTPException
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
