from datetime import datetime

import pytz

from config.settings import settings

ET = pytz.timezone(settings.timezone)


def now_et() -> datetime:
    return datetime.now(ET)


def is_market_open() -> bool:
    """True if the US market is currently open (Mon–Fri, 9:30–16:00 ET)."""
    now = now_et()
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= now < market_close


def is_trading_day() -> bool:
    """True if today is a weekday."""
    return now_et().weekday() < 5


def session_label() -> str:
    """Return a label for the current evaluation window."""
    now = now_et()
    hour, minute = now.hour, now.minute
    total_minutes = hour * 60 + minute

    if total_minutes < 9 * 60 + 30:
        return "pre-market"
    elif total_minutes < 11 * 60:
        return "morning"
    elif total_minutes < 13 * 60:
        return "midday"
    elif total_minutes < 15 * 60:
        return "afternoon"
    else:
        return "close"
