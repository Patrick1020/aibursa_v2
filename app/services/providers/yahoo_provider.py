from __future__ import annotations
from typing import Iterable, List
from datetime import datetime, timezone
import pandas as pd
import yfinance as yf

from .base import MarketProvider, Quote, Candle

_PERIOD_MAP = {
    "1d":"1d","5d":"5d","1mo":"1mo","3mo":"3mo","6mo":"6mo","1y":"1y","2y":"2y","5y":"5y","10y":"10y","ytd":"ytd","max":"max"
}
_INTERVAL_MAP = {
    "1m":"1m","2m":"2m","5m":"5m","15m":"15m","30m":"30m","60m":"60m","90m":"90m","1h":"1h",
    "1d":"1d","5d":"5d","1wk":"1wk","1mo":"1mo","3mo":"3mo"
}

class YahooProvider(MarketProvider):
    name = "yahoo"

    def get_quotes(self, tickers: Iterable[str]) -> List[Quote]:
        syms = [t.upper() for t in tickers if t]
        if not syms:
            return []

        data = yf.download(
            tickers=" ".join(syms),
            period="1d", interval="1m",
            group_by="ticker", progress=False, prepost=True, threads=True,
            auto_adjust=False,
        )

        quotes: List[Quote] = []
        now = datetime.now(timezone.utc)

        def last_close_from_df(df: pd.DataFrame):
            try:
                s = df["Close"].dropna()
                return float(s.iloc[-1]) if len(s) else None
            except Exception:
                return None

        if isinstance(data, pd.DataFrame) and isinstance(data.columns, pd.MultiIndex):
            # multi-ticker: coloane pe nivelul 0 sunt tickerele
            for t in syms:
                price = last_close_from_df(data[t]) if t in data.columns.levels[0] else None
                quotes.append(Quote(ticker=t, price=price, currency=None, ts=now, provider=self.name))
        else:
            # single-ticker
            price = last_close_from_df(data) if isinstance(data, pd.DataFrame) else None
            quotes.append(Quote(ticker=syms[0], price=price, currency=None, ts=now, provider=self.name))

        return quotes

    def get_history(self, ticker: str, period: str, interval: str) -> List[Candle]:
        period = _PERIOD_MAP.get(period, "1y")
        interval = _INTERVAL_MAP.get(interval, "1d")

        # Încercarea 1: download
        df = yf.download(
            tickers=ticker, period=period, interval=interval,
            progress=False, prepost=True, threads=True, auto_adjust=False,
        )

        # Încercarea 2: Ticker.history (uneori revine când download e gol)
        if df is None or df.empty or df.dropna(how="all").empty:
            df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)

        if df is None or df.empty or df.dropna(how="all").empty:
            raise RuntimeError(f"Yahoo empty history for {ticker} ({period}/{interval})")

        # Păstrăm doar coloanele necesare; toate ca vectori (scalari garantat)
        cols = [c for c in ["Open","High","Low","Close","Volume"] if c in df.columns]
        df = df[cols].dropna()

        # Iterare pe tupluri (nu Series) ca să evităm FutureWarning
        candles: List[Candle] = []
        # asigură ordinea indexului
        df = df.sort_index()
        # extragem ca numpy pentru viteză
        opens  = df["Open"  ].to_numpy(dtype="float64") if "Open"   in df.columns else None
        highs  = df["High"  ].to_numpy(dtype="float64") if "High"   in df.columns else None
        lows   = df["Low"   ].to_numpy(dtype="float64") if "Low"    in df.columns else None
        closes = df["Close" ].to_numpy(dtype="float64") if "Close"  in df.columns else None
        vols   = df["Volume"].to_numpy(dtype="float64") if "Volume" in df.columns else None

        for idx_i, ts in enumerate(df.index):
            # ts poate fi tz-naive; normalizăm la UTC
            if isinstance(ts, pd.Timestamp):
                if ts.tzinfo is None:
                    dt = ts.tz_localize("UTC").to_pydatetime()
                else:
                    dt = ts.tz_convert("UTC").to_pydatetime()
            else:
                dt = datetime.fromtimestamp(int(pd.Timestamp(ts).timestamp()), tz=timezone.utc)

            o = opens[idx_i]  if opens  is not None else float("nan")
            h = highs[idx_i]  if highs  is not None else float("nan")
            l = lows[idx_i]   if lows   is not None else float("nan")
            c = closes[idx_i] if closes is not None else float("nan")
            v = vols[idx_i]   if vols   is not None else 0.0

            candles.append(Candle(date=dt, open=float(o), high=float(h), low=float(l), close=float(c), volume=float(v)))

        return candles
