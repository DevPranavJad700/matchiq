"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://matchiq:matchiq@localhost:5432/matchiq"

    # Application
    APP_NAME: str = "MatchIQ"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ML
    MODEL_DIR: str = "ml/models"
    MODEL_FILENAME: str = "best_model.joblib"
    FEATURE_META_FILENAME: str = "feature_metadata.json"

    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
