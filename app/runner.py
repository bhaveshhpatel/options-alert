import logging
import sys

from .config import Config
from .providers.stocktwits import StocktwitsFirestream
from .providers.x_api import XRecentSearch
from .providers.public_feed import PublicFeed
from .detector import detect
from .correlator import correlate
from .alerts import send_webhook, format_alert

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("flow-agent")


def collect(cfg):
    events = []
    if cfg.stocktwits_username and cfg.stocktwits_password:
        try:
            events += [
                e
                for e in StocktwitsFirestream(
                    cfg.stocktwits_username, cfg.stocktwits_password
                ).events(cfg.provider_runtime_seconds)
                if e
            ]
        except Exception:
            log.exception("Stocktwits stream failed")
    if cfg.x_bearer_token:
        try:
            events += XRecentSearch(cfg.x_bearer_token, cfg.x_query).events()
        except Exception:
            log.exception("X recent search failed")
    for url in cfg.public_feed_urls:
        try:
            events += PublicFeed(url).events()
        except Exception:
            log.exception("Public feed failed: %s", url)
    return events


def run_once():
    cfg = Config()
    events = collect(cfg)
    signals = [s for e in events if (s := detect(e))]
    clusters = correlate(signals, cfg.correlation_window_minutes)
    for c in clusters:
        send_webhook(cfg.alert_webhook_url, format_alert(c))
    log.info(
        "events=%s signals=%s clusters=%s",
        len(events),
        len(signals),
        len(clusters),
    )
    return clusters


if __name__ == "__main__":
    if "--live" in sys.argv or Config().live_mode:
        from .live import run_live

        run_live()
    else:
        run_once()
