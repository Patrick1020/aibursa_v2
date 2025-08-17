from __future__ import annotations
import numpy as np
import pandas as pd

def synth_candles(n: int = 600, seed: int = 7):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    # trend + sezonal + random walk
    trend = 0.0006 * t
    season = 0.02 * np.sin(2*np.pi*t/90) + 0.01 * np.sin(2*np.pi*t/30)
    walk = rng.normal(0, 0.01, size=n).cumsum()
    price = 100 * (1 + trend + season + 0.001*walk)
    vol = np.clip(rng.normal(1e6, 2e5, size=n), 2e5, None)
    df = pd.DataFrame({
        "date": pd.date_range("2018-01-01", periods=n, freq="B"),
        "close": price,
    })
    df["open"] = df["close"].shift(1).fillna(df["close"])
    df["high"] = df[["open","close"]].max(axis=1) * (1 + rng.normal(0.0015, 0.002, size=n))
    df["low"]  = df[["open","close"]].min(axis=1) * (1 - rng.normal(0.0015, 0.002, size=n))
    df["volume"] = vol
    return df[["date","open","high","low","close","volume"]]
