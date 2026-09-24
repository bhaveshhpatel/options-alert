import re
from .models import SocialEvent, SignalEvent
PATTERNS=[(r'repeat.{0,30}sweeper.{0,30}buy','repeat_sweeper_buying',0.98),(r'repeat.{0,30}buying','repeat_buying',0.90),(r'repeat.{0,30}activity','repeat_activity',0.88),(r'(?:unusual|bull(?:ish)?).{0,20}sweeper','bull_sweeper',0.90),(r'active.{0,20}flow','active_flow',0.78)]
def ticker(text):
    m=re.search(r'\$([A-Z][A-Z0-9]{0,5})\b',text.upper())
    return m.group(1) if m else None
def detect(event: SocialEvent):
    t=ticker(event.text)
    if not t:return None
    low=event.text.lower()
    for p,name,confidence in PATTERNS:
        if re.search(p,low):
            direction='bearish' if re.search(r'\bput|bearish|selling\b',low) else 'bullish'
            return SignalEvent(event,t,name,confidence,direction)
    return None
