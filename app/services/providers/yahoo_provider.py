from __future__ import annotations
from typing import Iterable, List
from datetime import datetime, timezone
import yfinance as yf
from .base import MarketProvider, Quote, Candle

_PERIOD_MAP = {
    "1d":"1d","5d":"5d","1mo":"1mo","3mo":"3mo","6mo":"6mo","1y":"1y","2y":"2y","5y":"5y","10y":"10y","ytd":"ytd","max":"max"
}
_INTERVAL_MAP = {
    "1m":"1m","2m":"2m","5m":"5m","15m":"15m","30m":"30m","60m":"60m","90m":"90m","1h":"1h","1d":"1d","5d":"5d","1wk":"1wk","1mo":"1mo","3mo":"3mo"
}

class YahooProvider(MarketProvider):
    name = "yahoo"

    def get_quotes(self, tickers: Iterable[str]) -> List[Quote]:
        tickers = [t.upper() for t in tickers]
        if not tickers: return []
        data = yf.download(tickers=" ".join(tickers), period="1d", interval="1m", group_by="ticker", progress=False, prepost=True, threads=True)
        quotes: List[Quote] = []
        # yfinance returnează fie multi-index pe multe tickere, fie un DataFrame simplu la un singur ticker
        def last_close(df):
            try:
                return float(df["Close"].dropna().iloc[-1])
            except Exception:
                return None
        if isinstance(data.columns, yf.pdr_data._utils.MultiIndexType):
            for t in tickers:
                df = data[t] if t in data.columns.levels[0] else None
                price = last_close(df) if df is not None else None
                quotes.append(Quote(ticker=t, price=price, currency=None, ts=datetime.now(timezone.utc), provider=self.name))
        else:
            price = last_close(data)
            quotes.append(Quote(ticker=tickers[0], price=price, currency=None, ts=datetime.now(timezone.utc), provider=self.name))
        return quotes

    def get_history(self, ticker: str, period: str, interval: str) -> List[Candle]:
        period = _PERIOD_MAP.get(period, "1y")
        interval = _INTERVAL_MAP.get(interval, "1d")
        df = yf.download(tickers=ticker, period=period, interval=interval, progress=False, prepost=True, threads=True)
        df = df.dropna()
        candles: List[Candle] = []
        for idx, row in df.iterrows():
            # idx poate fi timestamp tz-aware; îl convertim la UTC
            ts = idx.tz_convert("UTC").to_pydatetime() if hasattr(idx, "tz_convert") else datetime.fromtimestamp(int(idx.timestamp()), timezone.utc)
            candles.append(Candle(
                date=ts,
                open=float(row["Open"]), high=float(row["High"]), low=float(row["Low"]),
                close=float(row["Close"]), volume=float(row.get("Volume", 0.0)),
            ))
        return candles
