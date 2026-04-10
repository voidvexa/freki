# Freki

> Built by a human, pair-programmed with [Claude](https://claude.ai). The AI writes the signals *and* some of the code that generates them. Skynet starts with ETFs, apparently.

ETF signal scanner that runs on a schedule during US market hours. It fetches price data for a list of ETFs, computes technical indicators on two timeframes, sends the data to Claude for analysis, and delivers actionable trade signals to Telegram.

## How It Works

| Parameter | Value |
|---|---|
| Entry timeframe | 30-minute candles (100 bars) |
| Trend bias | 4-hour candles (100 bars) |
| Stop loss | ATR(30m) x 1.0 |
| Take profit | Stop distance x 1.5 (R:R = 1:1.5) |
| Min confidence | 65% |
| Scans per day | 11 (every 30 min, 10:32 - 15:32 ET) |
| EOD alert | 15:50 ET |

### Scan Schedule (Eastern Time)

| # | Time | Last Complete 30m Candle |
|---|---|---|
| 1 | 10:32 | 10:00 - 10:30 |
| 2 | 11:02 | 10:30 - 11:00 |
| 3 | 11:32 | 11:00 - 11:30 |
| 4 | 12:02 | 11:30 - 12:00 |
| 5 | 12:32 | 12:00 - 12:30 |
| 6 | 13:02 | 12:30 - 13:00 |
| 7 | 13:32 | 13:00 - 13:30 |
| 8 | 14:02 | 13:30 - 14:00 |
| 9 | 14:32 | 14:00 - 14:30 |
| 10 | 15:02 | 14:30 - 15:00 |
| 11 | 15:32 | 15:00 - 15:30 |
| -- | 15:50 | *EOD close reminder* |

## Pipeline

Each scan follows this sequence for every symbol in the watchlist:

### 1. Fetch Data

The app calls the Alpaca API and requests two sets of candles:

- **100 bars of 30m candles** -- the last ~2 trading days of price action
- **100 bars of 4h candles** -- the last ~2-3 weeks for trend context

### 2. Compute Indicators

For both timeframes, the following indicators are computed from raw OHLCV data:

| Indicator | Purpose |
|---|---|
| MACD bullish? | Is momentum pointing up or down? |
| MACD expanding? | Is that momentum getting stronger or fading? |
| Price above EMA21? | Is price above or below its recent average? |
| RSI (0-100) | Is the ETF overbought (>70), oversold (<30), or neutral? |
| Volume ratio | Is current volume higher or lower than the 20-bar average? |
| OBV rising? | Is money flowing in (buying) or out (selling)? |

ATR is computed on the entry timeframe for stop loss and take profit calculations.

> These indicators work for both long and short signals. For example, "MACD bullish = false" means bearish momentum; "Price above EMA21 = false" means a downtrend; "OBV rising = false" means money flowing out. Claude interprets the full picture in both directions.

### 3. Build Summary

The indicators are formatted into a readable text block:

```
Price: $550.00
30M: MACD bullish (expanding) | above EMA21 | RSI 58.2 | ATR $1.05 | Vol 1.4x | OBV rising
4H:  MACD bullish (expanding) | above EMA21 | RSI 62.1 | ATR $5.75 | Vol 0.9x | OBV rising
```

### 4. Claude Evaluation

The summary is sent to Claude with a system prompt instructing it to act as a conservative signal analyst. Claude reads the indicators, reasons through them, and responds with:

```json
{
  "direction": "long",
  "confidence": 72,
  "reasoning": "Both timeframes aligned bullish..."
}
```

### 5. Confidence Filter

If `confidence >= 65%`, the signal proceeds. Otherwise it's logged as neutral and skipped.

### 6. Calculate Stop Loss and Take Profit

Using the entry timeframe ATR (e.g. $1.05):

|  | Long | Short |
|---|---|---|
| Entry | $550.00 | $550.00 |
| Stop Loss | $550.00 - $1.05 = **$548.95** | $550.00 + $1.05 = **$551.05** |
| Take Profit | $550.00 + $1.58 = **$551.58** | $550.00 - $1.58 = **$548.42** |

Risk-to-reward is always **1:1.5**.

### 7. Telegram Notification

```
LONG SPY

Entry: $550.00 (as of 2026-04-09 12:00 ET)
Stop Loss: $548.95
Take Profit: $551.58
Confidence: 72%

Reasoning:
Both timeframes aligned bullish. 30m MACD expanding with price
above EMA21. Volume confirms the move with OBV rising and 1.4x
average volume.
```

### 8. Repeat

Steps 1-7 repeat for each symbol in the watchlist. After all symbols are scanned, the app sleeps until the next scheduled scan.

## End of Day

At **15:50 ET** (10 minutes before market close), the app sends a reminder to close all open positions.

## Setup

### Requirements

- Python 3.11+
- [Alpaca](https://alpaca.markets/) account (market data API)
- [Anthropic](https://console.anthropic.com/) API key
- [Telegram bot](https://core.telegram.org/bots#creating-a-new-bot) + chat ID

### Installation

```bash
git clone <repo-url> && cd freki
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
```

### Running

```bash
python main.py
```

The scheduler will start and run scans at the configured times. Press `Ctrl+C` to stop.

## Project Structure

```
freki/
  main.py                    # Scheduler entry point
  config/
    settings.py              # Environment config (pydantic-settings)
    symbols.py               # ETF watchlist
    trading_params.py         # ATR multiplier, R:R, confidence threshold
  data/
    alpaca_client.py          # Alpaca API client
    market_data.py            # OHLCV data fetching
  indicators/
    composite.py              # Technical indicator computation
  signals/
    formatter.py              # Indicator summary formatting
  agent/
    claude_client.py          # Claude API integration + prompt
  scheduler/
    signal_runner.py          # Main scan loop
  notifications/
    telegram.py               # Telegram delivery
  monitoring/
    logger.py                 # Loguru configuration
```

## License

Private. Not for redistribution.
