# WallStJesus Flow Alert Agent

Research and real-time alerting application for studying social-media flow signals. It does not place trades or submit orders.

## Real-time alerting

The live service processes events as they arrive:

- **Stocktwits Firestream:** persistent Server-Sent Events connection with reconnect/backoff and Firestream `seq_id` cursor support.
- **X Recent Search:** optional polling adapter; it is not a true push stream.
- **Immediate signal alerts:** a detected signal is sent to the configured webhook and/or WhatsApp immediately.
- **Cross-source alerts:** when another author/source corroborates a signal within the configured window, a second correlation alert is emitted.
- **Optional WhatsApp delivery:** alerts can be sent through the Meta WhatsApp Cloud API without changing the existing webhook path.
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
    WHATSAPP_ACCESS_TOKEN=
    WHATSAPP_PHONE_NUMBER_ID=
    WHATSAPP_TO=15551234567
    WHATSAPP_GRAPH_API_VERSION=v23.0
    WHATSAPP_API_URL=
    CORRELATION_WINDOW_MINUTES=360

Never commit credentials. Use environment variables, a secret manager, or GitHub Actions Secrets.


### Optional WhatsApp alerts

WhatsApp delivery is independent of `ALERT_WEBHOOK_URL`. You can use either channel or both.

Configure these environment variables/secrets:

- `WHATSAPP_ACCESS_TOKEN` — Meta WhatsApp Cloud API access token.
- `WHATSAPP_PHONE_NUMBER_ID` — the WhatsApp Business phone-number ID used by the Cloud API.
- `WHATSAPP_TO` — destination phone number(s) in international format, comma-separated for multiple recipients.
- `WHATSAPP_GRAPH_API_VERSION` — optional Graph API version; defaults to `v23.0`.
- `WHATSAPP_API_URL` — optional full API endpoint override; normally leave blank.

The application sends a text message containing the ticker, signal, direction/confidence when available, source/author, source text, URL, and the research-only disclaimer. It truncates the message to WhatsApp's text-message size limit.

For GitHub Actions, add `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, and `WHATSAPP_TO` as repository secrets. `WHATSAPP_GRAPH_API_VERSION` can be a repository variable if you need to override the default. The WhatsApp credentials are optional; leaving them unset keeps the existing webhook behavior unchanged.

Meta's WhatsApp Business Platform also has messaging-policy/template requirements that can affect when a business can initiate free-form messages. The code deliberately does not attempt to bypass those rules.

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


## Deplexo always-on deployment

Deplexo can connect directly to this GitHub repository and automatically redeploy on pushes. The repository now includes `deplexo.yaml` and a Deplexo-specific entrypoint.

The Deplexo container:

- runs the same `app.live` real-time alert engine;
- exposes a lightweight `/health` endpoint on Deplexo's `PORT`;
- keeps the existing Stocktwits/X provider reconnect behavior;
- uses the existing environment variables and SQLite state path;
- does not require a GitHub Personal Access Token for the GitHub-to-Deplexo connection.

Deploy from Deplexo:

1. Sign in to Deplexo and connect GitHub via OAuth.
2. Select `bhaveshhpatel/options-alert`.
3. Deploy the repository using the committed `deplexo.yaml`.
4. Add the runtime environment variables/secrets in Deplexo's dashboard:
   - `STOCKTWITS_USERNAME`
   - `STOCKTWITS_PASSWORD`
   - `X_BEARER_TOKEN` (optional)
   - `X_QUERY` (optional)
   - `ALERT_WEBHOOK_URL` (optional)
   - `WHATSAPP_ACCESS_TOKEN` (optional)
   - `WHATSAPP_PHONE_NUMBER_ID` (optional)
   - `WHATSAPP_TO` (optional)
   - `WHATSAPP_GRAPH_API_VERSION` (optional)
   - `WHATSAPP_API_URL` (optional)
   - `CORRELATION_WINDOW_MINUTES` (optional)
   - `STATE_DB_PATH=data/runtime/agent.db` (optional; this is already the application default)
5. Confirm the Deplexo logs show `Live alert service started` and the health endpoint responds.

**Persistence note:** the alert engine's SQLite database is written to `data/runtime/agent.db`. The Deplexo deployment configuration does not assume a persistent-volume feature that is not documented by Deplexo. Therefore, treat SQLite persistence on Deplexo as container-local unless the Deplexo dashboard explicitly provides persistent storage for the deployed app. The GitHub Actions 5-minute fallback remains enabled and continues to use its own artifact-backed state.

The existing `.github/workflows/monitor.yml` remains the fallback monitor and now passes the optional WhatsApp configuration through to the live service.
