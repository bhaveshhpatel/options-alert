CREATE TABLE IF NOT EXISTS social_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, source_event_id TEXT,
 event_time TEXT NOT NULL, author TEXT, ticker TEXT, text TEXT NOT NULL, url TEXT,
 relationship_type TEXT, UNIQUE(source, source_event_id)
);
CREATE TABLE IF NOT EXISTS signal_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, social_event_id INTEGER, ticker TEXT NOT NULL,
 signal_type TEXT NOT NULL, confidence REAL NOT NULL, detected_at TEXT NOT NULL,
 FOREIGN KEY(social_event_id) REFERENCES social_events(id)
);
CREATE TABLE IF NOT EXISTS market_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT NOT NULL, event_time TEXT NOT NULL,
 close REAL, volume REAL, source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS forward_returns (
 id INTEGER PRIMARY KEY AUTOINCREMENT, signal_event_id INTEGER NOT NULL,
 horizon_trading_days INTEGER NOT NULL, return_pct REAL, benchmark_return_pct REAL,
 sector_return_pct REAL, max_favorable_excursion_pct REAL, max_adverse_excursion_pct REAL,
 FOREIGN KEY(signal_event_id) REFERENCES signal_events(id)
);
