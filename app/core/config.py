from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    app_name: str = "AI Stock Predictor v2"
    debug: bool = False

    # Market providers
    alpha_vantage_api_key: str | None = None
    market_provider_order: str = "yahoo,alpha_vantage"
    market_cache_ttl_seconds: int = 5

    # Database
    database_url: str = "sqlite:///./data/app.db"

    # CORS
    cors_origins: str | None = None  # ex: "http://127.0.0.1:8000,http://localhost:8000"

    # Security
    secret_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

settings = Settings()
