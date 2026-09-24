from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _int_env(name, default):
    value = os.getenv(name, "").strip()
    return int(value) if value else default


def _csv_env(name):
    return tuple(value.strip() for value in os.getenv(name, "").split(",") if value.strip())


@dataclass(frozen=True)
class Config:
    # Legacy Firestream credentials remain supported, but the REST API provider
    # is preferred when STOCKTWITS_API_KEY is configured.
    stocktwits_api_key: str = os.getenv("STOCKTWITS_API_KEY", "").strip()
    stocktwits_api_base_url: str = os.getenv(
        "STOCKTWITS_API_BASE_URL",
        "https://api.stocktwitsapi.com/v1",
    ).strip().rstrip("/")
    stocktwits_symbols: tuple[str, ...] = _csv_env("STOCKTWITS_SYMBOLS")
    stocktwits_username: str = os.getenv("STOCKTWITS_USERNAME", "").strip()
    stocktwits_password: str = os.getenv("STOCKTWITS_PASSWORD", "")
    stocktwits_api_poll_seconds: int = _int_env("STOCKTWITS_API_POLL_SECONDS", 300)
    stocktwits_api_lookback_minutes: int = _int_env("STOCKTWITS_API_LOOKBACK_MINUTES", 10)
    stocktwits_api_limit: int = _int_env("STOCKTWITS_API_LIMIT", 100)

    x_bearer_token: str = os.getenv("X_BEARER_TOKEN", "").strip()
    x_query: str = os.getenv(
        "X_QUERY",
        '(from:WallStJesus OR "WallStJesus" OR "sweeper" OR "repeat buying" OR "repeat activity") -is:retweet',
    ).strip()
    public_feed_urls: tuple[str, ...] = _csv_env("PUBLIC_FEED_URLS")
    public_feed_poll_seconds: int = _int_env("PUBLIC_FEED_POLL_SECONDS", 30)
    alert_webhook_url: str = os.getenv("ALERT_WEBHOOK_URL", "").strip()

    whatsapp_access_token: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    whatsapp_phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    whatsapp_to: str = os.getenv("WHATSAPP_TO", "").strip()

    provider_runtime_seconds: int = _int_env("PROVIDER_RUNTIME_SECONDS", 180)
    correlation_window_minutes: int = _int_env("CORRELATION_WINDOW_MINUTES", 360)
    x_poll_seconds: int = _int_env("X_POLL_SECONDS", 30)
    live_mode: bool = os.getenv("LIVE_MODE", "false").lower() in {"1", "true", "yes"}
    state_db_path: str = os.getenv("STATE_DB_PATH", "data/runtime/agent.db").strip()
