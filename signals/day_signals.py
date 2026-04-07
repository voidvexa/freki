from signals.signal_types import SwingSignal, SignalDirection, SignalStrength


def evaluate_signal(snapshot: dict) -> SwingSignal:
    """
    Score a symbol for a swing trade.
    1d = trend direction (dominant). 4h = entry timing.
    """
    symbol = snapshot["symbol"]
    tf4h = snapshot.get("4h", {})
    tf1d = snapshot.get("1d", {})

    bullish_reasons = []
    bearish_reasons = []

    # --- 1D trend (weighted heavily) ---
    d1_bullish = tf1d.get("macd_bullish") is True
    d1_bearish = tf1d.get("macd_bullish") is False
    d1_above_ema = tf1d.get("price_above_ema21") is True
    d1_below_ema = tf1d.get("price_above_ema21") is False

    if d1_bullish:
        bullish_reasons.extend(["1d MACD bullish", "1d trend up"])
    elif d1_bearish:
        bearish_reasons.extend(["1d MACD bearish", "1d trend down"])

    if d1_above_ema:
        bullish_reasons.append("price above 1d EMA21")
    elif d1_below_ema:
        bearish_reasons.append("price below 1d EMA21")

    strong_1d_bearish = d1_bearish and d1_below_ema
    strong_1d_bullish = d1_bullish and d1_above_ema

    rsi_4h = tf4h.get("rsi")
    rsi_1d = tf1d.get("rsi")

    if strong_1d_bearish:
        if rsi_4h is not None and rsi_4h >= 55:
            bearish_reasons.append(f"4h RSI {rsi_4h} — overbought bounce in 1d downtrend (short entry)")
        elif rsi_4h is not None and rsi_4h < 45:
            bearish_reasons.append(f"4h RSI {rsi_4h} — momentum aligning with 1d downtrend")
        if tf4h.get("macd_bullish") is False:
            bearish_reasons.append("4h MACD also bearish — full alignment for short")
        if tf1d.get("obv_rising") is False:
            bearish_reasons.append("OBV falling — distribution confirms short")

    elif strong_1d_bullish:
        if rsi_4h is not None and 45 <= rsi_4h <= 62:
            bullish_reasons.append(f"4h RSI {rsi_4h} — pullback in 1d uptrend (long entry)")
        if tf4h.get("macd_bullish") is True and tf4h.get("macd_hist_expanding"):
            bullish_reasons.append("4h MACD bullish + histogram expanding")
        if tf1d.get("obv_rising") is True:
            bullish_reasons.append("OBV rising — accumulation confirms long")

    else:
        if tf4h.get("macd_bullish") is True and tf4h.get("macd_hist_expanding"):
            bullish_reasons.append("4h MACD bullish + expanding (mixed trend)")
        elif tf4h.get("macd_bullish") is False and tf4h.get("macd_hist_expanding"):
            bearish_reasons.append("4h MACD bearish + expanding (mixed trend)")

    # --- 1d RSI extremes ---
    if rsi_1d is not None:
        if rsi_1d < 35 and strong_1d_bearish:
            bearish_reasons.append(f"1d RSI {rsi_1d} — deeply oversold but trend still down")
        elif rsi_1d > 65 and strong_1d_bullish:
            bullish_reasons.append(f"1d RSI {rsi_1d} — momentum strong")

    # --- Tally ---
    score = len(bullish_reasons) - len(bearish_reasons)

    if score >= 4:
        direction, strength = SignalDirection.BULLISH, SignalStrength.STRONG
        reasons = bullish_reasons
    elif score >= 2:
        direction, strength = SignalDirection.BULLISH, SignalStrength.MODERATE
        reasons = bullish_reasons
    elif score <= -3:
        direction, strength = SignalDirection.BEARISH, SignalStrength.STRONG
        reasons = bearish_reasons
    elif score <= -1:
        direction, strength = SignalDirection.BEARISH, SignalStrength.MODERATE
        reasons = bearish_reasons
    else:
        direction, strength = SignalDirection.NEUTRAL, SignalStrength.WEAK
        reasons = bullish_reasons + bearish_reasons

    return SwingSignal(symbol=symbol, direction=direction, strength=strength, reasons=reasons)
