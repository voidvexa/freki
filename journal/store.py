import json
import os
import sqlite3
from datetime import datetime, timezone

from config.settings import settings
from monitoring.logger import log

DB_PATH = os.path.join("journal", "signals.sqlite")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emitted_at TEXT NOT NULL,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,
    bar_time TEXT,
    stop REAL NOT NULL,
    target REAL NOT NULL,
    reasoning TEXT,
    model TEXT,
    atr REAL,
    rsi_4h REAL,
    rsi_1d REAL,
    macd_4h_bullish INTEGER,
    ema_4h_above INTEGER,
    ema_1d_above INTEGER,
    vol_ratio_4h REAL,
    obv_4h_rising INTEGER,
    macro_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_signals_emitted_at ON signals(emitted_at);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
"""


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA)


_ensure_schema()


def _to_int_bool(v) -> int | None:
    if v is None:
        return None
    return 1 if v else 0


def record_signal(
    symbol: str,
    direction: str,
    entry_price: float,
    bar_time: str | None,
    stop: float,
    target: float,
    reasoning: str,
    snapshot: dict,
    macro: dict | None,
) -> None:
    tf_4h = snapshot.get("4h", {}) or {}
    tf_1d = snapshot.get("1d", {}) or {}

    row = (
        datetime.now(timezone.utc).isoformat(),
        symbol,
        direction,
        entry_price,
        bar_time,
        stop,
        target,
        reasoning,
        settings.anthropic_model,
        tf_4h.get("atr"),
        tf_4h.get("rsi"),
        tf_1d.get("rsi"),
        _to_int_bool(tf_4h.get("macd_bullish")),
        _to_int_bool(tf_4h.get("price_above_ema21")),
        _to_int_bool(tf_1d.get("price_above_ema21")),
        tf_4h.get("volume_ratio"),
        _to_int_bool(tf_4h.get("obv_rising")),
        json.dumps(macro) if macro else None,
    )

    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO signals (
                    emitted_at, symbol, direction, entry_price, bar_time,
                    stop, target, reasoning, model,
                    atr, rsi_4h, rsi_1d, macd_4h_bullish, ema_4h_above,
                    ema_1d_above, vol_ratio_4h, obv_4h_rising, macro_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                row,
            )
    except sqlite3.Error as e:
        log.error(f"Journal write failed for {symbol}: {e}")
