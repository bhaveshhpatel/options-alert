from dataclasses import dataclass
import os
from dotenv import load_dotenv
load_dotenv()

@dataclass(frozen=True)
class Config:
    stocktwits_username: str = os.getenv("STOCKTWITS_USERNAME", "")
    stocktwits_password: str = os.getenv("STOCKTWITS_PASSWORD", "")
    x_bearer_token: str = os.getenv("X_BEARER_TOKEN", "")
    x_query: str = os.getenv("X_QUERY", '("sweeper" OR "repeat buying" OR "repeat activity") -is:retweet')
    alert_webhook_url: str = os.getenv("ALERT_WEBHOOK_URL", "")
    provider_runtime_seconds: int = int(os.getenv("PROVIDER_RUNTIME_SECONDS", "180"))
    correlation_window_minutes: int = int(os.getenv("CORRELATION_WINDOW_MINUTES", "360"))
