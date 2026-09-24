import json
from datetime import datetime, timezone
import requests
from requests.auth import HTTPBasicAuth
from ..models import SocialEvent


class StocktwitsAuthError(RuntimeError):
    """Raised when Firestream rejects the configured credentials."""


class StocktwitsFirestream:
    def __init__(self, username, password, url="https://firestream.stocktwits.com/stream"):
        self.username, self.password, self.url = username, password, url

    def events(self, seconds=180):
        started = datetime.now(timezone.utc)
        for event, _seq_id in self.events_with_cursor():
            if (datetime.now(timezone.utc) - started).total_seconds() > seconds:
                break
            yield event

    def events_with_cursor(self, seq_id=None, keepalive=True, read_timeout=75):
        """Yield (SocialEvent, seq_id) from the authorized Firestream SSE feed.

        Firestream documents seq_id recovery for roughly 24 hours, so callers can
        persist/reuse the latest cursor when a long-lived connection reconnects.
        """
        params = {"seq_id": seq_id} if seq_id else {}
        headers = {
            "Accept": "text/event-stream",
            "Accept-Encoding": "gzip",
            "Cache-Control": "no-cache",
        }
        with requests.get(
            self.url,
            params=params,
            auth=HTTPBasicAuth(self.username, self.password),
            headers=headers,
            stream=True,
            timeout=(15, read_timeout),
        ) as response:
            if response.status_code == 401:
                raise StocktwitsAuthError(
                    "Stocktwits Firestream returned HTTP 401 Unauthorized. "
                    "The configured credentials are not authorized for Firestream. "
                    "Verify the login and that the Stocktwits account has Firestream access."
                )
            response.raise_for_status()
            data_lines = []
            current_seq = seq_id
            for raw_line in response.iter_lines(decode_unicode=True):
                if raw_line is None:
                    continue
                line = raw_line.strip()
                if not line:
                    if data_lines:
                        payload = "\n".join(data_lines)
                        data_lines = []
                        event, current_seq = self._parse(payload, current_seq)
                        if event:
                            yield event, current_seq
                    elif not keepalive:
                        continue
                    continue
                if line.startswith("data:"):
                    data_lines.append(line[5:].strip())
                elif line.startswith("id:"):
                    current_seq = line[3:].strip() or current_seq

            if data_lines:
                event, current_seq = self._parse("\n".join(data_lines), current_seq)
                if event:
                    yield event, current_seq

    def _parse(self, payload, fallback_seq=None):
        try:
            obj = json.loads(payload)
        except Exception:
            return None, fallback_seq

        # Firestream wraps messages in {object, action, data, time, seq_id}.
        if isinstance(obj.get("data"), dict):
            data = obj["data"]
        else:
            data = obj

        text = data.get("body") or data.get("text") or data.get("message") or ""
        if not text:
            return None, obj.get("seq_id") or fallback_seq

        user = data.get("user") or {}
        author = user.get("username") or user.get("name") or "unknown"
        event_id = str(data.get("id") or obj.get("seq_id") or hash(payload))
        ts = data.get("created_at") or obj.get("time") or data.get("timestamp")
        try:
            created = (
                datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                if ts
                else datetime.now(timezone.utc)
            )
        except Exception:
            created = datetime.now(timezone.utc)

        url = data.get("url")
        next_seq = obj.get("seq_id") or fallback_seq
        return SocialEvent("stocktwits", event_id, author, text, created, url), next_seq
