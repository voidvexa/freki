import pandas as pd
import pandas_ta as ta


def compute_trend(df: pd.DataFrame) -> dict:
    """
    Compute EMA, SMA, and MACD from a closing price series.
    Returns a flat dict of indicator values based on the latest bar.
    """
    if df.empty or len(df) < 26:
        return {}

    close = df["close"]

    ema9 = ta.ema(close, length=9)
    ema21 = ta.ema(close, length=21)
    sma50 = ta.sma(close, length=50)
    sma200 = ta.sma(close, length=200)
    macd_df = ta.macd(close, fast=12, slow=26, signal=9)

    latest_close = close.iloc[-1]

    result = {
        "ema9": round(ema9.iloc[-1], 4) if ema9 is not None else None,
        "ema21": round(ema21.iloc[-1], 4) if ema21 is not None else None,
        "sma50": round(sma50.iloc[-1], 4) if sma50 is not None else None,
        "sma200": round(sma200.iloc[-1], 4) if sma200 is not None else None,
        "price_above_ema21": bool(latest_close > ema21.iloc[-1]) if ema21 is not None else None,
        "price_above_sma50": bool(latest_close > sma50.iloc[-1]) if sma50 is not None else None,
        "golden_cross": bool(sma50.iloc[-1] > sma200.iloc[-1]) if (sma50 is not None and sma200 is not None) else None,
    }

    if macd_df is not None and not macd_df.empty:
        macd_line = macd_df["MACD_12_26_9"].iloc[-1]
        signal_line = macd_df["MACDs_12_26_9"].iloc[-1]
        histogram = macd_df["MACDh_12_26_9"].iloc[-1]
        prev_histogram = macd_df["MACDh_12_26_9"].iloc[-2]

        result.update({
            "macd_line": round(macd_line, 4),
            "macd_signal": round(signal_line, 4),
            "macd_histogram": round(histogram, 4),
            "macd_hist_expanding": bool(abs(histogram) > abs(prev_histogram)),
            "macd_bullish": bool(macd_line > signal_line),
        })

    return result
