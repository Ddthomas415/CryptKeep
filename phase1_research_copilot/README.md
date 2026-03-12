# Phase 1 Research Copilot (No Trading)

This is a production-style MVP for research assistance only.

## What this phase does
- Ingests live crypto market data from one exchange (REST + WebSocket path).
- Ingests news from a small set of sources (RSS + article fetch).
- Ingests archived context via Wayback lookups.
- Stores:
  - market/time-series data in PostgreSQL + TimescaleDB
  - normalized document metadata in PostgreSQL
  - raw HTML/text in MinIO object storage
  - document vectors in Qdrant
- Answers user questions through a web chat + REST API.
- Writes structured audit logs for actions.

## What this phase does not do
- No order creation
- No broker/exchange account actions
- No autonomous trade execution

`risk-stub` always returns `NO_TRADING`.

## Repo structure
```
phase1_research_copilot/
  Dockerfile.service
  docker-compose.yml
  .env.example
  requirements.txt
  contracts/
    service_contracts.md
  db/init/
    001_init.sql
  shared/
    config.py
    logging.py
    retry.py
    db.py
    audit.py
    models.py
  gateway/
  orchestrator/
  market_data/
  news_ingestion/
  archive_lookup/
  parser_normalizer/
  memory_retrieval/
  risk_stub/
  audit_log/
```

## Quick start
1. `cd /Users/baitus/Downloads/crypto-bot-pro/phase1_research_copilot`
2. `cp .env.example .env`
3. Set `OPENAI_API_KEY` in `.env` if you want live model reasoning.
4. `docker compose up --build`
5. Open web chat: `http://localhost:8001/`

## Smoke check
Once the stack is running, verify the gateway and orchestrator paths with:

```bash
python scripts/smoke_phase1_copilot.py --asset SOL --question "Why is SOL moving?"
```

The script checks:
- `GET /healthz` for gateway and orchestrator
- `POST /v1/explain`
- `POST /v1/chat`

## OpenAI reasoning mode
- `gateway` and `orchestrator` run in research-only mode whether OpenAI is configured or not.
- If `OPENAI_API_KEY` is set:
  - `/v1/explain` uses the OpenAI Responses API as the reasoning layer.
  - safe read-only tool calling is enabled for:
    - market snapshot
    - risk summary
    - operations summary
    - signal summary
- If OpenAI is unavailable:
  - `orchestrator` falls back to deterministic research-only reasoning
  - `gateway` falls back again if `orchestrator` itself is unavailable
- No trading or order placement is allowed in either mode.

## Health checks
- `http://localhost:8001/healthz` gateway
- `http://localhost:8002/healthz` orchestrator
- `http://localhost:8003/healthz` market-data
- `http://localhost:8004/healthz` news-ingestion
- `http://localhost:8005/healthz` archive-lookup
- `http://localhost:8006/healthz` parser-normalizer
- `http://localhost:8007/healthz` memory-retrieval
- `http://localhost:8008/healthz` risk-stub
- `http://localhost:8009/healthz` audit-log

## Sample API requests

### 1) Ask a question (gateway)
```bash
curl -s http://localhost:8001/v1/chat \
  -H 'content-type: application/json' \
  -d '{"asset":"SOL","question":"Why is SOL moving?","lookback_minutes":60}' | jq
```

Example response shape:
```json
{
  "ok": true,
  "asset": "SOL",
  "question": "Why is SOL moving?",
  "current_cause": "SOL moved up 1.84% in the lookback window...",
  "past_precedent": "Most relevant past precedent: ...",
  "relevant_past_precedent": "Most relevant past precedent: ...",
  "future_catalyst": "Closest forward catalyst: ...",
  "confidence": 0.71,
  "confidence_score": 0.71,
  "risk_note": "Research only. Execution disabled.",
  "execution_disabled": true,
  "evidence": [],
  "evidence_bundle": {
    "market": {},
    "market_snapshot": {},
    "recent_news": [],
    "past_context": [],
    "future_context": []
  },
  "risk_posture": {
    "execution_mode": "DISABLED",
    "gate": "NO_TRADING",
    "allow_trading": false
  },
  "execution": {
    "enabled": false,
    "reason": "Phase 1 research copilot only"
  },
  "assistant_status": {
    "provider": "openai",
    "model": "o4-mini",
    "fallback": false
  },
  "assistant_response": "SOL is rising on stronger spot demand. Risk note: research only.",
  "chat_status": {
    "provider": "openai",
    "model": "gpt-4.1-mini",
    "fallback": false
  }
}
```

### 2) Trigger one news poll
```bash
curl -s -X POST http://localhost:8004/v1/news/poll-now | jq
```

### 3) Ingest archive context
```bash
curl -s http://localhost:8005/v1/archive/lookup \
  -H 'content-type: application/json' \
  -d '{"url":"solana.com","asset":"SOL","max_snapshots":2,"ingest":true}' | jq
```

### 4) Retrieve combined context directly
```bash
curl -s http://localhost:8007/v1/memory/retrieve \
  -H 'content-type: application/json' \
  -d '{"asset":"BTC","question":"What changed in BTC in the last hour?","lookback_minutes":60,"limit":5}' | jq
```

### 5) Check audit events
```bash
curl -s 'http://localhost:8009/v1/audit/events/recent?limit=20' | jq
```

## Data model highlights
- `market_ticks` hypertable (TimescaleDB)
- `documents` metadata table
- `audit_events` log table

Normalization fields captured per document:
- `fetched_at` (timestamp)
- `asset_tags`
- `source`
- `timeline_tag` (`past|present|future`)
- `confidence`
- `content_hash`

## Retry behavior
- External fetches and service-to-service ingestion use exponential backoff retries.
- Failures are emitted to `audit-log` and structured stdout logs.

## Phase 2 backlog (paper trading)
1. Add deterministic signal generation with feature store-backed models.
2. Add paper broker service and simulated order lifecycle.
3. Add execution policy engine with hard limits and explainable blocks.
4. Add portfolio/risk attribution and replayable PnL accounting.
5. Add champion/challenger model evaluation before promotion.
6. Add human approval workflow for any execution intent.
7. Add exchange private API connectivity checks (still paper-only first).
8. Add incident runbooks and auto-generated postmortems.
9. Upgrade embeddings to model-based vectors (replace hash embedding stub).
10. Add authN/authZ and tenant-aware audit trails.
