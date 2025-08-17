from __future__ import annotations
from typing import Iterable, List, Dict
from dataclasses import asdict
from fastapi import HTTPException
from app.core.config import settings
from .cache import TTLCache
from .providers.base import Quote, Candle, MarketProvider
from .providers.yahoo_provider import YahooProvider
from .providers.alpha_vantage_provider import AlphaVantageProvider

_quote_cache = TTLCache(ttl_seconds=settings.market_cache_ttl_seconds, maxsize=4096)

def _build_providers() -> List[MarketProvider]:
    order = [s.strip() for s in (settings.market_provider_order or "").split(",") if s.strip()]
    providers: List[MarketProvider] = []
    for name in order:
        if name == "yahoo":
            providers.append(YahooProvider())
        elif name == "alpha_vantage":
            if settings.alpha_vantage_api_key:
                providers.append(AlphaVantageProvider(settings.alpha_vantage_api_key))
    if not providers:
        providers.append(YahooProvider())
    return providers

_PROVIDERS = _build_providers()

def get_quotes(tickers: Iterable[str]) -> Dict[str, float | None]:
    # cache per „tickers order” pentru simplitate
    key = "quotes:" + ",".join(sorted({t.upper() for t in tickers}))
    cached = _quote_cache.get(key)
    if cached is not None:
        return cached
    last_err: Exception | None = None
    for p in _PROVIDERS:
        try:
            quotes = p.get_quotes(tickers)
            result = {q.ticker: q.price for q in quotes}
            # ținem și `None` ca să nu mai încercăm în buclă timp de TTL
            _quote_cache.set(key, result)
            return result
        except Exception as e:
            last_err = e
            continue
    raise HTTPException(status_code=502, detail=f"Eroare quotes: {last_err}")

def get_history(ticker: str, period: str, interval: str) -> List[Dict]:
    last_err: Exception | None = None
    for p in _PROVIDERS:
        try:
            candles = p.get_history(ticker, period, interval)
            return [ {
                "date": c.date.isoformat(),
                "open": c.open, "high": c.high, "low": c.low, "close": c.close, "volume": c.volume
            } for c in candles ]
        except Exception as e:
            last_err = e
            continue
    raise HTTPException(status_code=502, detail=f"Eroare history: {last_err}")
