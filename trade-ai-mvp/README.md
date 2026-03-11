# trade-ai-mvp

Phase 1 research copilot for crypto market intelligence. This project is explicitly **not** a live trading bot.

## Features in this scaffold
- TimescaleDB + Postgres storage for market and document records
- Redis + Qdrant wiring for cache/vector retrieval paths
- 10 FastAPI services with health endpoints
- Alembic migrations for core schema
- Structured JSON logging
- Seeded sample data so explanation flow works without external APIs
- One working user story: `POST /query/explain` for `"Why is SOL moving?"`

## Services
- `gateway` (public API)
- `orchestrator` (explanation workflow)
- `market_data` (snapshot endpoint + coinbase fetch/fallback)
- `news_ingestion` (ingest + list news)
- `archive_lookup` (historical context)
- `parser_normalizer` (hash/timeline/tag normalization)
- `memory` (hybrid retrieval)
- `risk_stub` (execution disabled)
- `audit_log` (structured audit sink)
- `execution_sim` (paper order simulation only)

## API quick test
```bash
curl -s http://localhost:8000/query/explain \
  -H 'content-type: application/json' \
  -d '{"asset":"SOL","question":"Why is SOL moving?"}' | jq
```

```bash
curl -s http://localhost:8000/query/propose-trade \
  -H 'content-type: application/json' \
  -d '{"asset":"SOL","question":"Should we open a SOL paper position now?","max_notional_usd":250}' | jq
```

```bash
curl -s "http://localhost:8000/live/status?symbol=SOL-USD" | jq
curl -s "http://localhost:8000/live/custody/status" | jq
curl -s "http://localhost:8000/live/custody/keys" | jq
curl -s -X POST "http://localhost:8000/live/custody/keys/verify" \
  -H 'content-type: application/json' \
  -d '{"operator":"ops-oncall","ticket_id":"SEC-2042","strict":true}' | jq
curl -s "http://localhost:8000/live/custody/rotation/plan" | jq
curl -s -X POST "http://localhost:8000/live/custody/rotation/run" \
  -H 'content-type: application/json' \
  -d '{"operator":"ops-oncall","note":"quarterly rotation window","ticket_id":"SEC-1234","force":true}' | jq
curl -s "http://localhost:8000/live/deployment/checklist?symbol=SOL-USD" | jq
curl -s "http://localhost:8000/live/deployment/state" | jq
curl -s http://localhost:8000/live/deployment/arm \
  -H 'content-type: application/json' \
  -d '{"operator":"ops-oncall","symbol":"SOL-USD","note":"dry-run arm","force":true}' | jq
curl -s "http://localhost:8000/live/router/policy" | jq
curl -s http://localhost:8000/live/router/plan \
  -H 'content-type: application/json' \
  -d '{"symbol":"SOL-USD","side":"buy","quantity":1.0,"order_type":"market"}' | jq
curl -s http://localhost:8000/live/router/simulate \
  -H 'content-type: application/json' \
  -d '{"symbol":"SOL-USD","side":"buy","quantity":1.0,"order_type":"market","max_slippage_bps":20}' | jq
curl -s http://localhost:8000/live/router/allocation \
  -H 'content-type: application/json' \
  -d '{"symbol":"SOL-USD","side":"buy","quantity":3.0,"order_type":"market","max_venues":2,"min_venues":1,"max_venue_ratio":0.7,"min_slice_quantity":0.25,"max_slippage_bps":25}' | jq
curl -s "http://localhost:8000/live/router/decisions?symbol=SOL-USD&source_endpoint=router_plan&limit=20" | jq
curl -s "http://localhost:8000/live/router/analytics?symbol=SOL-USD&source_endpoint=router_plan&window_hours=24&limit=2000" | jq
curl -s "http://localhost:8000/live/router/alerts?symbol=SOL-USD&source_endpoint=router_plan&window_hours=24&limit=2000" | jq
curl -s http://localhost:8000/live/router/maintenance/retention \
  -H 'content-type: application/json' \
  -d '{"days":30}' | jq
curl -s "http://localhost:8000/live/router/runbook?symbol=SOL-USD&source_endpoint=router_plan&window_hours=24&limit=2000" | jq
curl -s "http://localhost:8000/live/router/gate?symbol=SOL-USD&source_endpoint=router_plan&window_hours=24&limit=2000" | jq
curl -s "http://localhost:8000/live/router/gate?symbol=SOL-USD&source_endpoint=router_plan&window_hours=24&limit=2000&include_risk=true" | jq
curl -s "http://localhost:8000/live/router/gates?symbol=SOL-USD&source_endpoint=router_plan&source=incident&recommended_gate=HALT_NEW_POSITIONS&limit=20" | jq
curl -s "http://localhost:8000/live/router/gates/summary?symbol=SOL-USD&source_endpoint=router_plan&window_hours=168&limit=5000" | jq
curl -s http://localhost:8000/live/router/gates/maintenance/retention \
  -H 'content-type: application/json' \
  -d '{"days":180}' | jq
curl -s http://localhost:8000/live/router/incidents/open \
  -H 'content-type: application/json' \
  -d '{"operator":"ops-oncall","symbol":"SOL-USD","source_endpoint":"router_plan","window_hours":24,"limit":2000,"note":"dry-run incident open"}' | jq
curl -s "http://localhost:8000/live/router/incidents?status=open&symbol=SOL-USD&limit=20" | jq
curl -s "http://localhost:8000/live/router/incidents/<incident-id>" | jq
curl -s "http://localhost:8000/live/router/incidents/summary?symbol=SOL-USD&source_endpoint=router_plan&window_hours=168&limit=2000" | jq
curl -s http://localhost:8000/live/router/incidents/maintenance/retention \
  -H 'content-type: application/json' \
  -d '{"days":180}' | jq
curl -s -X POST "http://localhost:8000/live/router/incidents/<incident-id>/reopen" \
  -H 'content-type: application/json' \
  -d '{"operator":"ops-oncall","note":"reopened for verification"}' | jq
curl -s -X POST "http://localhost:8000/live/router/incidents/<incident-id>/ack" \
  -H 'content-type: application/json' \
  -d '{"operator":"ops-oncall","note":"acknowledged"}' | jq
curl -s -X POST "http://localhost:8000/live/router/incidents/<incident-id>/resolve" \
  -H 'content-type: application/json' \
  -d '{"operator":"ops-oncall","note":"resolved"}' | jq
curl -s "http://localhost:8000/live/custody/providers" | jq
curl -s "http://localhost:8000/live/custody/policy" | jq
curl -s http://localhost:8000/live/order-intent \
  -H 'content-type: application/json' \
  -d '{"symbol":"SOL-USD","side":"buy","quantity":1.0,"order_type":"market","client_order_id":"live-dryrun-001"}' | jq
curl -s "http://localhost:8000/live/order-intents?symbol=SOL-USD&status=blocked&limit=20" | jq
curl -s -X POST "http://localhost:8000/live/order-intents/<intent-id>/approve" | jq
curl -s "http://localhost:8000/live/execution/providers" | jq
curl -s "http://localhost:8000/live/execution/submissions?symbol=SOL-USD&limit=20" | jq
curl -s "http://localhost:8000/live/execution/submissions/summary?symbol=SOL-USD&window_hours=24&limit=2000" | jq
curl -s "http://localhost:8000/live/execution/place/analytics?symbol=SOL-USD&window_hours=168&limit=2000" | jq
curl -s "http://localhost:8000/live/execution/place/strategy-analytics?symbol=SOL-USD&provider=coinbase_sandbox&window_hours=168&limit=2000" | jq
curl -s "http://localhost:8000/live/execution/place/strategy-analytics?symbol=SOL-USD&provider=coinbase_sandbox&requested_strategy=auto&resolved_strategy=single_venue&window_hours=168&limit=2000" | jq
curl -s "http://localhost:8000/live/execution/place/strategy-analytics?symbol=SOL-USD&provider=coinbase_sandbox&has_shortfall=true&min_coverage_ratio=0.5&window_hours=168&limit=2000" | jq
curl -s -X POST "http://localhost:8000/live/execution/submissions/sync?symbol=SOL-USD&limit=20" | jq
curl -s -X POST "http://localhost:8000/live/execution/submissions/<submission-id>/sync" | jq
curl -s http://localhost:8000/live/execution/submissions/maintenance/retention \
  -H 'content-type: application/json' \
  -d '{"days":90}' | jq
curl -s "http://localhost:8000/live/execution/submissions/<submission-id>" | jq
curl -s "http://localhost:8000/live/execution/orders/<venue-order-id>/status?submission_id=<submission-id>" | jq
curl -s -X POST "http://localhost:8000/live/execution/orders/<venue-order-id>/cancel" \
  -H 'content-type: application/json' \
  -d '{"submission_id":"<submission-id>","provider":"mock","reason":"operator_cancel"}' | jq
curl -s -X POST "http://localhost:8000/live/execution/place/preflight" \
  -H 'content-type: application/json' \
  -d '{"intent_id":"<intent-id>","provider":"coinbase_sandbox","venue":"coinbase"}' | jq
curl -s -X POST "http://localhost:8000/live/execution/place/preview" \
  -H 'content-type: application/json' \
  -d '{"intent_id":"<intent-id>","provider":"coinbase_sandbox","venue":"coinbase","mode":"sandbox_submit"}' | jq
curl -s -X POST "http://localhost:8000/live/execution/place/route" \
  -H 'content-type: application/json' \
  -d '{"intent_id":"<intent-id>","provider":"coinbase_sandbox","strategy":"single_venue","max_venues":2,"min_venues":1,"max_venue_ratio":0.7,"min_slice_quantity":0.25,"max_slippage_bps":25}' | jq
curl -s -X POST "http://localhost:8000/live/execution/place/route/compare" \
  -H 'content-type: application/json' \
  -d '{"intent_id":"<intent-id>","provider":"coinbase_sandbox","strategies":["intent","single_venue","multi_venue"],"max_venues":2,"min_venues":1,"max_venue_ratio":0.7,"min_slice_quantity":0.25,"max_slippage_bps":25}' | jq
curl -s -X POST "http://localhost:8000/live/execution/place" \
  -H 'content-type: application/json' \
  -d '{"intent_id":"<intent-id>","provider":"coinbase_sandbox","strategy":"auto","max_venues":2,"min_venues":1,"max_venue_ratio":0.7,"min_slice_quantity":0.25,"max_slippage_bps":25}' | jq
curl -s -X POST http://localhost:8000/live/execution/submit \
  -H 'content-type: application/json' \
  -d '{"intent_id":"<intent-id>"}' | jq
curl -s -X POST http://localhost:8000/live/execution/submit \
  -H 'content-type: application/json' \
  -d '{"intent_id":"<intent-id>","mode":"sandbox_submit"}' | jq
curl -s -X POST http://localhost:8000/live/execution/submit \
  -H 'content-type: application/json' \
  -d '{"intent_id":"<intent-id>","mode":"live_place","provider":"coinbase_sandbox","strategy":"auto","max_venues":2,"min_venues":1,"max_venue_ratio":0.7,"min_slice_quantity":0.25,"max_slippage_bps":25}' | jq
curl -s http://localhost:8000/live/deployment/disarm \
  -H 'content-type: application/json' \
  -d '{"operator":"ops-oncall","symbol":"SOL-USD","note":"dry-run disarm"}' | jq
```

```bash
curl -s "http://localhost:8000/alerts/paper/risk" | jq
```

```bash
curl -s http://localhost:8000/market/BTC-USD/snapshot | jq
```

```bash
curl -s http://localhost:8000/documents/search \
  -H 'content-type: application/json' \
  -d '{"query":"SOL roadmap unlock validator growth","asset":"SOL","timeline":["past","present","future"],"limit":10}' | jq
```

```bash
# Requires PAPER_TRADING_ENABLED=true in .env
curl -s http://localhost:8000/paper/orders \
  -H 'content-type: application/json' \
  -d '{"symbol":"SOL-USD","side":"buy","order_type":"market","quantity":1.0,"signal_source":"regime_model_v1","rationale":"Momentum + headline confirmation","catalyst_tags":["roadmap","governance"]}' | jq
```

```bash
curl -s "http://localhost:8000/paper/orders?symbol=SOL-USD&status=filled&limit=20" | jq
```

```bash
curl -s "http://localhost:8000/paper/fills?symbol=SOL-USD&limit=50&sort=desc" | jq
curl -s "http://localhost:8000/paper/summary" | jq
curl -s "http://localhost:8000/paper/performance?limit=1000" | jq
curl -s "http://localhost:8000/paper/readiness" | jq
curl -s -X POST http://localhost:8000/paper/performance/rollups/refresh \
  -H 'content-type: application/json' \
  -d '{"interval":"hourly"}' | jq
curl -s "http://localhost:8000/paper/performance/rollups?interval=hourly&limit=48&sort=desc" | jq
curl -s -X POST http://localhost:8000/paper/replay/run \
  -H 'content-type: application/json' \
  -d '{"symbol":"SOL-USD","entry_bps":10.0,"hold_steps":1}' | jq
curl -s -X POST http://localhost:8000/paper/shadow/compare \
  -H 'content-type: application/json' \
  -d '{"symbol":"SOL-USD","champion_entry_bps":10.0,"challenger_entry_bps":5.0,"hold_steps":1}' | jq
curl -s -X POST http://localhost:8000/paper/maintenance/retention \
  -H 'content-type: application/json' \
  -d '{"days":30}' | jq
curl -s "http://localhost:8009/metrics" | head -n 30
```

```bash
# Requires PAPER_TRADING_ENABLED=true in .env
curl -s http://localhost:8000/paper/equity/snapshot \
  -H 'content-type: application/json' \
  -d '{"note":"manual"}' | jq
curl -s "http://localhost:8000/paper/equity?limit=50&sort=desc" | jq
```

Expected fields:
- `current_cause`
- `past_precedent`
- `future_catalyst`
- `confidence`
- `evidence`
- `execution_disabled: true`

## Run locally
1. Create env file:
```bash
cp .env.example .env
```
   If port `8000` is already in use, set `GATEWAY_PORT=8010` (or another free port) in `.env`.
2. Build and start:
```bash
docker compose up --build
```
3. Migrations + seed run automatically via the `migrator` service.  
   If you need to re-run manually:
```bash
docker compose run --rm migrator
```
4. Validate health:
```bash
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8001/health | jq
```
5. Run happy-path smoke test:
```bash
./scripts/smoke_explain.sh
```

## Dev shortcuts
```bash
make up
make migrate
make seed
make test
make smoke
make backup-paper
make restore-paper FILE=./backups/paper/paper_tables_YYYYMMDDTHHMMSSZ.sql
make down
```

## Paper backup/restore
- Backup script: `/Users/baitus/Downloads/crypto-bot-pro/trade-ai-mvp/scripts/paper_backup.sh`
- Restore script: `/Users/baitus/Downloads/crypto-bot-pro/trade-ai-mvp/scripts/paper_restore.sh`

Examples:
```bash
bash ./scripts/paper_backup.sh
bash ./scripts/paper_backup.sh ./backups/paper
bash ./scripts/paper_restore.sh ./backups/paper/paper_tables_20260311T020000Z.sql
```

## Notes
- Trading is hard-disabled via `EXECUTION_ENABLED=false` and `risk_stub` behavior.
- `/live/*` endpoints are dry-run planning/status surfaces only in this phase.
- `/live/router/plan` includes policy-aware multi-venue dry-run scoring from public Coinbase/Binance/Kraken market data when available.
- `/live/router/policy` and `/live/router/simulate` expose dry-run routing constraints and route feasibility (still no execution path).
- `/live/router/allocation` provides dry-run multi-venue split recommendations with slippage-capped venue filtering.
- `/live/router/decisions` returns persisted dry-run routing decisions for replay/inspection.
- `/live/router/analytics` provides aggregated dry-run routing metrics by venue/blocker over a time window.
- `/live/router/alerts` provides threshold-based dry-run routing health alerts from analytics windows.
- `/live/router/maintenance/retention` applies retention cleanup for persisted dry-run route decisions.
- `/live/router/runbook` converts alert signals into dry-run ops actions and suggested gate states.
- `/live/router/gate` emits a single dry-run recommended gate output (incident-first, then runbook fallback) for bot-side enforcement.
- `/live/router/gate` can optionally include risk overlay (`include_risk=true`) and emits the stricter gate when risk is binding.
- `/live/router/gates`, `/live/router/gates/summary`, and `/live/router/gates/maintenance/retention` provide persisted gate-signal history, aggregation, and retention.
- `/live/router/incidents/*` supports dry-run incident lifecycle (open/list/get/reopen/ack/resolve) for routing degradations.
- `/live/router/incidents/summary` and `/live/router/incidents/maintenance/retention` provide dry-run incident observability and lifecycle maintenance.
- `/live/custody/providers` and `/live/custody/policy` provide custody-source inventory and rotation-policy checks (scaffold only).
- `/live/custody/keys` and `/live/custody/keys/verify` provide metadata-only custody key inventory/verification contracts (no secret fetch, no key ops).
- `/live/custody/rotation/plan` and `/live/custody/rotation/run` provide custody key-rotation workflow contracts, with run intentionally blocked in Phase 2.
- `/live/deployment/*` endpoints provide dry-run arming governance only; no capital movement is possible.
- `/live/execution/providers` returns configured sandbox provider readiness (`mock`, `coinbase_sandbox`) and blockers.
- `/live/execution/submissions*` provides persistent live execution submit-attempt history (blocked and accepted sandbox attempts) for audit/replay.
- `/live/execution/place/analytics` aggregates live-place attempt outcomes and blocker frequencies for operator review.
- `/live/execution/place/strategy-analytics` aggregates requested/resolved strategy behavior, transition matrix diagnostics (`requested->resolved`), auto-resolution quality (including explicit `auto->intent` fallback count/rate), route feasibility, provider-venue compatibility, estimated-cost distributions, diversification diagnostics (`rejected_venues` reasons + ratio-cap incidence), and allocation constraint/capacity metrics (coverage ratios, shortfall incidence, blocker/failure rates) over persisted live-place attempts.
- `/live/execution/place/strategy-analytics` supports optional scoped filters: `requested_strategy`, `resolved_strategy`, `has_shortfall`, and `min_coverage_ratio`.
- `/live/execution/submissions/sync` bulk-refreshes persisted submission state for filtered batches.
- `/live/execution/submissions/{submission_id}/sync` refreshes persisted submission state from sandbox status checks.
- `/live/execution/submissions/maintenance/retention` applies retention cleanup to persisted execution submissions.
- `/live/execution/orders/{venue_order_id}/status` and `/cancel` provide sandbox order lifecycle checks and cancellation wiring.
- `/live/execution/place/preflight` evaluates per-intent live placement readiness checks and blockers (no execution path).
- `/live/execution/place/preview` returns provider-specific order payload preview plus blockers/can-submit signal (no execution path).
- `/live/execution/place/route` returns per-intent single/multi-venue route recommendations with deployment/risk/custody blockers, estimated route cost (`total_estimated_cost_bps`), allocation coverage diagnostics (`requested_quantity`, `allocated_quantity`, `allocation_coverage_ratio`, `allocation_shortfall_quantity`), and optional diversification constraints (`min_venues`, `max_venue_ratio`, `min_slice_quantity`) (no execution path).
- `/live/execution/place/route` surfaces allocation rejection blockers (for example min-slice/min-venues/ratio-unachievable) so operator tooling can distinguish diversification constraint failures from generic route infeasibility.
- `/live/execution/place/route/compare` compares route outcomes across strategies and returns a deterministic recommended strategy with cost-aware tie-breaking plus recommended allocation coverage/shortfall diagnostics and explicit ranking/tie-break metadata (`sort_rank`, `sort_key`, `recommended_tie_break_reason`) (no execution path).
- `/live/execution/place/route/compare` marks no-feasible allocation-capacity cases with explicit `recommended_reason` values (`no_feasible_route_capacity_shortfall_*`) and uses `no_feasible_route_constraint_failure_*` for other allocation-constraint failures.
- `/live/execution/place` is a Phase 3 live-placement contract stub that stays hard-blocked in Phase 2 while persisting audit attempts; it accepts routing strategy inputs (`intent`/`single_venue`/`multi_venue`/`auto`) for dry-run venue resolution.
- `/live/execution/submit` supports `mode=dry_run`, `mode=sandbox_submit`, and `mode=live_place` (delegates to placement stub; still blocked in Phase 2), including routing strategy passthrough in `live_place` mode.
- `strategy=auto` resolves through `/live/execution/place/route/compare` and returns `requested_strategy`/`resolved_strategy` plus resolution diagnostics (`strategy_resolution_reason`, `strategy_resolution_tie_break_reason`) in placement responses.
- Live placement routing now enforces provider/venue compatibility (for example `coinbase_sandbox` only allows `coinbase`) and surfaces mismatches via explicit blockers.
- Paper trading is separately feature-flagged with `PAPER_TRADING_ENABLED` (default `false`).
- Paper fill realism is configurable with `PAPER_MARKET_SLIPPAGE_BPS` and `PAPER_FEE_BPS`.
- Paper risk limits are configurable with `PAPER_MAX_NOTIONAL_USD`, `PAPER_MAX_POSITION_QTY`, and `PAPER_DAILY_LOSS_LIMIT_USD`.
- Optional gateway approval gate is configurable with `PAPER_ORDER_REQUIRE_APPROVAL`.
- Paper alert thresholds are configurable with `PAPER_ALERT_DRAWDOWN_PCT_THRESHOLD` and `PAPER_ALERT_CONCENTRATION_PCT_THRESHOLD`.
- Paper promotion readiness windows are configurable with `PAPER_MIN_PERFORMANCE_DAYS` and `PAPER_MIN_PERFORMANCE_POINTS`.
- Paper data retention is configurable with `PAPER_RETENTION_DAYS`.
- Sandbox submit behavior is configurable with `LIVE_EXECUTION_SANDBOX_ENABLED` and `LIVE_EXECUTION_PROVIDER` (`mock` or `coinbase_sandbox`).
- Optional sandbox HTTP transport is configurable with `LIVE_EXECUTION_SANDBOX_TRANSPORT_ENABLED` (default `false`).
- Coinbase sandbox HTTP transport additionally requires `COINBASE_API_PASSPHRASE`; when disabled, `coinbase_sandbox` uses stubbed submission envelopes.
- Custody source/policy scaffolding is configurable with `LIVE_CUSTODY_PROVIDER`, `LIVE_CUSTODY_KEY_ID`, `LIVE_CUSTODY_SECRET_ID`, `LIVE_CUSTODY_LAST_ROTATED_AT`, and `LIVE_CUSTODY_ROTATION_MAX_AGE_DAYS`.
- Dry-run live route policy is configurable with `LIVE_ROUTER_MAX_SPREAD_BPS`, `LIVE_ROUTER_MAX_ESTIMATED_COST_BPS`, and venue fee bps env vars.
- Dry-run live route alerts are configurable with `LIVE_ROUTER_ALERT_MIN_DECISIONS`, `LIVE_ROUTER_ALERT_MIN_ROUTE_ELIGIBLE_RATE`, `LIVE_ROUTER_ALERT_MIN_FEASIBLE_ROUTE_RATE`, `LIVE_ROUTER_ALERT_MAX_SPREAD_BLOCKER_RATIO`, and `LIVE_ROUTER_ALERT_MAX_COST_BLOCKER_RATIO`.
- Dry-run live route decision retention is configurable with `LIVE_ROUTER_RETENTION_DAYS`.
- Dry-run live router gate signal retention is configurable with `LIVE_ROUTER_GATE_RETENTION_DAYS`.
- Dry-run live router incident retention is configurable with `LIVE_ROUTER_INCIDENT_RETENTION_DAYS`.
- Dry-run live execution submission retention is configurable with `LIVE_EXECUTION_SUBMISSION_RETENTION_DAYS`.
- External API keys are optional. Missing keys do not crash services.
- Services use graceful fallback to seeded data when live fetches fail.
- Orchestrator degrades safely when downstream services are unavailable and still returns a valid explanation response.
- Grafana dashboard scaffold includes a Paper Trading section (positions, fills, risk state, readiness).

## Additional docs
- Service contracts: `docs/SERVICE_CONTRACTS.md`
- Phase 2 paper-trading backlog: `docs/PHASE2_PAPER_TRADING_BACKLOG.md`
