from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    
        # ----- Universe -----
    universe_fixed: str = "AAPL,MSFT,GOOGL,AMZN,META,TSLA,NVDA,AVGO,AMD,COST,PEP,KO,JNJ,XOM,PG,HD,UNH,LLY,ABBV,ORCL,CRM,ADBE,INTC,CSCO,TXN,QCOM,NFLX,AMAT,LIN,V,PYPL,MA,WMT,TMO,NKE,PFE,MCD,UPS,BAC,JPM,C,MS,GS,BLK,SPGI,BRK.B,UNP,CAT,DE,BA,GE,IBM,SBUX,LOW,T,TMUS,VZ,PLTR,SNOW,SHOP,UBER,ABNB,INTU,ADP,ISRG,MDT,VRTX,NOW,ASML,TSM,NVO,AZN,RIVN,F,GM,LCID,BYDDF,NIO,BABA,JD,PDD,TCEHY,TWTR,DIS,NKE,EA,ATVI,TTWO,ROKU,SPOT,SNAP,PINS,ETSY,CRWD,ZS,NET,PANW,OKTA,DDOG,MDB"
    universe_random_pool_path: str = "data/etoro_universe.csv"
    universe_random_daily_count: int = 100
    universe_random_seed: int | None = None
    
    
    @field_validator("universe_random_seed", mode="before")
    @classmethod
    def _seed_empty_ok(cls, v):
        # Acceptă '', ' ', 'None', 'null' ca „necompletat”
        if v is None: 
            return None
        if isinstance(v, str) and v.strip().lower() in ("", "none", "null"):
            return None
        # dacă e deja int sau string numeric, îl întoarcem ca int
        try:
            return int(v)
        except (TypeError, ValueError):
            raise ValueError("UNIVERSE_RANDOM_SEED trebuie să fie întreg sau gol")


    
    # Logging
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Database
    database_url: str = "sqlite:///./data/app.db"

    @property
    def sqlalchemy_database_uri(self) -> str:
        # Alias compatibil cu codul vechi
        return self.database_url

    # App
    app_name: str = "AI Stock Predictor v2"
    debug: bool = False

    # Market providers
    alpha_vantage_api_key: str | None = None
    market_provider_order: str = "yahoo,alpha_vantage"
    market_cache_ttl_seconds: int = 5

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
