"""MatchIQ FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.leagues import analytics_router, router as leagues_router
from app.api.matches import router as matches_router
from app.api.predictions import router as predictions_router
from app.api.teams import router as teams_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.ml import model_loader

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    logger.info("MatchIQ API starting up...")
    loaded = model_loader.load_model()
    if loaded:
        logger.info("ML model loaded successfully")
    else:
        logger.warning("ML model not available — predictions will be disabled")
    yield
    logger.info("MatchIQ API shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="MatchIQ API",
        description="Football Match Outcome Prediction & Analytics Platform",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — allow React dev server and production origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health_router)
    app.include_router(teams_router)
    app.include_router(matches_router)
    app.include_router(leagues_router)
    app.include_router(predictions_router)
    app.include_router(analytics_router)

    return app


app = create_app()
