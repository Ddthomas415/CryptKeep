## Governance Checklist — Implementation Status

The checklist is actively maintained to reflect completed work and the current system state.

Items are marked as:
- [x] **completed** — implemented and verified
- [ ] **pending** — requires human review, approval, or additional validation

This checklist reflects execution and verification status only. It does not represent final approval, deployment sign-off, or policy clearance.

# Maintenance Mode Status Update

## Implemented
- [x] Restored execution compatibility in `services/execution/exchange_client.py`
- [x] Restored Binance guard compatibility and then switched to canonical `services/security/binance_guard.py`
- [x] Restored `OrderDedupeStore` compatibility for execution paths
- [x] Fixed `services/fills/user_stream_ws.py` shutdown loop so websocket tests no longer hang
- [x] Added/kept `client_id_param(...)` support in `services/execution/exchange_client.py`
- [x] Updated `tools/repo_doctor.py` allowlist policy for intentional top-level repo structure
- [x] `repo_doctor --strict` now reports:
  - [x] Non-canonical top-level dirs: none
  - [x] Suspicious top-level files: none
- [x] Stopped stray local runner processes before baseline verification
- [x] Established clean baseline on branch `followup/compat-cleanup`
- [x] Committed and pushed preset review change:
  - [x] `services/strategies/presets.py`
  - [x] `ema_cross.min_cross_gap_pct: 0.03 -> 0.02`
  - [x] Commit: `2672605`

## Campaign Execution
- [x] Ran paper strategy evidence collector
- [x] Venue: `coinbase`
- [x] Symbol: `APR/USD`
- [x] Strategies:
  - [x] `breakout_donchian`
  - [x] `ema_cross`
- [x] Per-strategy runtime: `300s`
- [x] Tick interval: `1.0s`
- [x] Strategy min bars: `28`

## Campaign Results
- [x] Collector completed successfully
- [x] Completed strategies: `2/2`
- [x] `breakout_donchian` run completed
  - [x] stop_reason: `runtime_elapsed`
  - [x] runner_status: `stopped`
  - [x] enqueued_total: `0`
  - [x] fills_delta: `0`
  - [x] closed_trades_delta: `0`
- [x] `ema_cross` run completed
  - [x] stop_reason: `runtime_elapsed`
  - [x] runner_status: `stopped`
  - [x] enqueued_total: `2`
  - [x] fills_delta: `2`
  - [x] closed_trades_delta: `1`

## Evidence / Records
- [x] Strategy evidence latest file written
  - [x] `.cbp_state/data/strategy_evidence/strategy_evidence.latest.json`
- [x] Strategy evidence history file written
  - [x] `.cbp_state/data/strategy_evidence/strategy_evidence.20260321T044154Z.json`
- [x] Decision record written
  - [x] `docs/strategies/decision_record_2026-03-21.md`

## Maintenance Mode
- [x] Transitioned to maintenance mode
- [x] New campaign baseline verified
- [ ] Human strategy review complete for preset tuning commit `2672605`
- [ ] Pre-commit/backend/OpenAPI hook validation rerun in the correct backend-enabled environment
