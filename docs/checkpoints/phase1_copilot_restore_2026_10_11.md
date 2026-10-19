# Phase 1 copilot restore - step 1: source back on disk, offline-verified (2026-10-11)

ENGINEER: Claude (cloud session), per Damian's I01 decision "restore the full copilot". READY_FOR_INDEPENDENT_REVIEW.
No container, service, deployment, network call, API key use or git change.

## What was done
- Extracted all 40 files of phase1_research_copilot/ from ad18488df^ (the commit before its April 16 removal) into the
  existing gitignored sidecar folder with no-clobber copy. The operator's local phase1_research_copilot/.env was not
  overwritten or read (only key names and set/empty status checked: OPENAI_API_KEY is EMPTY; SERVICE_TOKEN and
  MINIO_SECRET_KEY are set).
- Replaced news_ingestion/main.py and memory_retrieval/main.py with the reviewed recovery versions from
  research/companion_recovery/ (date handling, re-poll on malformed dates, retry re-indexing of the persisted row;
  ACCEPTED_WITH_RISK 2026-10-01). Originals kept beside them as main.py.ad18488df_original.
- Separate venv outside the repo ($HOME/venv_p1, Python 3.12, sidecar requirements pinned last).

## Verification
- All sidecar modules byte-compile.
- Every root test that references the sidecar or companion recovery (previously skipped when the folder was empty):
  126 passed, 1 skipped (explicit opt-in disposable Postgres/Qdrant persistence test), 6.41 s.
These are unit/contract tests with mocked services; no real feed, database, vector store, object store or LLM ran.

## What it needs to actually run (from the sidecar's own docker-compose.yml/README)
TimescaleDB (Postgres 16, port 5432), Qdrant (6333), MinIO (9000/9001), and FastAPI services: market 8003, news 8004,
archive, parser 8006, memory 8007, risk stub 8008, audit 8009, orchestrator 8002, gateway/web chat 8001.
Without OPENAI_API_KEY the orchestrator answers with its deterministic fallback reasoning (labeled provider "fallback").
The dashboard reaches it through CK_PHASE1_ORCHESTRATOR_URL (default http://localhost:8002).
Known conflicts to resolve at deploy time: root docker/docker-compose.yml "backend" expects gateway on 9000, which
collides with MinIO's 9000 in the sidecar compose, and sets BACKEND_URL that the dashboard never reads.

## Next step (needs operator choice)
Where to run the stack (Mac Docker Desktop vs the Hetzner host), and whether to add an OpenAI key (recurring cost).
Then: start the stack, ingest one real feed item, ask one question from the dashboard, verify the cited answer (I02-I04).
