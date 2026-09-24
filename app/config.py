from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _int_env(name, default):
    value = os.getenv(name, "").strip()
    return int(value) if value else default


@dataclass(frozen=True)
class Config:
    stocktwits_username: str = os.getenv("STOCKTWITS_USERNAME", "").strip()
    stocktwits_password: str = os.getenv("STOCKTWITS_PASSWORD", "")
    x_bearer_token: str = os.getenv("X_BEARER_TOKEN", "").strip()
    x_query: str = os.getenv(
        "X_QUERY",
        '("sweeper" OR "repeat buying" OR "repeat activity") -is:retweet',
    ).strip()
    alert_webhook_url: str = os.getenv("ALERT_WEBHOOK_URL", "").strip()

    # WhatsApp is completely optional. If these are unset, alerts are still
    # printed to the console/GitHub Actions log.
    whatsapp_access_token: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    whatsapp_phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    whatsapp_to: str = os.getenv("WHATSAPP_TO", "").strip()

    provider_runtime_seconds: int = _int_env("PROVIDER_RUNTIME_SECONDS", 180)
    correlation_window_minutes: int = _int_env("CORRELATION_WINDOW_MINUTES", 360)
    x_poll_seconds: int = _int_env("X_POLL_SECONDS", 30)
    live_mode: bool = os.getenv("LIVE_MODE", "false").lower() in {"1", "true", "yes"}
    state_db_path: str = os.getenv("STATE_DB_PATH", "data/runtime/agent.db").strip()
