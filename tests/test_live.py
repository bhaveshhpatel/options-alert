from datetime import datetime, timezone

from app.config import Config
from app.live import LiveAlertEngine
from app.models import SocialEvent
from app.providers.stocktwits import StocktwitsFirestream


def make_cfg():
    return Config(
        stocktwits_username="",
        stocktwits_password="",
        x_bearer_token="",
        x_query="",
        alert_webhook_url="",
        provider_runtime_seconds=30,
        correlation_window_minutes=60,
        x_poll_seconds=30,
    )


def test_live_engine_deduplicates():
    engine = LiveAlertEngine(make_cfg())
    event = SocialEvent(
        "x",
        "1",
        "alice",
        "$P REPEAT SWEEPER BUYING",
        datetime.now(timezone.utc),
    )
    engine.on_event(event)
    engine.on_event(event)
    assert len(engine.seen) == 1


def test_stocktwits_firestream_parses_wrapped_message():
    provider = StocktwitsFirestream("u", "p")
    payload = (
        '{"object":"Message","action":"create","seq_id":"42",'
        '"time":"2026-09-23T12:00:00Z","data":'
        '{"id":123,"body":"$P REPEAT SWEEPER BUYING",'
        '"created_at":"2026-09-23T12:00:00Z",'
        '"user":{"username":"alice"}}}'
    )
    event, seq = provider._parse(payload)
    assert event.source == "stocktwits"
    assert event.event_id == "123"
    assert event.author == "alice"
    assert event.text == "$P REPEAT SWEEPER BUYING"
    assert seq == "42"
