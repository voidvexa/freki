import pandas as pd
import pandas_ta as ta
import pytz

from data.market_data import get_bars
from indicators.trend import compute_trend
from indicators.momentum import compute_momentum
from indicators.volume import compute_volume
from config.trading_params import INTRADAY_LOOKBACK, TREND_LOOKBACK


def _compute_atr(df: pd.DataFrame, period: int = 14) -> float | None:
    if df.empty or len(df) < period + 1:
        return None
    atr = ta.atr(df["high"], df["low"], df["close"], length=period)
    if atr is None or atr.empty:
        return None
    return round(atr.iloc[-1], 4)


def get_full_snapshot(symbol: str) -> dict:
    """
    Fetch 4h and 1d bars for a symbol and compute all indicators.
    4h = entry timing and momentum signals.
    1d = trend filter.
    """
    df_4h = get_bars(symbol, timeframe="4h", limit=INTRADAY_LOOKBACK)
    df_1d = get_bars(symbol, timeframe="1d", limit=TREND_LOOKBACK)

    last_bar_time = (
        df_4h.index[-1].astimezone(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M ET")
        if not df_4h.empty else None
    )

    snapshot = {
        "symbol": symbol,
        "current_price": round(df_4h["close"].iloc[-1], 4) if not df_4h.empty else None,
        "last_bar_time": last_bar_time,
        "4h": {},
        "1d": {},
    }

    if not df_4h.empty:
        snapshot["4h"] = {
            **compute_trend(df_4h),
            **compute_momentum(df_4h),
            **compute_volume(df_4h),
            "atr": _compute_atr(df_4h),
        }

    if not df_1d.empty:
        snapshot["1d"] = {
            **compute_trend(df_1d),
            **compute_momentum(df_1d),
            **compute_volume(df_1d),
            "atr": _compute_atr(df_1d),
        }

    return snapshot
