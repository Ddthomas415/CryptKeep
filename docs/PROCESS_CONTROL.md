# Process Control

`docs/CURRENT_RUNTIME_TRUTH.md` is the authoritative operator-facing runtime
truth for startup, stop, and status behavior. This file summarizes process
control surfaces and must stay aligned with that document.

Executable guard: `tests/test_process_control_runtime_truth_guard.py` pins the
canonical control plane, status surfaces, compatibility-only legacy surface,
and dashboard Process Control boundary documented here.

## Canonical control plane
- `python scripts/start_bot.py [--with_reconcile]`
- `python scripts/stop_bot.py [--all|--pipeline|--executor|--intent_consumer|--ops_signal_adapter|--ops_risk_gate|--reconciler]`
- `python scripts/bot_status.py`
- managed-service startup via supervisor / `service_ctl`

## Canonical status surfaces
- `runtime/flags/*.status.json`
- `runtime/health/*.json`
- process-supervisor service state for `pipeline`, `executor`, `intent_consumer`, `market_ws`, `ops_signal_adapter`, `ops_risk_gate`, and optional `reconciler`

## Compatibility-only legacy surface
- `python scripts/bot_ctl.py ...`
- `data/bot_process.json`
- `data/bot_heartbeat.json`
- `data/logs/bot.log`
- `scripts/run_bot_safe.py`

Use the legacy surface only for compatibility with older tooling. Do not use it for new operator automation or new startup orchestration.

## UI
Dashboard → Process Control uses the canonical supervised services and status surfaces above.
