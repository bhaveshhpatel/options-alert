import logging
import os
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from .alerts import format_alert, send_webhook
from .config import Config
from .correlator import correlate
from .detector import detect
from .providers.stocktwits import StocktwitsAuthError, StocktwitsFirestream
from .providers.x_api import XRecentSearch
from .providers.public_feed import PublicFeed
from .state import StateStore
from .whatsapp import send_whatsapp_text

log = logging.getLogger("flow-agent.live")


class LiveAlertEngine:
    """Consumes events and emits immediate signal alerts plus correlation alerts."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.store = StateStore(cfg.state_db_path)
        self.seen = set()
        self.recent = defaultdict(deque)
        self.lock = threading.Lock()
        self.sent_correlations = set()

    def on_event(self, event):
        key = f"{event.source}:{event.event_id}"
        with self.lock:
            if key in self.seen:
                return

            # If persistent state already has this event, keep the in-memory
            # dedupe set consistent before returning.
            if self.store.seen_event(key):
                self.seen.add(key)
                return

            self.seen.add(key)
            self.store.save_event(key, event)
            if len(self.seen) > 100_000:
                self.seen = set(list(self.seen)[-50_000:])

        signal = detect(event)
        if not signal:
            return

        self.store.save_signal(key, signal)

        # Alert immediately: this is independent of cross-source confirmation.
        payload = {
            "type": "flow_signal",
            "ticker": signal.ticker,
            "signal": signal.signal_type,
            "direction": signal.direction,
            "confidence": signal.confidence,
            "source": signal.social.source,
            "author": signal.social.author,
            "text": signal.social.text,
            "time": signal.social.created_at.isoformat(),
            "url": signal.social.url,
            "disclaimer": "Research alert only; not a trade instruction.",
        }
        self._send(payload, alert_key=f"signal:{key}")

        with self.lock:
            cutoff = signal.social.created_at - timedelta(
                minutes=self.cfg.correlation_window_minutes
            )
            q = self.recent[signal.ticker]
            while q and q[0].social.created_at < cutoff:
                q.popleft()
            prior = list(q)
            q.append(signal)

        if prior:
            clusters = correlate(prior + [signal], self.cfg.correlation_window_minutes)
            for cluster in clusters:
                if cluster["lead"].social.event_id != signal.social.event_id:
                    continue
                key = (
                    cluster["ticker"],
                    cluster["lead"].social.event_id,
                    tuple(sorted(m.social.event_id for m in cluster["matches"])),
                )
                with self.lock:
                    if key in self.sent_correlations:
                        continue
                    self.sent_correlations.add(key)
                self._send(format_alert(cluster), correlation=True, alert_key=f"correlation:{key}")

    def _send(self, payload, correlation=False, alert_key=None):
        if alert_key and not self.store.save_alert(
            alert_key,
            "correlation" if correlation else "signal",
            payload.get("ticker", ""),
            payload,
        ):
            return

        delivered = False

        # Always print alerts to stdout. This is the primary no-setup alert
        # channel and makes GitHub Actions logs useful even when every
        # external notification provider is disabled.
        log.warning(
            "🚨 FLOW ALERT | %s | %s",
            payload.get("ticker", "?"),
            _console_alert_summary(payload, correlation=correlation),
        )

        if self.cfg.alert_webhook_url:
            try:
                send_webhook(self.cfg.alert_webhook_url, payload)
                delivered = True
            except Exception:
                log.exception("Webhook delivery failed")

        if self.cfg.whatsapp_access_token and self.cfg.whatsapp_phone_number_id:
            recipients = [
                value.strip()
                for value in self.cfg.whatsapp_to.split(",")
                if value.strip()
            ]
            if not recipients:
                log.warning(
                    "WhatsApp credentials are configured but WHATSAPP_TO is empty; "
                    "WhatsApp delivery is disabled."
                )
            else:
                try:
                    send_whatsapp_text(
                        self.cfg.whatsapp_access_token,
                        self.cfg.whatsapp_phone_number_id,
                        recipients,
                        _whatsapp_message(payload, correlation=correlation),
                    )
                    delivered = True
                except Exception:
                    log.exception("WhatsApp delivery failed")

        if not delivered:
            log.info(
                "%s alert: %s",
                "correlation" if correlation else "signal",
                payload,
            )


def _console_alert_summary(payload, correlation=False):
    ticker = payload.get("ticker", "?")
    signal = payload.get("signal", "flow_cluster" if correlation else "signal")
    direction = payload.get("direction", "")
    confidence = payload.get("confidence")
    source = payload.get("source") or payload.get("lead_source", "")
    author = payload.get("author") or payload.get("lead_author", "")
    text = (payload.get("text") or payload.get("lead_text", "")).replace("\\n", " ")
    if len(text) > 240:
        text = text[:237] + "..."
    parts = [signal]
    if direction:
        parts.append(direction)
    if confidence is not None:
        parts.append(f"confidence={confidence}")
    if source or author:
        parts.append(f"{source}/{author}")
    if text:
        parts.append(text)
    return " | ".join(parts)


def _whatsapp_message(payload, correlation=False):
    """Render a compact WhatsApp-safe text alert."""
    ticker = payload.get("ticker", "?")
    signal = payload.get("signal", "flow_cluster" if correlation else "signal")
    direction = payload.get("direction", "")
    confidence = payload.get("confidence")
    source = payload.get("source") or payload.get("lead_source", "")
    author = payload.get("author") or payload.get("lead_author", "")
    text = payload.get("text") or payload.get("lead_text", "")
    url = payload.get("url", "")

    lines = [
        f"FLOW ALERT | {ticker}",
        f"Signal: {signal}",
        f"Direction: {direction}" if direction else None,
        f"Confidence: {confidence}" if confidence is not None else None,
        f"Source: {source} | Author: {author}" if source or author else None,
        f"Text: {text}" if text else None,
        f"URL: {url}" if url else None,
        "Research alert only; not a trade instruction.",
    ]
    return "\n".join(line for line in lines if line)


def run_live():
    cfg = Config()
    engine = LiveAlertEngine(cfg)
    threads = []

    if cfg.stocktwits_username and cfg.stocktwits_password:
        t = threading.Thread(
            target=_stocktwits_loop,
            args=(cfg, engine),
            name="stocktwits-stream",
            daemon=True,
        )
        threads.append(t)
        t.start()
    else:
        log.warning("Stocktwits Firestream is not configured; live Stocktwits alerts are disabled.")

    if cfg.x_bearer_token:
        t = threading.Thread(
            target=_x_poll_loop,
            args=(cfg, engine),
            name="x-poll",
            daemon=True,
        )
        threads.append(t)
        t.start()
    else:
        log.info("X provider is not configured; X polling is disabled.")

    for index, url in enumerate(cfg.public_feed_urls, start=1):
        t = threading.Thread(
            target=_public_feed_loop,
            args=(cfg, engine, url),
            name=f"public-feed-{index}",
            daemon=True,
        )
        threads.append(t)
        t.start()

    if not threads:
        raise SystemExit("No live providers configured.")

    log.info("Live alert service started with %d provider(s).", len(threads))
    try:
        while any(t.is_alive() for t in threads):
            time.sleep(2)
    except KeyboardInterrupt:
        log.info("Live alert service stopping.")


def _stocktwits_loop(cfg, engine):
    backoff = 2
    seq_id = engine.store.get_cursor("stocktwits") or os.getenv("STOCKTWITS_SEQ_ID", "") or None

    while True:
        try:
            stream = StocktwitsFirestream(
                cfg.stocktwits_username,
                cfg.stocktwits_password,
            )
            for event, next_seq in stream.events_with_cursor(
                seq_id=seq_id,
                keepalive=True,
            ):
                if next_seq:
                    seq_id = next_seq
                    engine.store.set_cursor("stocktwits", seq_id)
                engine.on_event(event)
            backoff = 2
        except StocktwitsAuthError as exc:
            log.error(
                "Stocktwits Firestream authentication failed: %s. "
                "The monitor will not retry invalid credentials.",
                exc,
            )
            return
        except Exception:
            log.exception("Stocktwits stream disconnected; reconnecting.")
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)


def _public_feed_loop(cfg, engine, url):
    interval = max(15, cfg.public_feed_poll_seconds)
    while True:
        try:
            for event in PublicFeed(url).events():
                engine.on_event(event)
        except Exception:
            log.exception("Public feed poll failed: %s", url)
        time.sleep(interval)


def _x_poll_loop(cfg, engine):
    interval = max(10, cfg.x_poll_seconds)
    while True:
        try:
            for event in XRecentSearch(cfg.x_bearer_token, cfg.x_query).events():
                engine.on_event(event)
        except Exception:
            log.exception("X recent-search poll failed.")
        time.sleep(interval)


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    run_live()
