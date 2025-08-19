from __future__ import annotations

"""
Alpha Vantage provider (enterprise-grade)
- Shared HTTPX client with timeouts
- Retry with exponential backoff on rate-limit / transient errors
- Proper interval mapping (our canonical -> AV)
- Raise on empty series so orchestrator can fallback
"""

from typing import Iterable, List, Dict, Optional
from datetime import datetime, timezone
import time
import httpx

from .base import MarketProvider, Quote, Candle


_BASE_URL = "https://www.alphavantage.co/query"
_INTRADAY_MAP = {  # our canonical -> AV expected
    "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min", "60m": "60min", "1h": "60min"
}
# AV only supports above granularities for intraday; daily/adjusted for others.

class AlphaVantageProvider(MarketProvider):
    name = "alpha_vantage"

    def __init__(self, api_key: Optional[str]):
        if not api_key:
            raise ValueError("Alpha Vantage API key missing")
        self.api_key = api_key
        self._client = httpx.Client(timeout=httpx.Timeout(20.0, read=30.0))

    # --------------- low-level ---------------

    def _get(self, params: Dict[str, str]) -> Dict:
        p = dict(params)
        p["apikey"] = self.api_key

        # Basic retry for transient errors / throttling
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                r = self._client.get(_BASE_URL, params=p)
                r.raise_for_status()
                j = r.json()
                if "Note" in j:
                    # rate limit -> retry with backoff
                    raise RuntimeError("rate_limit: " + j["Note"][:200])
                if "Error Message" in j:
                    # permanent error for this symbol/request
                    raise RuntimeError(j["Error Message"])
                return j
            except Exception as e:
                last_err = e
                # small backoff; last attempt will bubble up
                time.sleep(0.6 * (attempt + 1))
        raise RuntimeError(f"AlphaVantage request failed: {last_err}")

    # --------------- quotes ---------------

    def get_quotes(self, tickers: Iterable[str]) -> List[Quote]:
        quotes: List[Quote] = []
        now = datetime.now(timezone.utc)
        for t in sorted(set([t.upper() for t in tickers if t])):
            j = self._get({"function": "GLOBAL_QUOTE", "symbol": t})
            q = (j or {}).get("Global Quote", {}) or {}
            price = q.get("05. price")
            try:
                price_f = float(price) if price is not None else None
            except Exception:
                price_f = None
            quotes.append(Quote(ticker=t, price=price_f, currency=None, ts=now, provider=self.name))
        return quotes

    # --------------- history ---------------

    def get_history(self, ticker: str, period: str, interval: str) -> List[Candle]:
        """
        Return candles in ascending time order. Raises on empty series.
        'period' is not enforced server-side for AV; we return full series
        and let the orchestrator trim if needed.
        """
        ticker = ticker.upper()

        # Intraday?
        if interval in _INTRADAY_MAP:
            av_interval = _INTRADAY_MAP[interval]
            j = self._get({
                "function": "TIME_SERIES_INTRADAY",
                "symbol": ticker,
                "interval": av_interval,
                "outputsize": "full",
                "datatype": "json",
            })
            key = next((k for k in j.keys() if "Time Series" in k and "Intraday" in k), None)
            series = (j.get(key) or {}) if key else {}
            items = sorted(series.items(), key=lambda kv: kv[0])
            candles = self._items_to_candles_intraday(items)
        else:
            # Daily adjusted
            j = self._get({
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": ticker,
                "outputsize": "full",
                "datatype": "json",
            })
            series = j.get("Time Series (Daily)", {}) or {}
            items = sorted(series.items(), key=lambda kv: kv[0])
            candles = self._items_to_candles_daily(items)

        if not candles:
            raise RuntimeError(f"Alpha Vantage empty history for {ticker} (interval={interval})")

        return candles

    # --------------- helpers ---------------

    @staticmethod
    def _items_to_candles_intraday(items: List) -> List[Candle]:
        out: List[Candle] = []
        for s, row in items:
            # s like "2025-08-19 14:55:00"
            try:
                dt = datetime.fromisoformat(s.replace(" ", "T")).replace(tzinfo=timezone.utc)
            except Exception:
                # fallback naive parse
                dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            out.append(Candle(
                date=dt,
                open=float(row.get("1. open") or row.get("open") or 0.0),
                high=float(row.get("2. high") or row.get("high") or 0.0),
                low=float(row.get("3. low") or row.get("low") or 0.0),
                close=float(row.get("4. close") or row.get("close") or 0.0),
                volume=float(row.get("5. volume") or row.get("volume") or 0.0),
            ))
        return out

    @staticmethod
    def _items_to_candles_daily(items: List) -> List[Candle]:
        out: List[Candle] = []
        for s, row in items:
            # s like "2025-08-19"
            try:
                dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
            except Exception:
                dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            out.append(Candle(
                date=dt,
                open=float(row.get("1. open") or row.get("1. Open") or row.get("open") or 0.0),
                high=float(row.get("2. high") or row.get("2. High") or row.get("high") or 0.0),
                low=float(row.get("3. low") or row.get("3. Low") or row.get("low") or 0.0),
                close=float(row.get("4. close") or row.get("4. Close") or row.get("close") or 0.0),
                volume=float(row.get("6. volume") or row.get("5. volume") or row.get("volume") or 0.0),
            ))
        return out
