from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class PredictionIn(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=16)
    horizon_days: int = Field(ge=1, le=90, default=7)

class PredictionOut(BaseModel):
    id: int
    ticker: str
    horizon_days: int
    expected_change_pct: float
    probability_pct: float
    outcome: str
    reward_to_risk: float
    rationale: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
