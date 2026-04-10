import json
import re

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from monitoring.logger import log

_client = Anthropic(api_key=settings.anthropic_api_key)

SIGNAL_SYSTEM_PROMPT = (
    "You are a disciplined ETF swing signal analyst. "
    "You receive raw technical indicator data for an ETF across two timeframes: 4h (entry timing) and 1d (trend). "
    "Analyze the indicators independently and decide whether there is a clear swing trading opportunity. "
    "Be selective and conservative — only signal LONG or SHORT when there is genuine alignment "
    "across both timeframes. Most setups should be NEUTRAL. "
    "Respond in JSON with three fields: "
    "\"direction\": \"long\", \"short\", or \"neutral\", "
    "\"confidence\": integer 1-100 representing how confident you are in your analysis "
    "(e.g. neutral with 40% means you analyzed thoroughly but found no clear setup, "
    "neutral with 10% means indicators are too mixed to read — never return 0), "
    "\"reasoning\": string (100 words max, only if direction is long or short, else empty string)."
)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def evaluate_with_claude(symbol: str, snapshot_summary: str) -> tuple[str, int, str]:
    prompt = (
        f"ETF: {symbol}\n\n"
        f"Indicator snapshot:\n{snapshot_summary}\n\n"
        "Analyze these indicators and give your signal."
    )

    try:
        response = _client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            temperature=settings.anthropic_temperature,
            system=SIGNAL_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in response.content if b.type == "text").strip()

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON object found in response: {text!r}")
        result = json.loads(match.group())
        direction = result.get("direction", "neutral").lower()
        confidence = int(result.get("confidence", 0))
        reasoning = result.get("reasoning", "").strip()
        return direction, confidence, reasoning

    except Exception as e:
        log.error(f"Claude evaluation error for {symbol}: {e}")
        return "error", -1, ""
