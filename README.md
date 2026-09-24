# WallStJesus Flow Alert Agent

Research and alerting application for studying social-media flow signals. It does not place trades.

## Live providers

- Stocktwits Firestream: optional
- X Recent Search: optional
- Signal detector for repeat activity / sweeper-style language
- Cross-source correlation with configurable ecosystem grouping
- Webhook alerts
- GitHub Actions scheduled monitor

If X credentials are missing, the X adapter is skipped. The runner can therefore operate with Stocktwits only. If both providers are missing, it exits cleanly after logging that no live providers are configured.

Never commit credentials. Use environment variables or GitHub Actions Secrets.

## Historical research / backtest

The historical engine is offline and does not require API credentials.

Social-event CSV columns:
event_id,source,author,ticker,text,created_at,url

OHLC CSV columns:
ticker,date,open,high,low,close

Run:

    python -m app.research --events data/historical_events.example.csv --prices data/historical_prices.example.csv

Outputs:

- research_output/signal_results.csv
- research_output/cross_source_signals.csv
- research_output/summary.json

The engine evaluates +1, +3, +5, and +7 trading-day forward returns, plus maximum favorable excursion (MFE) and maximum adverse excursion (MAE). It uses trading rows rather than calendar-day offsets.

Example files are included under data/.

## Important research controls

Historical results should be interpreted with timestamp accuracy, timezone normalization, source/account independence, repost/duplicate handling, look-ahead bias prevention, survivorship bias, catalyst/event controls, market/sector benchmarks, delisted symbols, ticker changes, and realistic entry/liquidity assumptions.

This repository is for research and alerting, not trade execution.
