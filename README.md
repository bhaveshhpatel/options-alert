# WallStJesus Flow Alert Agent

Research and real-time alerting application for studying social-media flow signals. It does not place trades or submit orders.

## Real-time alerting

The live service processes events as they arrive:

- **Stocktwits Firestream:** persistent Server-Sent Events connection with reconnect/backoff and Firestream `seq_id` cursor support.
- **X Recent Search:** optional polling adapter; it is not a true push stream.
- **Immediate signal alerts:** a detected signal is sent to the configured webhook immediately.
- **Cross-source alerts:** when another author/source corroborates a signal within the configured window, a second correlation alert is emitted.
- **Persistent local state:** SQLite stores processed events, signals, alerts, and provider cursors.
- **Graceful degradation:** each provider can be enabled independently.

Start locally:

    python -m app.live

Or:

    python -m app.runner --live

Docker:

    docker compose up -d --build

Required environment variables depend on the providers you enable:

    STOCKTWITS_USERNAME=
    STOCKTWITS_PASSWORD=
    X_BEARER_TOKEN=
    X_QUERY=("sweeper" OR "repeat buying" OR "repeat activity") -is:retweet
    X_POLL_SECONDS=30
    ALERT_WEBHOOK_URL=
    CORRELATION_WINDOW_MINUTES=360

Never commit credentials. Use environment variables, a secret manager, or GitHub Actions Secrets.

### Stocktwits availability

The code supports the documented, authorized Stocktwits Firestream interface. Stocktwits currently says it is reviewing its API program and is not accepting new API registrations; its current subscription page lists API access under Enterprise. Therefore the repository does **not** scrape Stocktwits or bypass authentication. If you already have authorized Firestream access, configure the credentials and the live service can consume the stream.

## GitHub Actions

The repository includes a **5-minute scheduled fallback monitor** so collection can begin immediately while a true always-on deployment is being arranged. GitHub scheduled workflows are not guaranteed to start exactly every five minutes and are not suitable for second-by-second streaming.

Each run:

1. Restores the latest `flow-agent-state` artifact.
2. Runs tests.
3. Monitors providers for up to 3 minutes.
4. Uploads the updated SQLite state.
5. Deletes superseded state artifacts.

The workflow uses GitHub Actions artifacts for interim persistence, so the SQLite database is **not committed to the repository**. Artifact retention is currently configured for 7 days. The workflow is serialized to avoid concurrent state updates.

For continuous real-time monitoring, run `app.live` as a long-lived container/service. The included Dockerfile and docker-compose.yml are the deployment starting point.

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

## Research controls

Historical results should be interpreted with timestamp accuracy, timezone normalization, source/account independence, repost/duplicate handling, look-ahead bias prevention, survivorship bias, catalyst/event controls, market/sector benchmarks, delisted symbols, ticker changes, and realistic entry/liquidity assumptions.

This repository is for research and alerting, not trade execution.


## Free always-on deployment

The recommended deployment target is an OCI Always Free Ampere A1 Linux VM. See `deploy/oci/README.md`. The repository includes a bootstrap script and a manual GitHub Actions deployment workflow at `.github/workflows/deploy-oci.yml`.
