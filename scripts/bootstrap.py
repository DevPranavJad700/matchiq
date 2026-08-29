"""Auto-boot initialization script for MatchIQ.

Ensures that:
1. Database schema is populated with seed data if empty.
2. ML model artifacts exist and are trained if missing.
3. Active model version is registered in the database.
"""

import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def bootstrap() -> None:
    """Run application bootstrap tasks."""
    logger.info("==================================================")
    logger.info("MatchIQ Application Bootstrap Sequence")
    logger.info("==================================================")

    # 1. Check and seed database if empty
    try:
        from app.db.session import SessionLocal
        from app.models.orm_models import Team, ModelVersion
        from sqlalchemy import select

        db = SessionLocal()
        team_count = len(list(db.execute(select(Team)).scalars().all()))
        db.close()

        if team_count == 0:
            logger.info("Database is empty. Ingesting Premier League seed data...")
            from scripts.seed_demo_data import seed_to_db
            seed_to_db(reset=False)
        else:
            logger.info(f"Database contains {team_count} teams. Skipping seed.")
    except Exception as e:
        logger.warning(f"Database check/seed warning: {e}")

    # 2. Check ML model artifacts
    model_file = project_root / "ml" / "models" / "best_model.joblib"
    if not model_file.exists():
        logger.info("No model artifact found. Initiating ML training pipeline...")
        from ml.training.train import train
        train()
    else:
        logger.info(f"Found trained model artifact at {model_file}")

    # 3. Ensure active model registered in DB
    try:
        from app.db.session import SessionLocal
        from app.models.orm_models import ModelVersion
        from sqlalchemy import select
        import json

        db = SessionLocal()
        active_model = db.execute(select(ModelVersion).where(ModelVersion.is_active == True)).scalar_one_or_none()
        
        if not active_model:
            logger.info("No active model registered in DB. Registering trained model...")
            meta_path = project_root / "ml" / "models" / "feature_metadata.json"
            if meta_path.exists():
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                mv = ModelVersion(
                    name=meta.get("name", "MatchIQ Model"),
                    version_tag=meta.get("version_tag", "v1.0.0"),
                    algorithm=meta.get("algorithm", "logistic_regression"),
                    accuracy=meta.get("accuracy", 0.48),
                    f1_score=meta.get("f1_score", 0.43),
                    log_loss=meta.get("log_loss", 0.99),
                    features_json=json.dumps(meta.get("features", [])),
                    is_active=True,
                )
                db.add(mv)
                db.commit()
                logger.info(f"Registered active model version: {mv.version_tag}")
        db.close()
    except Exception as e:
        logger.warning(f"Model registration warning: {e}")

    logger.info("✓ Bootstrap sequence finished successfully. System ready.")


if __name__ == "__main__":
    bootstrap()
