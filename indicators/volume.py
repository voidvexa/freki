import pandas as pd
import pandas_ta as ta


def compute_volume(df: pd.DataFrame) -> dict:
    """
    Compute OBV and volume-vs-average from OHLCV data.
    Returns a flat dict with the latest values.
    """
    if df.empty or len(df) < 21:
        return {}

    close = df["close"]
    volume = df["volume"]

    obv = ta.obv(close, volume)

    vol_avg_20 = volume.rolling(20).mean().iloc[-1]
    vol_current = volume.iloc[-1]
    vol_ratio = round(vol_current / vol_avg_20, 2) if vol_avg_20 > 0 else None

    result = {
        "volume": int(vol_current),
        "volume_avg_20": int(vol_avg_20),
        "volume_ratio": vol_ratio,
        "volume_surge": bool(vol_ratio >= 1.2) if vol_ratio is not None else None,
    }

    if obv is not None and len(obv) >= 5:
        obv_now = obv.iloc[-1]
        obv_5_ago = obv.iloc[-5]
        result["obv"] = round(obv_now, 0)
        result["obv_rising"] = bool(obv_now > obv_5_ago)

    return result
