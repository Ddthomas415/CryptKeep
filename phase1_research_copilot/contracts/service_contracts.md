# Phase 1 Service Contracts

All services expose `GET /healthz`.

## 1) gateway (`:8001`)
- `GET /`
  - Returns simple web chat UI.
- `POST /v1/chat`
  - Request:
    ```json
    {"asset":"SOL","question":"Why is SOL moving?","lookback_minutes":60}
    ```
  - Response: proxied orchestrator explanation payload.

## 2) orchestrator (`:8002`)
- `POST /v1/explain`
  - Request:
    ```json
    {"asset":"BTC","question":"What changed in BTC in the last hour?","lookback_minutes":60}
    ```
  - Response:
    - `current_cause`
    - `relevant_past_precedent`
    - `future_catalyst`
    - `confidence_score`
    - `evidence` bundle
    - `execution.enabled=false`

## 3) market-data (`:8003`)
- Background ingestion:
  - REST ticker polling (CCXT)
  - WebSocket ticker stream (Binance when enabled)
- `GET /v1/market/latest?symbol=SOL/USDT`

## 4) news-ingestion (`:8004`)
- Background ingestion from configured RSS feeds.
- `POST /v1/news/poll-now`
  - Runs one immediate poll cycle.

## 5) archive-lookup (`:8005`)
- `POST /v1/archive/lookup`
  - Request:
    ```json
    {"url":"solana.com","asset":"SOL","max_snapshots":3,"ingest":true}
    ```
  - Fetches Wayback snapshots, parses them, optionally ingests into memory.

## 6) parser-normalizer (`:8006`)
- `POST /v1/parse/url`
  - Fetches and normalizes URL content.
- `POST /v1/parse/html`
  - Normalizes provided HTML.
- Output normalized fields:
  - `timestamp` (fetched_at)
  - `asset_tags`
  - `source`
  - `timeline_tag` (`past|present|future`)
  - `confidence`
  - `content_hash`

## 7) memory-retrieval (`:8007`)
- `POST /v1/memory/documents`
  - Ingests normalized document into:
    - PostgreSQL metadata table
    - MinIO raw object store
    - Qdrant vector index
- `POST /v1/memory/retrieve`
  - Request:
    ```json
    {"asset":"SOL","question":"Why is SOL moving?","lookback_minutes":60,"limit":5}
    ```
  - Response combines:
    - market summary
    - recent news
    - past context
    - future catalysts
    - vector matches

## 8) risk-stub (`:8008`)
- `GET /v1/risk/status`
  - Always returns `NO_TRADING` posture.
- `POST /v1/risk/check-order`
  - Always blocks order execution.

## 9) audit-log (`:8009`)
- `POST /v1/audit/events`
  - Central structured event sink.
- `GET /v1/audit/events/recent?limit=50`
  - Returns recent audit entries.
