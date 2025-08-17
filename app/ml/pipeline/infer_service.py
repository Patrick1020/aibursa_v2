from __future__ import annotations
import os, json
from typing import Dict, Any
import numpy as np
import pandas as pd
from joblib import load
from app.ml.features.indicators import add_indicators

ART_DIR = "app/ml/artifacts"

def _tag(ticker: str, horizon_days: int) -> str:
    return f"{ticker.upper()}_{horizon_days}d"

def _load_models(ticker: str, horizon_days: int):
    tag = _tag(ticker, horizon_days)
    cls = load(os.path.join(ART_DIR, f"cls_{tag}.joblib"))
    reg = load(os.path.join(ART_DIR, f"reg_{tag}.joblib"))
    return cls, reg

def predict_from_candles(ticker: str, horizon_days: int, candles: pd.DataFrame) -> Dict[str, Any]:
    """
    candles columns: ['date','open','high','low','close','volume'] ascending by date
    """
    if candles is None or len(candles) < 40:
        raise ValueError("Not enough candles (min 40).")

    cls, reg = _load_models(ticker, horizon_days)
    feat = add_indicators(candles).tail(1)  # last row
    X = feat.drop(columns=["date","open","high","low","close","volume"], errors="ignore").values
    proba = float(cls.predict_proba(X)[:,1][0])   # P(up)
    exp_change = float(reg.predict(X)[0])         # % change over horizon

    # Simplă estimare R:R din distribuția regresiei (proxy): raport față de ATR
    atr = float(feat["atr_14"].iloc[0])
    price = float(feat["close"].iloc[0])
    rr = float(max(0.1, abs(exp_change)) / (atr/price*100 + 1e-6))  # ad-hoc, îl rafinăm ulterior

    return {
        "ticker": ticker.upper(),
        "horizon_days": horizon_days,
        "probability_pct": round(proba * 100, 2),
        "expected_change_pct": round(exp_change, 2),
        "reward_to_risk": round(rr, 2),
    }
