# Phase 1 copilot on the Mac (Docker Desktop, no OpenAI key) - step 2 runbook (2026-10-11)

## Current correction: do not use the historical startup commands below yet

Codex found existing stopped companion containers and persistent volumes from six months ago. Their credentials have not been reconciled. The updated Compose requires POSTGRES_PASSWORD, SERVICE_TOKEN, MINIO_ACCESS_KEY and MINIO_SECRET_KEY, binds ports to loopback and makes repository mounts read-only. When POSTGRES_PASSWORD is set, application Settings derives the matching owned-database DSN; existing DATABASE_URL is overridden in that case. Changing environment values does not rotate credentials in an existing volume.

The controlled verification tool uses a separate random project, fresh disposable volumes and no existing .env. It is not an instruction to reuse the old database. The authenticated smoke script now reads SERVICE_TOKEN securely from its environment and refuses redirects; it no longer needs manual request replacement. Browser chat separately requires a distinct BROWSER_CHAT_TOKEN.

Before persistent startup: reconcile old-volume credentials without deleting data, complete the runtime evidence review, and explicitly choose whether the stack should remain running. Historical instructions below are retained as provenance, not current safe startup approval.

Operator decisions: host = Mac Docker Desktop; start WITHOUT an OpenAI key (orchestrator answers in labeled
"fallback" mode from retrieved data). Claude cannot run Docker from the laptop VM; Damian runs the commands below.

## Build fix applied before first run (sidecar folder only; originals kept as *.ad18488df_original)
The April compose built every service with the REPO ROOT as Docker context (~203 GB working tree, no .dockerignore),
which would stall or fail. Changed sidecar docker-compose.yml to context "." / dockerfile "Dockerfile.service", and
Dockerfile.service to COPY its own folder. Added phase1_research_copilot/.dockerignore excluding .env (secrets stay out of
images; services still receive them via env_file), the *_original files and caches. Compose file parses: 12 services.

## Ports that must be free on the Mac
5432 (TimescaleDB), 6333 (Qdrant), 9000/9001 (MinIO), 8001-8009 (gateway, orchestrator, market, news, archive,
parser, memory, risk stub, audit). Stop any local Postgres on 5432 first.

## Commands (Terminal on the Mac)
    cd ~/Downloads/crypto-bot-pro/phase1_research_copilot
    docker compose up -d --build          # first build takes several minutes
    docker compose ps                     # all 12 should be running/healthy
    curl -s http://localhost:8002/healthz
    TOKEN=$(grep '^SERVICE_TOKEN=' .env | cut -d= -f2-)
    curl -s -X POST http://localhost:8002/v1/explain \
      -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
      -d '{"asset":"BTC","question":"Why is BTC moving?","lookback_minutes":60}' | python3 -m json.tool > ~/Downloads/crypto-bot-pro/phase1_first_explain.json
(The bundled scripts/smoke_phase1_copilot.py sends no service token, so /v1/explain will refuse it; use the curl above.)
Dashboard: start it with  CK_PHASE1_SERVICE_TOKEN="$TOKEN"  in its environment; it already defaults to
http://localhost:8002 for the orchestrator. Stop the stack: docker compose down (data volumes are kept).

## What Claude verifies afterwards (I02-I04 evidence)
From phase1_first_explain.json and the stack logs: provider/fallback flag, market observation timestamp, retrieved
news items with source URLs and dates, as-of time, and that no order/trading action exists (risk stub NO_TRADING).
Then one dashboard query showing the same evidence. Failures are recorded, not hidden.
