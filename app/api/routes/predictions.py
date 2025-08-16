from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.prediction import StockPrediction
from app.schemas.prediction import PredictionIn, PredictionOut
from app.services.prediction_engine import PredictionEngine
from typing import List

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

engine = PredictionEngine()

@router.post("", response_model=PredictionOut)
def create_prediction(payload: PredictionIn, db: Session = Depends(get_db)):
    res = engine.predict(payload.ticker, payload.horizon_days)
    obj = StockPrediction(
        ticker=payload.ticker.upper(),
        horizon_days=payload.horizon_days,
        expected_change_pct=res.expected_change_pct,
        probability_pct=res.probability_pct,
        outcome=res.outcome,
        reward_to_risk=res.reward_to_risk,
        rationale=res.rationale,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("", response_model=List[PredictionOut])
def list_predictions(db: Session = Depends(get_db), limit: int = 100):
    return db.query(StockPrediction).order_by(StockPrediction.created_at.desc()).limit(limit).all()
