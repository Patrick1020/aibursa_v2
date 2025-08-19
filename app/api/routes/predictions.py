from fastapi import APIRouter, Depends, HTTPException
from fastapi import Path, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.market_data import get_history, get_quotes
from app.services.ml_integration import ensure_model_and_predict
from app.db.session import SessionLocal
from app.models.prediction import StockPrediction
from app.schemas.prediction import PredictionIn, PredictionOut
from app.services.prediction_engine import PredictionEngine

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

class CandleOut(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class PredictionRowOut(BaseModel):
    id: int
    ticker: str
    horizon_days: int
    probability_pct: float
    expected_change_pct: float
    reward_to_risk: float
    outcome: Optional[str] = None
    rationale: Optional[str] = None
    created_at: str

class PredictionDetailsResponse(BaseModel):
    ticker: str
    last_price: Optional[float] = None
    period: str = Field(..., description="ex: 3mo, 6mo, 1y, 2y, 5y, max")
    interval: str = Field(..., description="ex: 1d, 1h, 30m, 15m, 5m, 1m")
    prediction: Optional[PredictionRowOut] = None
    previous: List[PredictionRowOut] = []
    candles: List[CandleOut] = []



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

engine = PredictionEngine()

@router.post("", response_model=PredictionOut)
def create_prediction(payload: PredictionIn, db: Session = Depends(get_db)):
    # Normalizăm input-ul
    ticker = payload.ticker.upper()
    horizon_days = payload.horizon_days

    # === Predict din date reale + model ML (auto-train dacă lipsesc artefactele) ===
    try:
        ml = ensure_model_and_predict(ticker, horizon_days)
        probability_pct = ml["probability_pct"]
        expected_change_pct = ml["expected_change_pct"]
        reward_to_risk = ml["reward_to_risk"]
    except Exception as e:
        # 502: problemă la provider/ML, nu la client
        raise HTTPException(status_code=502, detail=f"Predict ML a eșuat: {e}")

    # Outcome pentru predicție „nouă”: o ținem neutră (UI-ul o afișează ca Breakeven)
    outcome = "breakeven"

    # (opțional) un motiv scurt/explicativ pentru audit/UX
    rationale = f"ML(v1): prob={probability_pct}%, exp={expected_change_pct}%, rr={reward_to_risk}"

    obj = StockPrediction(
        ticker=ticker,
        horizon_days=horizon_days,
        expected_change_pct=expected_change_pct,
        probability_pct=probability_pct,
        outcome=outcome,
        reward_to_risk=reward_to_risk,
        rationale=rationale,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/{ticker}", response_model=PredictionDetailsResponse)
def prediction_details(
    ticker: str = Path(..., description="Symbol, ex: AAPL"),
    period: str = Query("3mo"),
    interval: str = Query("1d"),
    limit: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db),
):
    t = ticker.upper()

    # 1) Predicții din DB: ultima + câteva anterioare
    #    (presupunem modelul SQLAlchemy: StockPrediction cu coloane folosite în UI)
    q = db.query(StockPrediction).filter(StockPrediction.ticker == t).order_by(StockPrediction.created_at.desc())
    latest = q.first()
    prev = q.offset(1).limit(limit).all()

    def row_to_out(r: StockPrediction) -> PredictionRowOut:
        return PredictionRowOut(
            id=int(r.id),
            ticker=r.ticker,
            horizon_days=int(r.horizon_days),
            probability_pct=float(r.probability_pct),
            expected_change_pct=float(r.expected_change_pct),
            reward_to_risk=float(r.reward_to_risk),
            outcome=getattr(r, "outcome", None),
            rationale=getattr(r, "rationale", None),
            created_at=r.created_at.isoformat() if getattr(r, "created_at", None) else "",
        )

    latest_out = row_to_out(latest) if latest else None
    previous_out = [row_to_out(r) for r in prev]

    # 2) Istoric de piață (period/interval din query)
    try:
        candles_js = get_history(t, period, interval)  # list[dict]
    except Exception as e:
        # dacă providerii dau rate-limit/eroare, continuăm totuși cu secțiunea de predicții
        candles_js = []
    candles_out = [CandleOut(**c) for c in candles_js]

    # 3) Ultimul preț live (pentru header)
    try:
        qp = get_quotes([t])  # dict: {ticker: price}
        last_price = qp.get(t)
    except Exception:
        last_price = None

    return {
        "ticker": t,
        "last_price": last_price,
        "period": period,
        "interval": interval,
        "prediction": latest_out,
        "previous": previous_out,
        "candles": candles_out,
    }


@router.get("", response_model=List[PredictionOut])
def list_predictions(db: Session = Depends(get_db), limit: int = 100):
    return db.query(StockPrediction).order_by(StockPrediction.created_at.desc()).limit(limit).all()
