from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Iterable, List, Dict, Any
from datetime import datetime

@dataclass
class Quote:
    ticker: str
    price: float | None
    currency: str | None = None
    ts: datetime | None = None
    provider: str | None = None

@dataclass
class Candle:
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class MarketProvider(Protocol):
    name: str
    def get_quotes(self, tickers: Iterable[str]) -> List[Quote]: ...
    def get_history(self, ticker: str, period: str, interval: str) -> List[Candle]: ...
