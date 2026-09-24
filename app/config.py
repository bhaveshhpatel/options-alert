from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    stocktwits_username: str = os.getenv("STOCKTWITS_USERNAME", "")
    stocktwits_password: str = os.getenv("STOCKTWITS_PASSWORD", "")
    x_bearer_token: str = os.getenv("X_BEARER_TOKEN", "")
    x_query: str = os.getenv(
        "X_QUERY",
        '("sweeper" OR "repeat buying" OR "repeat activity") -is:retweet',
    )
    alert_webhook_url: str = os.getenv("ALERT_WEBHOOK_URL", "")
    whatsapp_access_token: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    whatsapp_phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    whatsapp_to: str = os.getenv("WHATSAPP_TO", "")
    provider_runtime_seconds: int = int(os.getenv("PROVIDER_RUNTIME_SECONDS", "180"))
    correlation_window_minutes: int = int(os.getenv("CORRELATION_WINDOW_MINUTES", "360"))
    x_poll_seconds: int = int(os.getenv("X_POLL_SECONDS", "30"))
    live_mode: bool = os.getenv("LIVE_MODE", "false").lower() in {"1", "true", "yes"}
    state_db_path: str = os.getenv("STATE_DB_PATH", "data/runtime/agent.db")
