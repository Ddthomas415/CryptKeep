# Current Runtime Truth

**Last updated:** 2026-05-07

This document is the current operator-facing runtime truth for startup, stop, and status behavior.
Historical checkpoint records under `docs/checkpoints/` may preserve earlier launch paths and are not canonical unless reaffirmed here.

## Canonical operator control plane

- `python scripts/start_bot.py [--with_reconcile]`
- `python scripts/stop_bot.py [--all|--pipeline|--executor|--intent_consumer|--ops_signal_adapter|--ops_risk_gate|--reconciler]`
- `python scripts/bot_status.py`
- managed startup through supervisor / `service_ctl`

## Canonical runtime truth sources

- `services.runtime.process_supervisor.status(...)`
- `runtime/flags/*.status.json`
- `runtime/health/*.json`
- `runtime/flags/bot_runner.status.json`
- watchdog / crash-snapshot reads through `services/process/bot_runtime_truth.py`

## Canonical managed service set

- `market_ws` for the supervised WS freshness writer path
- `pipeline`
- `executor` for the paper execution path
- `intent_consumer` for the live submit-owner path
- `ops_signal_adapter`
- `ops_risk_gate`
- `reconciler` when enabled
- `ai_alert_monitor` for persisted copilot incident monitoring

## Current startup behavior shown in source

- `scripts/start_bot.py` starts supervised services; it is not a wrapper around `bot_ctl.py`.
- `scripts/run_intent_consumer_safe.py` and `scripts/run_live_reconciler_safe.py` gate managed `run` mode on `runtime_trading_config_available()` and enter IDLE / SAFE-IDLE on startup failure.
- `scripts/run_bot_runner.py` derives desired managed services from merged runtime config and writes `runtime/flags/bot_runner.status.json`.
- supervised symbol scope for `pipeline`, `executor`, `intent_consumer`, and `reconciler` is injected through `CBP_SYMBOLS`.
- `scripts/run_bot_runner.py` and `scripts/start_bot.py` derive that managed symbol set from `services/runtime/managed_symbol_selection.py`.
- when `managed_symbols.source=scanner`, paper mode uses scanner-ranked candidates with a refresh cache and preserves only fresh non-zero paper positions plus fresh actionable intents (`queued/submitting/submitted` by default).
- `runtime/flags/bot_runner.status.json` records `selected_symbols`, `protected_symbols`, and `protected_symbol_details` so operator status shows why a symbol stayed in the managed set.
- `services/process/bot_runtime_truth.py` no longer silently downgrades to legacy bot state unless `CBP_ALLOW_LEGACY_BOT_RUNTIME_FALLBACK=YES`.

## Compatibility-only legacy surfaces

- `scripts/bot_ctl.py`
- `scripts/run_bot_safe.py`
- `services.process.bot_process`
- `services.bot.start_manager.start(...)`
- `services.bot.start_manager.stop()`
- `services.bot.process_manager`
- `data/bot_process.json`
- `data/bot_heartbeat.json`

These remain for compatibility with older callers. They are not the canonical operator startup or runtime truth path.

## Startup reconciliation status

- `data/startup_status.json` is written by `services/execution/startup_status.py`.
- `services/execution/startup_reconcile.py` provides reconciliation helpers that can record success or failure.
- No current in-repo caller was shown enforcing startup-status freshness on the canonical supervised startup path.
- Treat `startup_status.json` as recorded reconciliation evidence, not as a current canonical launch gate, unless a caller is wired and documented.

## Historical note

- `docs/checkpoints/root_runtime_scope_record.md` and `docs/checkpoints/hidden_defaults_note.md` preserve earlier `scripts/bot_ctl.py -> scripts/run_bot_safe.py` assumptions for audit history.
- The current canonical operator path is the supervised `start_bot.py` / `stop_bot.py` / `bot_status.py` surface documented above.
