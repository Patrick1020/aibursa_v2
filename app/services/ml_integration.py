from __future__ import annotations
from typing import Dict, Any, Tuple
import pandas as pd

from app.services.market_data import get_history
from app.ml.pipeline.train_baseline import TrainConfig, train_on_dataframe
from app.ml.pipeline.infer_service import predict_from_candles

def _history_df(ticker: str, period: str, interval: str) -> pd.DataFrame:
    js = get_history(ticker, period, interval)  # list[dict]
    if not js:
        raise RuntimeError(f"Fără istoric pentru {ticker} ({period}/{interval}).")
    df = pd.DataFrame(js)
    # normalizăm coloanele
    df["date"] = pd.to_datetime(df["date"])
    df = df[["date","open","high","low","close","volume"]].sort_values("date").reset_index(drop=True)
    return df

def ensure_model_and_predict(ticker: str, horizon_days: int = 7) -> Dict[str, Any]:
    """
    1) încearcă să prezică cu modelul existent (dacă e antrenat);
    2) dacă lipsesc artefactele, antrenează rapid pe istoric real, apoi prezice.
    """
    ticker = ticker.upper()

    # Pas 1: avem destule date? (încercăm 5 ani daily; dacă nu, 1 an)
    try:
        df = _history_df(ticker, period="5y", interval="1d")
    except Exception:
        df = _history_df(ticker, period="1y", interval="1d")

    # Pas 2: încearcă direct să prezici (dacă modelul există)
    try:
        pred = predict_from_candles(ticker, horizon_days, df)
        return pred
    except FileNotFoundError:
        # artefactele lipsesc -> antrenăm rapid, apoi prezicem
        cfg = TrainConfig(ticker=ticker, horizon_days=horizon_days)
        train_on_dataframe(df, cfg)
        pred = predict_from_candles(ticker, horizon_days, df)
        return pred
