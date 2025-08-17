from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import pandas as pd

from app.ml.pipeline.train_baseline import TrainConfig, train_on_dataframe
from app.ml.pipeline.infer_service import predict_from_candles
from app.ml.data.synth import synth_candles

router = APIRouter(prefix="/api/ml", tags=["ml"])

class TrainRequest(BaseModel):
    ticker: str = Field(..., example="AAPL")
    horizon_days: int = Field(7, ge=2, le=30)
    use_synth: bool = Field(True, description="Folosește date sintetice demo până conectăm providerul real.")

@router.post("/train")
def train(req: TrainRequest):
    # TODO: înlocuiește synth_candles cu provider real (Yahoo/AlphaVantage)
    df = synth_candles(n=900, seed=11)
    metrics = train_on_dataframe(df, TrainConfig(ticker=req.ticker, horizon_days=req.horizon_days))
    return {"ok": True, "metrics": metrics}

class PredictRequest(BaseModel):
    ticker: str
    horizon_days: int = Field(7, ge=2, le=30)

@router.post("/predict")
def predict(req: PredictRequest):
    # pentru demo folosim ultimele N lumânări sintetice; în producție: ultimele lumânări din provider.
    df = synth_candles(n=1200, seed=13)
    try:
        out = predict_from_candles(req.ticker, req.horizon_days, df)
        return {"ok": True, "prediction": out}
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="Modelul nu există. Rulează /api/ml/train mai întâi.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
