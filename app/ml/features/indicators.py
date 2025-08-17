from __future__ import annotations
import numpy as np
import pandas as pd

def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    rs = _ema(up, period) / _ema(down, period)
    return 100 - (100 / (1 + rs))

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expects columns: ['date','open','high','low','close','volume'] with ascending date.
    Returns df with extra feature columns, NaNs dropped.
    """
    df = df.copy()
    df["sma_5"] = df["close"].rolling(5).mean()
    df["sma_20"] = df["close"].rolling(20).mean()
    df["ema_12"] = _ema(df["close"], 12)
    df["ema_26"] = _ema(df["close"], 26)
    df["rsi_14"] = rsi(df["close"], 14)
    df["atr_14"] = atr(df["high"], df["low"], df["close"], 14)
    df["ret_1d"] = df["close"].pct_change(1) * 100.0
    df["ret_5d"] = df["close"].pct_change(5) * 100.0
    df["vol_norm"] = (df["volume"] / (df["volume"].rolling(20).mean()+1e-9)).clip(upper=10.0)

    # gaps și poziții vs medii
    df["gap"] = (df["open"] - df["close"].shift(1)) / (df["close"].shift(1)+1e-9) * 100.0
    df["dist_sma20"] = (df["close"] - df["sma_20"]) / (df["sma_20"] + 1e-9) * 100.0
    df["dist_ema26"] = (df["close"] - df["ema_26"]) / (df["ema_26"] + 1e-9) * 100.0

    # cleanup
    df = df.dropna().reset_index(drop=True)
    return df
