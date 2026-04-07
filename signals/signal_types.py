from dataclasses import dataclass
from enum import Enum


class SignalDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class SignalStrength(Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


@dataclass
class SwingSignal:
    symbol: str
    direction: SignalDirection
    strength: SignalStrength
    reasons: list[str]

    def __str__(self) -> str:
        return f"{self.symbol} {self.direction.value} ({self.strength.value}): {', '.join(self.reasons)}"
