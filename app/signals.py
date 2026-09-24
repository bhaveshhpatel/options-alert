from dataclasses import dataclass
import re
from typing import Optional

@dataclass(frozen=True)
class Signal:
    ticker: str
    signal_type: str
    confidence: float
    matched_text: str

PATTERNS = [
    (r"repeat\s+(?:sweeper\s+)?buying", "repeat_sweeper_buying", 0.95),
    (r"repeat\s+activity", "repeat_activity", 0.85),
    (r"(?:unusual|bull(?:ish)?)\s+sweeper", "bull_sweeper", 0.90),
    (r"active\s+flow", "active_flow", 0.75),
    (r"repeat\s+buying", "repeat_buying", 0.85),
]

def extract_ticker(text: str) -> Optional[str]:
    m = re.search(r"\$([A-Z][A-Z0-9]{0,5})\b", text.upper())
    return m.group(1) if m else None

def classify(text: str) -> Optional[Signal]:
    ticker = extract_ticker(text)
    if not ticker: return None
    for pattern, signal_type, confidence in PATTERNS:
        m = re.search(pattern, text.lower())
        if m: return Signal(ticker, signal_type, confidence, m.group(0))
    return None
