from __future__ import annotations
from typing import List, Dict
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from app.services.market_data import get_quotes, get_history

router = APIRouter(prefix="/api/market", tags=["market"])

class QuotesResponse(BaseModel):
    quotes: List[Dict[str, float | None]]

@router.get("/quotes", response_model=QuotesResponse)
def quotes(tickers: str = Query(..., description="Comma-separated symbols, ex: AAPL,MSFT,TSLA")):
    syms = [s.strip().upper() for s in tickers.split(",") if s.strip()]
    data = get_quotes(syms)
    # returnăm fix forma așteptată de UI: {quotes:[{ticker, price}]}
    return {"quotes": [{"ticker": k, "price": v} for k, v in data.items()]}

class HistoryResponse(BaseModel):
    ticker: str
    period: str = Field(..., description="ex: 1mo, 3mo, 6mo, 1y, 2y, 5y, max")
    interval: str = Field(..., description="ex: 1d, 1h, 30m, 15m, 5m, 1m")
    candles: List[Dict]

@router.get("/history", response_model=HistoryResponse)
def history(
    ticker: str = Query(..., description="Symbol, ex: AAPL"),
    period: str = Query("1y"),
    interval: str = Query("1d"),
):
    return {"ticker": ticker.upper(), "period": period, "interval": interval, "candles": get_history(ticker, period, interval)}
