def format_snapshot_summary(snapshot: dict) -> str:
    """Format a snapshot into a readable text block for Claude reasoning."""
    lines = []
    price = snapshot.get("current_price")
    if price:
        lines.append(f"Price: ${price:.2f}")

    for tf_key in ("4h", "1d"):
        tf = snapshot.get(tf_key, {})
        if not tf:
            continue
        label = tf_key.upper()
        macd_dir = "bullish" if tf.get("macd_bullish") else "bearish"
        hist = "expanding" if tf.get("macd_hist_expanding") else "contracting"
        ema = "above" if tf.get("price_above_ema21") else "below"
        rsi = tf.get("rsi", "N/A")
        atr = tf.get("atr", "N/A")
        obv = "rising" if tf.get("obv_rising") else "falling"
        vol_ratio = tf.get("volume_ratio", "N/A")

        lines.append(
            f"{label}: MACD {macd_dir} ({hist}) | {ema} EMA21 | "
            f"RSI {rsi} | ATR ${atr} | Vol {vol_ratio}x | OBV {obv}"
        )

    return "\n".join(lines)
