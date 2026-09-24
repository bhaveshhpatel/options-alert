import json, os
from datetime import datetime, timezone
import requests
from .config import Config
from .db_init import init_db
from .signals import classify

def relationship_type(source_a, source_b):
    return "SAME_SOURCE" if source_a == source_b else "UNKNOWN"

def should_alert(signal_count, independent_confirmations, cfg):
    return signal_count > 0 and independent_confirmations >= cfg.min_independent_confirmations

def emit_webhook(payload, cfg):
    if not cfg.alert_webhook_url: return
    r = requests.post(cfg.alert_webhook_url, json=payload, timeout=15)
    r.raise_for_status()

def run_once():
    cfg = Config()
    init_db()
    example = os.getenv("TEST_SIGNAL_TEXT", "")
    detected = classify(example) if example else None
    result = {"timestamp":datetime.now(timezone.utc).isoformat(),"detected":bool(detected),
              "ticker":detected.ticker if detected else None,
              "signal_type":detected.signal_type if detected else None}
    if detected and should_alert(1, 1, cfg):
        emit_webhook({"type":"research_signal", **result}, cfg)
    print(json.dumps(result))
    return result

if __name__ == "__main__": run_once()
