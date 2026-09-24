import time
from datetime import datetime, timedelta, timezone

import requests

from ..models import SocialEvent


class StocktwitsApiAuthError(RuntimeError):
    """Raised when the Stocktwits REST API rejects the configured API key."""


class StocktwitsApi:
    """Poll the documented Stocktwits REST API for messages by symbol.

    The REST API is symbol-scoped, so it is intentionally a polling provider,
    not a replacement for Firestream's global SSE feed. Set symbols explicitly
    (for example, symbols discovered by another provider) to keep API usage
    predictable on the free tier.
    """

    def __init__(
        self,
        api_key,
        symbols,
        username="",
        base_url="https://api.stocktwitsapi.com/v1",
        lookback_minutes=10,
        limit=100,
        session=None,
    ):
        self.api_key = api_key.strip()
        self.symbols = tuple(dict.fromkeys(s.upper().lstrip("$") for s in symbols if s.strip()))
        self.username = username.strip()
        self.base_url = base_url.rstrip("/")
        self.lookback_minutes = max(1, int(lookback_minutes))
        self.limit = max(1, min(int(limit), 1000))
        self.session = session or requests.Session()

    def events(self):
        if not self.api_key or not self.symbols:
            return

        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=self.lookback_minutes)

        for symbol in self.symbols:
            params = {
                "symbol": symbol,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "limit": self.limit,
                "order": "asc",
                "primaryOnly": "false",
            }
            if self.username:
                params["username"] = self.username

            response = self.session.get(
                f"{self.base_url}/messages",
                params=params,
                headers={
                    "x-api-key": self.api_key,
                    "Accept": "application/json",
                },
                timeout=20,
            )
            if response.status_code == 401:
                raise StocktwitsApiAuthError(
                    "Stocktwits REST API returned HTTP 401 Unauthorized. "
                    "Check STOCKTWITS_API_KEY."
                )
            if response.status_code == 403:
                raise RuntimeError(
                    "Stocktwits REST API returned HTTP 403 Forbidden. "
                    "The API key/plan may not permit this request or lookback window."
                )
            if response.status_code == 429:
                raise RuntimeError(
                    "Stocktwits REST API returned HTTP 429 Too Many Requests. "
                    "Reduce polling frequency or number of symbols."
                )
            response.raise_for_status()

            payload = response.json()
            for message in payload.get("messages", []):
                event = self._parse_message(message)
                if event:
                    yield event

    @staticmethod
    def _parse_message(message):
        text = message.get("body") or message.get("text") or ""
        if not text:
            return None

        ts = message.get("created_at")
        try:
            created = (
                datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                if ts
                else datetime.now(timezone.utc)
            )
        except Exception:
            created = datetime.now(timezone.utc)

        symbols = message.get("symbols") or []
        ticker = symbols[0] if symbols else ""
        url = message.get("url")
        stocktwits_id = message.get("stocktwits_id") or message.get("id")
        event_id = str(stocktwits_id)

        return SocialEvent(
            "stocktwits_api",
            event_id,
            message.get("username") or message.get("name") or "unknown",
            text,
            created,
            url,
        )
