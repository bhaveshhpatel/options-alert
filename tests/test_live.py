from datetime import datetime, timezone
from app.live import LiveAlertEngine
from app.config import Config
from app.models import SocialEvent


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


def test_live_engine_deduplicates_and_detects_signal():
    engine = LiveAlertEngine(make_cfg())
    event = SocialEvent(
        "x",
        "1",
        "alice",
        "$P REPEAT SWEEPER BUYING",
        datetime.now(timezone.utc),
    )
    engine.on_event(event)
    assert "x:1" in engine.seen
