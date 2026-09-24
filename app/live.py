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
from .providers.stocktwits import StocktwitsFirestream
from .providers.x_api import XRecentSearch

log = logging.getLogger("flow-agent.live")


class LiveAlertEngine:
    """Consumes events and emits immediate signal alerts plus correlation alerts."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.seen = set()
        self.recent = defaultdict(deque)
        self.lock = threading.Lock()
        self.sent_correlations = set()

    def on_event(self, event):
        key = f"{event.source}:{event.event_id}"
        with self.lock:
            if key in self.seen:
                return
            self.seen.add(key)
            if len(self.seen) > 100_000:
                self.seen = set(list(self.seen)[-50_000:])

        signal = detect(event)
        if not signal:
            return

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
        self._send(payload)

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
                self._send(format_alert(cluster), correlation=True)

    def _send(self, payload, correlation=False):
        if not self.cfg.alert_webhook_url:
            log.info("%s alert: %s", "correlation" if correlation else "signal", payload)
            return
        try:
            send_webhook(self.cfg.alert_webhook_url, payload)
        except Exception:
            log.exception("Webhook delivery failed")


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
    seq_id = os.getenv("STOCKTWITS_SEQ_ID", "") or None

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
                engine.on_event(event)
            backoff = 2
        except Exception:
            log.exception("Stocktwits stream disconnected; reconnecting.")
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)


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
