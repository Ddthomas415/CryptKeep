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
  - Response:
    - proxied orchestrator explanation payload
    - `assistant_response` (chat-friendly summary)
    - `chat_status.provider` (`openai|fallback`)
    - `chat_status.fallback` (boolean)
  - Failure behavior:
    - if `orchestrator` is unavailable, gateway returns a deterministic research-only fallback payload
    - `assistant_status.provider=gateway_fallback`
    - `execution.enabled=false`

## 2) orchestrator (`:8002`)
- `POST /v1/explain`
  - Request:
    ```json
    {"asset":"BTC","question":"What changed in BTC in the last hour?","lookback_minutes":60}
    ```
  - Response:
    - `current_cause`
    - `past_precedent`
    - `relevant_past_precedent`
    - `future_catalyst`
    - `confidence`
    - `confidence_score`
    - `risk_note`
    - `execution_disabled=true`
    - `evidence` list
    - `evidence_bundle`
    - `assistant_status.provider` (`openai|fallback`)
    - `execution.enabled=false`
  - Reasoning behavior:
    - if `OPENAI_API_KEY` is set, reasoning uses the OpenAI Responses API
    - safe read-only tool calling is available for:
      - `get_market_snapshot`
      - `get_risk_summary`
      - `get_operations_summary`
      - `get_signal_summary`
    - if OpenAI is unavailable, returns deterministic research-only fallback reasoning

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
