from datetime import datetime, timedelta

import pandas as pd
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from data.alpaca_client import get_data_client


def _to_alpaca_timeframe(timeframe: str) -> TimeFrame:
    mapping = {
        "1d": TimeFrame(1, TimeFrameUnit.Day),
        "4h": TimeFrame(4, TimeFrameUnit.Hour),
        "1h": TimeFrame(1, TimeFrameUnit.Hour),
    }
    if timeframe not in mapping:
        raise ValueError(f"Unsupported timeframe '{timeframe}'. Use: {list(mapping)}")
    return mapping[timeframe]


def get_bars(symbol: str, timeframe: str = "30m", limit: int = 100) -> pd.DataFrame:
    tf = _to_alpaca_timeframe(timeframe)
    day_multiplier = {"1d": 1.5, "4h": 0.7, "1h": 0.25}
    days_back = max(10, int(limit * day_multiplier.get(timeframe, 0.15)))
    start = datetime.utcnow() - timedelta(days=days_back)

    try:
        client = get_data_client()
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=start,
            adjustment="split",
        )
        bars = client.get_stock_bars(request)

        df = bars.df
        if df.empty:
            return pd.DataFrame()

        if isinstance(df.index, pd.MultiIndex):
            df = df.xs(symbol, level="symbol")

        df.index = pd.to_datetime(df.index, utc=True)
        df = df[["open", "high", "low", "close", "volume"]].copy()
        df.sort_index(inplace=True)
        return df.tail(limit)

    except Exception as e:
        from monitoring.logger import log
        log.warning(f"get_bars({symbol}, {timeframe}): {e}")
        return pd.DataFrame()
