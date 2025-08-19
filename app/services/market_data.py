from __future__ import annotations

"""
Market data orchestrator (enterprise-grade)
- Provider registry driven by settings (order + availability)
- Robust fallback on errors AND empty series
- Canonical period/interval normalization
- TTL cache for quotes
- Structured logging & consistent HTTP errors
"""

from typing import Iterable, List, Dict, Tuple
from dataclasses import asdict
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import logger

from .cache import TTLCache
from .providers.base import Quote, Candle, MarketProvider
from .providers.yahoo_provider import YahooProvider
from .providers.alpha_vantage_provider import AlphaVantageProvider


# ---------------------------
# Canonical period/interval
# ---------------------------

_ALLOWED_PERIODS = {
    "1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"
}
_ALLOWED_INTERVALS = {
    "1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo","3mo"
}

def _normalize_period_interval(period: str, interval: str) -> Tuple[str, str]:
    p = (period or "1y").lower().strip()
    i = (interval or "1d").lower().strip()
    # Normalize common aliases
    if i == "1min": i = "1m"
    if i == "5min": i = "5m"
    if i == "15min": i = "15m"
    if i == "30min": i = "30m"
    if i == "60min": i = "60m"
    if i == "1hour": i = "1h"
    if p not in _ALLOWED_PERIODS: p = "1y"
    if i not in _ALLOWED_INTERVALS: i = "1d"
    return p, i


# ---------------------------
# Providers registry
# ---------------------------

def _build_providers() -> List[MarketProvider]:
    """
    Instantiate providers in the order declared in settings.MARKET_PROVIDER_ORDER.
    Unknown names are ignored. AlphaVantage is added only if API key is present.
    Fallback to Yahoo if list ends up empty.
    """
    order = [s.strip().lower() for s in (settings.market_provider_order or "").split(",") if s.strip()]
    providers: List[MarketProvider] = []
    for name in order:
        if name == "yahoo":
            providers.append(YahooProvider())
        elif name in ("alpha_vantage", "alphavantage", "av"):
            if settings.alpha_vantage_api_key:
                providers.append(AlphaVantageProvider(settings.alpha_vantage_api_key))
            else:
                logger.warning("AlphaVantage in provider order but API key is missing; skipping.")
        else:
            logger.warning("Unknown market provider in order: %s (skipped)", name)

    if not providers:
        logger.warning("No providers configured — falling back to YahooProvider only.")
        providers.append(YahooProvider())

    names = [getattr(p, "name", p.__class__.__name__) for p in providers]
    logger.info("Market providers initialized (order): %s", names)
    return providers

_PROVIDERS: List[MarketProvider] = _build_providers()


# ---------------------------
# Caching for quotes
# ---------------------------

_quote_cache = TTLCache(ttl_seconds=settings.market_cache_ttl_seconds, maxsize=4096)


# ---------------------------
# Public API
# ---------------------------

def get_quotes(tickers: Iterable[str]) -> Dict[str, float | None]:
    """
    Return last prices for the given tickers. Uses TTL cache and tries providers in order.
    Keeps None values (so we don't hammer providers during TTL).
    """
    uniq = sorted({t.strip().upper() for t in tickers if t and t.strip()})
    if not uniq:
        return {}

    key = "quotes:" + ",".join(uniq)
    cached = _quote_cache.get(key)
    if cached is not None:
        return cached

    last_err: Exception | None = None
    for p in _PROVIDERS:
        try:
            quotes = p.get_quotes(uniq)
            result = {q.ticker: q.price for q in quotes}
            # Cache even None to avoid loops for symbols unavailable at the provider
            _quote_cache.set(key, result)
            logger.debug("Quotes from %s for %s", p.name, uniq)
            return result
        except Exception as e:
            last_err = e
            logger.warning("get_quotes failed on provider '%s': %s", p.name, e)
            continue

    # No provider succeeded
    msg = f"Eroare quotes (all providers): {last_err}"
    logger.error(msg)
    raise HTTPException(status_code=502, detail=msg)


def get_history(ticker: str, period: str, interval: str) -> List[Dict]:
    """
    Return OHLCV as list[dict] with ISO dates; tries providers in order.
    If a provider returns an empty series, it's treated as failure and we try the next.
    We also attempt a second try per provider with a broader period when possible.
    """
    t = (ticker or "").strip().upper()
    if not t:
        raise HTTPException(status_code=400, detail="ticker missing")

    p_norm, i_norm = _normalize_period_interval(period, interval)
    last_err: Exception | None = None

    for provider in _PROVIDERS:
        # Attempt 1: requested (normalized) period/interval
        try:
            candles = provider.get_history(t, p_norm, i_norm)
            if not candles:
                raise RuntimeError(f"{provider.name} returned empty history")
            logger.debug("History OK from %s (%s/%s) for %s: %d rows",
                         provider.name, p_norm, i_norm, t, len(candles))
            return [_candle_dict(c) for c in candles]
        except Exception as e:
            last_err = e
            logger.info("History attempt#1 failed on %s for %s (%s/%s): %s",
                        provider.name, t, p_norm, i_norm, e)

        # Attempt 2: broaden period, keep interval (only if first failed and period != 'max')
        if p_norm != "max":
            try:
                candles = provider.get_history(t, "max", i_norm)
                if not candles:
                    raise RuntimeError(f"{provider.name} returned empty history (broadened)")
                logger.debug("History OK from %s (max/%s) for %s: %d rows",
                             provider.name, i_norm, t, len(candles))
                return [_candle_dict(c) for c in candles]
            except Exception as e2:
                last_err = e2
                logger.info("History attempt#2 failed on %s for %s (max/%s): %s",
                            provider.name, t, i_norm, e2)

        # Otherwise continue to next provider

    msg = f"Eroare history (all providers) for {t}: {last_err}"
    logger.error(msg)
    raise HTTPException(status_code=502, detail=msg)


# ---------------------------
# Helpers
# ---------------------------

def _candle_dict(c: Candle) -> Dict:
    return {
        "date": c.date.isoformat(),
        "open": float(c.open),
        "high": float(c.high),
        "low": float(c.low),
        "close": float(c.close),
        "volume": float(c.volume),
    }
