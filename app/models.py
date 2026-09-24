from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class SocialEvent:
    source: str
    event_id: str
    author: str
    text: str
    created_at: datetime
    url: Optional[str] = None

@dataclass(frozen=True)
class SignalEvent:
    social: SocialEvent
    ticker: str
    signal_type: str
    confidence: float
    direction: str
