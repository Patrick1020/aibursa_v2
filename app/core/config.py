from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_env: str = Field("dev", alias="APP_ENV")
    app_name: str = Field("AI Stock Predictor v2", alias="APP_NAME")
    sqlalchemy_database_uri: str = Field("sqlite:///./aibursa_v2.db", alias="SQLALCHEMY_DATABASE_URI")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

settings = Settings()
