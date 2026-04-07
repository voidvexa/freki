import requests

from config.settings import settings
from monitoring.logger import log

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"


def send_message(text: str) -> None:
    try:
        resp = requests.post(
            TELEGRAM_API,
            json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        if not resp.ok:
            log.warning(f"Telegram send failed: {resp.status_code} {resp.text}")
    except Exception as e:
        log.error(f"Telegram error: {e}")


def send_signal(symbol: str, direction: str, price: float, bar_time: str, stop: float, target: float, confidence: int, reasoning: str) -> None:
    """Send a single actionable signal (LONG or SHORT only)."""
    direction_upper = direction.upper()
    message = (
        f"*{direction_upper}* {symbol}\n\n"
        f"*Entry:* ${price:.2f} _(as of {bar_time})_\n"
        f"*Stop Loss:* ${stop:.2f}\n"
        f"*Take Profit:* ${target:.2f}\n"
        f"*Confidence:* {confidence}%\n\n"
        f"*Reasoning:*\n{reasoning}"
    )
    send_message(message)
