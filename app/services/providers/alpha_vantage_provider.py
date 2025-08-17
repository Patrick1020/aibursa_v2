from __future__ import annotations
from typing import Iterable, List, Dict
from datetime import datetime, timezone
import os, httpx
from .base import MarketProvider, Quote, Candle

_BASE_URL = "https://www.alphavantage.co/query"

class AlphaVantageProvider(MarketProvider):
    name = "alpha_vantage"

    def __init__(self, api_key: str | None):
        if not api_key:
            raise ValueError("Alpha Vantage API key missing")
        self.api_key = api_key

    def _get(self, params: Dict[str,str]) -> Dict:
        p = dict(params)
        p["apikey"] = self.api_key
        r = httpx.get(_BASE_URL, params=p, timeout=30)
        r.raise_for_status()
        j = r.json()
        # Alpha Vantage semnalează throttling prin "Note"
        if "Note" in j:
            raise RuntimeError("Alpha Vantage rate limit: " + j["Note"][:120])
        if "Error Message" in j:
            raise RuntimeError(j["Error Message"])
        return j

    def get_quotes(self, tickers: Iterable[str]) -> List[Quote]:
        quotes: List[Quote] = []
        for t in set([t.upper() for t in tickers]):
            j = self._get({"function":"GLOBAL_QUOTE","symbol":t})
            q = j.get("Global Quote", {})
            price = q.get("05. price")
            price_f = float(price) if price is not None else None
            quotes.append(Quote(ticker=t, price=price_f, currency=None, ts=datetime.now(timezone.utc), provider=self.name))
        return quotes

    def get_history(self, ticker: str, period: str, interval: str) -> List[Candle]:
        # Daily sau intraday, în funcție de interval
        if interval in ("1m","5m","15m","30m","60m"):
            j = self._get({"function":"TIME_SERIES_INTRADAY","symbol":ticker,"interval":interval,"outputsize":"full"})
            key = next((k for k in j.keys() if "Time Series" in k), None)
            series = j.get(key, {})
            items = sorted(series.items(), key=lambda kv: kv[0])
        else:
            j = self._get({"function":"TIME_SERIES_DAILY_ADJUSTED","symbol":ticker,"outputsize":"full"})
            series = j.get("Time Series (Daily)", {})
            items = sorted(series.items(), key=lambda kv: kv[0])
        candles: List[Candle] = []
        for s, row in items:
            # s e un string timestamp; îl considerăm UTC
            try:
                dt = datetime.fromisoformat(s.replace(" ", "T")).replace(tzinfo=timezone.utc)
            except Exception:
                dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            candles.append(Candle(
                date=dt,
                open=float(row.get("1. open") or row.get("1. Open") or row.get("open")),
                high=float(row.get("2. high") or row.get("2. High") or row.get("high")),
                low=float(row.get("3. low") or row.get("3. Low") or row.get("low")),
                close=float(row.get("4. close") or row.get("4. Close") or row.get("close")),
                volume=float(row.get("6. volume") or row.get("5. volume") or row.get("volume") or 0),
            ))
        return candles
