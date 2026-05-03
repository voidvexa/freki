from collections import Counter
from datetime import datetime, timedelta, timezone

from journal.store import _connect
from notifications.telegram import send_message
from monitoring.logger import log


def send_weekly_digest() -> None:
    since = datetime.now(timezone.utc) - timedelta(days=7)
    since_iso = since.isoformat()

    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT symbol, direction FROM signals WHERE emitted_at >= ?",
                (since_iso,),
            ).fetchall()
    except Exception as e:
        log.error(f"Weekly digest query failed: {e}")
        return

    total = len(rows)
    if total == 0:
        send_message("*Weekly Digest*\n\nNo signals in the last 7 days.")
        log.info("Weekly digest sent: no signals")
        return

    by_direction = Counter(r["direction"] for r in rows)
    by_symbol = Counter(r["symbol"] for r in rows)

    lines = [
        "*Weekly Digest* — last 7 days",
        "",
        f"*Total signals:* {total}",
        f"*Long:* {by_direction.get('long', 0)}",
        f"*Short:* {by_direction.get('short', 0)}",
        "",
        "*By ETF:*",
    ]
    for sym, count in by_symbol.most_common():
        lines.append(f"  {sym}: {count}")

    send_message("\n".join(lines))
    log.info(f"Weekly digest sent: {total} signals across {len(by_symbol)} ETFs")
