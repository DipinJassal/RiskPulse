"""
Looks up real-time stock data for entities extracted by the classifier.
Uses yfinance Search to resolve company names to tickers, then fetches
1-day price change % and current price.
"""
from __future__ import annotations

import yfinance as yf


def _resolve_ticker(entity: str) -> str | None:
    try:
        results = yf.Search(entity, max_results=1).quotes
        if results:
            return results[0].get("symbol")
    except Exception:
        pass
    return None


def get_stock_info(entities: list[str]) -> dict:
    """
    Given a list of company/sector names, return a dict mapping
    ticker -> {price, change_pct, name} for any that resolve.
    Silently skips entities that can't be resolved or have no data.
    """
    result: dict = {}
    seen: set[str] = set()

    for entity in entities[:5]:  # cap at 5 to stay fast
        ticker_sym = _resolve_ticker(entity)
        if not ticker_sym or ticker_sym in seen:
            continue
        seen.add(ticker_sym)
        try:
            ticker = yf.Ticker(ticker_sym)
            hist = ticker.history(period="2d")
            if len(hist) < 2:
                continue
            prev_close = hist["Close"].iloc[-2]
            curr_close = hist["Close"].iloc[-1]
            change_pct = round(((curr_close - prev_close) / prev_close) * 100, 2)
            result[ticker_sym] = {
                "name": entity,
                "price": round(float(curr_close), 2),
                "change_pct": change_pct,
            }
        except Exception:
            continue

    return result
