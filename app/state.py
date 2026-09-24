import sqlite3
import threading
from datetime import datetime, timezone

class StateStore:
    """SQLite state store for events/signals/alerts; safe for a single service process."""
    def __init__(self, path="data/runtime/agent.db"):
        self.path=path
        import os; os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.lock=threading.Lock()
        self.conn=sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS events(
          event_key TEXT PRIMARY KEY, source TEXT, event_id TEXT, author TEXT,
          ticker TEXT, text TEXT, created_at TEXT, url TEXT, inserted_at TEXT);
        CREATE TABLE IF NOT EXISTS signals(
          event_key TEXT PRIMARY KEY, ticker TEXT, signal_type TEXT,
          confidence REAL, direction TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS alerts(
          alert_key TEXT PRIMARY KEY, alert_type TEXT, ticker TEXT,
          payload TEXT, sent_at TEXT);
        CREATE TABLE IF NOT EXISTS cursors(
          provider TEXT PRIMARY KEY, cursor TEXT, updated_at TEXT);
        """)
        self.conn.commit()

    def seen_event(self,key):
        with self.lock:
            return self.conn.execute("SELECT 1 FROM events WHERE event_key=?",(key,)).fetchone() is not None

    def save_event(self,key,e):
        with self.lock:
            self.conn.execute("INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?,?,?,?)",
              (key,e.source,e.event_id,e.author,self._ticker(e.text),e.text,e.created_at.isoformat(),e.url,datetime.now(timezone.utc).isoformat()))
            self.conn.commit()

    def save_signal(self,key,s):
        with self.lock:
            self.conn.execute("INSERT OR REPLACE INTO signals VALUES(?,?,?,?,?,?)",
              (key,s.ticker,s.signal_type,s.confidence,s.direction,s.social.created_at.isoformat()))
            self.conn.commit()

    def save_alert(self,key,alert_type,ticker,payload):
        import json
        with self.lock:
            cur=self.conn.execute("INSERT OR IGNORE INTO alerts VALUES(?,?,?,?,?)",
              (key,alert_type,ticker,json.dumps(payload,default=str),datetime.now(timezone.utc).isoformat()))
            self.conn.commit()
            return cur.rowcount == 1

    def get_cursor(self,provider):
        row=self.conn.execute("SELECT cursor FROM cursors WHERE provider=?",(provider,)).fetchone()
        return row[0] if row else None

    def set_cursor(self,provider,cursor):
        with self.lock:
            self.conn.execute("INSERT OR REPLACE INTO cursors VALUES(?,?,?)",
              (provider,str(cursor),datetime.now(timezone.utc).isoformat()))
            self.conn.commit()

    @staticmethod
    def _ticker(text):
        import re
        m=re.search(r"\$([A-Z][A-Z0-9]{0,5})\b",str(text).upper())
        return m.group(1) if m else ""
