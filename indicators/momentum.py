import pandas as pd
import pandas_ta as ta


def compute_momentum(df: pd.DataFrame) -> dict:
    """
    Compute RSI from a closing price series.
    Returns a flat dict with the latest RSI value and zone label.
    """
    if df.empty or len(df) < 15:
        return {}

    close = df["close"]
    rsi = ta.rsi(close, length=14)

    if rsi is None or rsi.empty:
        return {}

    value = round(rsi.iloc[-1], 2)

    if value < 30:
        zone = "oversold"
    elif value < 45:
        zone = "weak"
    elif value < 55:
        zone = "neutral"
    elif value < 70:
        zone = "bullish"
    else:
        zone = "overbought"

    return {
        "rsi": value,
        "rsi_zone": zone,
    }
