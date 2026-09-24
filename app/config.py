from dataclasses import dataclass
import os
from dotenv import load_dotenv
load_dotenv()

def _int(name, default): return int(os.getenv(name, default))
def _float(name, default): return float(os.getenv(name, default))

@dataclass(frozen=True)
class Config:
    stocktwits_username: str = os.getenv("STOCKTWITS_USERNAME", "")
    stocktwits_password: str = os.getenv("STOCKTWITS_PASSWORD", "")
    x_bearer_token: str = os.getenv("X_BEARER_TOKEN", "")
    massive_api_key: str = os.getenv("MASSIVE_API_KEY", "")
    tradestie_api_key: str = os.getenv("TRADESTIE_API_KEY", "")
    alert_webhook_url: str = os.getenv("ALERT_WEBHOOK_URL", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///flow_agent.db")
    correlation_window_minutes: int = _int("CORRELATION_WINDOW_MINUTES", 360)
    min_independent_confirmations: int = _int("MIN_INDEPENDENT_CONFIRMATIONS", 1)
    options_zscore_threshold: float = _float("OPTIONS_ZSCORE_THRESHOLD", 2.5)
    volume_zscore_threshold: float = _float("VOLUME_ZSCORE_THRESHOLD", 2.0)
    alert_cooldown_minutes: int = _int("ALERT_COOLDOWN_MINUTES", 30)
