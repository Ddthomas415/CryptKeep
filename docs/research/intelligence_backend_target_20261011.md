# Intelligence path: which backend the dashboard expects, and where it is (2026-10-11)

Claude (cloud session). Read-only follow-up to intelligence_path_refresh_20261011.md, which ended on "Next material fact:
whether a separate companion backend is already deployed and intended for this dashboard". No code/runtime change.

## SHOWN (git and file evidence, this checkout, HEAD 620bc8dbe)
1. The dashboard explain caller (dashboard/services/views/market_view.py get_research_explain) tries, in order:
   CK_API_BASE_URL (default http://localhost:8000) POST /api/v1/research/explain -> CK_PHASE1_ORCHESTRATOR_URL
   (default http://localhost:8002) POST /v1/explain -> a static mock that exists only for SOL.
2. Both servers it expects were REMOVED from git tracking in commit ad18488df (2026-04-16, "audit: P1+P2 fixes - orphan
   removal ..."; 313 files, -17,650 lines):
   - /api/v1/research/explain was served by crypto-trading-ai/backend/app/main.py (FastAPI; 252 tracked files at ad18488df^).
   - /v1/explain was served by phase1_research_copilot/orchestrator/main.py (40 non-test files at ad18488df^), which needs
     PostgreSQL+TimescaleDB, MinIO, Qdrant and an OpenAI API key (its own README).
   Both remain recoverable from history at ad18488df^. In the working tree phase1_research_copilot/ is gitignored and holds
   only empty gateway/orchestrator/shared/scripts folders plus a local .env (contents not read).
3. docker/docker-compose.yml still defines an opt-in "backend" service (profile phase1-companion) running
   gateway.main:app from that now-empty folder, so it cannot start from this checkout. Its dashboard service sets
   BACKEND_URL=http://backend:9000, but no dashboard/services/scripts code reads BACKEND_URL (the client reads
   CK_API_BASE_URL / CK_PHASE1_ORCHESTRATOR_URL) - a second disconnection even if the backend existed.
4. No systemd unit in packaging/systemd runs either backend, and no Hetzner checkpoint records one. Deployment anywhere is
   UNVERIFIED (no evidence found); the Hetzner host itself was not inspected.
5. docs/COMPANION_REPO_DEPENDENCY.md (2026-07-03) already decided: companion = archived sidecar, not a root dependency,
   with an open choice: vendor it back, document it as an external prerequisite, or remove stale references.

## Consequence
Unless an operator runs a backend outside this repo, every dashboard "explain" request today ends in the labeled static
fallback (SOL only). research/companion_recovery/ is a partial recovery of pieces (feed parsing, memory retrieval), not
a running service. This is the existing September 29 disconnection, now traced to the exact commit.

## I01 decision needed (operator)
A. Restore phase1 copilot from ad18488df^ as an external sidecar - most capability; new infrastructure and recurring
   cost (database, vector store, object store, LLM usage).
B. Smallest in-repo repair - a cited "explain" built only from data the repo already stores (OHLCV archive, CMC
   snapshots, crypto-edge archive), no LLM: facts with sources and as-of times, no causal claims.
C. Defer/retire - keep the companion archived, make the dashboard say "explanation backend not installed" instead of
   showing a demo, and remove the stale compose/BACKEND_URL references.
