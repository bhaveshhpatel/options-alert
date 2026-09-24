from datetime import datetime,timezone
from app.models import SocialEvent
from app.detector import detect

def test_repeat_sweeper():
    s=detect(SocialEvent('x','1','tester','$P REPEAT SWEEPER BUYING',datetime.now(timezone.utc)))
    assert s and s.ticker=='P' and s.signal_type=='repeat_sweeper_buying'

def test_non_signal():
    assert detect(SocialEvent('x','2','tester','$P earnings tomorrow',datetime.now(timezone.utc))) is None
