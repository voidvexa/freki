from datetime import datetime

import pytz

from config.settings import settings
from config.symbols import ETF_SYMBOLS
from config.trading_params import ATR_STOP_MULT, MIN_RISK_REWARD
from indicators.composite import get_full_snapshot
from signals.day_signals import evaluate_signal
from signals.formatter import format_snapshot_summary
from agent.claude_client import evaluate_with_claude
from notifications.telegram import send_signal
from data.market_calendar import session_label
from monitoring.logger import log

ET = pytz.timezone(settings.timezone)


def run_signal_scan():
    now = datetime.now(ET)
    session = session_label()
    log.info(f"{'='*50}")
    log.info(f"  Signal Scan | {len(ETF_SYMBOLS)} ETFs | {session} | {now.strftime('%H:%M ET')}")
    log.info(f"{'='*50}")

    for sym in ETF_SYMBOLS:
        snap = get_full_snapshot(sym)
        if not snap.get("current_price"):
            log.warning(f"  {sym}: no data, skipping")
            continue

        price = snap["current_price"]
        bar_time = snap.get("last_bar_time", "N/A")
        atr = snap.get("4h", {}).get("atr", 0)
        stop_dist = atr * ATR_STOP_MULT if atr else price * 0.01

        # Pre-analysis — for log comparison only, NOT sent to Claude
        pre = evaluate_signal(snap)
        pre_label = f"{pre.direction.value}/{pre.strength.value}"

        # Claude independently analyzes raw indicators
        summary = format_snapshot_summary(snap)
        direction, confidence, reasoning = evaluate_with_claude(sym, summary)

        if direction == "long":
            stop = round(price - stop_dist, 2)
            target = round(price + stop_dist * MIN_RISK_REWARD, 2)
            log.info(
                f"  {sym:6s} | LONG  | ${price:.2f} ({bar_time}) | SL ${stop:.2f} | TP ${target:.2f} | "
                f"agent={confidence}% | pre={pre_label}"
            )
            send_signal(sym, direction, price, bar_time, stop, target, confidence, reasoning)

        elif direction == "short":
            stop = round(price + stop_dist, 2)
            target = round(price - stop_dist * MIN_RISK_REWARD, 2)
            log.info(
                f"  {sym:6s} | SHORT | ${price:.2f} ({bar_time}) | SL ${stop:.2f} | TP ${target:.2f} | "
                f"agent={confidence}% | pre={pre_label}"
            )
            send_signal(sym, direction, price, bar_time, stop, target, confidence, reasoning)

        else:
            log.info(f"  {sym:6s} | NEUTRAL | ${price:.2f} ({bar_time}) | pre={pre_label}")

    log.info(f"{'='*50}")
